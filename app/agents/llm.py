"""Clientes de LLM com saída JSON garantida.

O provedor é escolhido por `LLM_PROVIDER` (`gemini`, o padrão, ou `nvidia`) e
`get_cliente_llm()` devolve o cliente certo. Os dois expõem a mesma interface —
`gerar_json`, `gerar_texto`, `caminho`, `disponivel` — e por isso o grafo de
agentes não sabe, e não precisa saber, quem está do outro lado.

Gemini — primário: LangChain (`ChatGoogleGenerativeAI`), alinhado ao edital.
Fallback: SDK `google-generativeai` direto, caso o wrapper LangChain falhe.

NVIDIA — HTTP direto contra a API compatível com OpenAI de build.nvidia.com,
com `requests`, que já é dependência do projeto. Não adiciona SDK novo ao deploy.
"""

from __future__ import annotations

import json
import logging
import re

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class ErroLLM(Exception):
    """Falha na chamada ao modelo de linguagem."""


class ErroQuota(ErroLLM):
    """Cota da API esgotada (HTTP 429 / RESOURCE_EXHAUSTED).

    Separada de ErroLLM porque o tratamento é outro: não adianta tentar de
    novo, nem cair para outro caminho de chamada — toda tentativa, inclusive a
    que falha, consome o saldo. Quem captura decide quando voltar a partir de
    `segundos`, que vem do próprio `retry_delay` (Gemini) ou do cabeçalho
    `Retry-After` (NVIDIA) da resposta.
    """

    # Marca reconhecível sem importar esta classe. A interface roda como script
    # do Streamlit, onde o nome "app" é disputado pelo próprio arquivo; quanto
    # menos ela precisar importar do pacote no topo, menos frágil ela fica.
    cota_esgotada = True

    def __init__(
        self,
        mensagem: str,
        segundos: int | None = None,
        provedor: str = "Gemini",
    ) -> None:
        super().__init__(mensagem)
        self.segundos = segundos
        # Também lido pela interface via getattr, pelo mesmo motivo acima.
        self.provedor = provedor


# Marcas de uma resposta de cota esgotada, em qualquer um dos caminhos de
# chamada (LangChain embrulha a exceção do SDK, que embrulha o erro HTTP).
_MARCAS_DE_QUOTA = (
    "429",
    "resource_exhausted",
    "resourceexhausted",
    "exceeded your current quota",
    "quota_metric",
    "quota exceeded",
)

# O Gemini devolve o tempo de espera em dois formatos conhecidos.
_ESPERA_PROTOBUF = re.compile(r"retry_delay\s*\{\s*seconds:\s*(\d+)", re.IGNORECASE)
_ESPERA_TEXTO = re.compile(r"retry in\s+([\d.]+)\s*s", re.IGNORECASE)


def _erro_de_quota(exc: Exception) -> ErroQuota | None:
    """Reconhece um 429 de cota e extrai o tempo de espera, se houver."""
    texto = str(exc)
    if not any(marca in texto.lower() for marca in _MARCAS_DE_QUOTA):
        return None

    segundos: int | None = None
    for padrao in (_ESPERA_PROTOBUF, _ESPERA_TEXTO):
        achado = padrao.search(texto)
        if achado:
            try:
                segundos = int(float(achado.group(1)))
            except ValueError:
                segundos = None
            break

    return ErroQuota("Cota da API do Gemini esgotada.", segundos)


def _texto_da_resposta(resposta: object) -> str:
    """Extrai o texto de uma resposta do LangChain.

    No LangChain 1.x, `AIMessage.content` pode ser uma string OU uma lista de
    blocos de conteúdo (`[{"type": "text", "text": "..."}]`). Aplicar `str()`
    sobre a lista devolve o repr do Python, não o texto — origem silenciosa de
    "JSON inválido". Aqui tratamos os dois formatos.
    """
    # LangChain expõe `.text` como atalho já normalizado
    texto_pronto = getattr(resposta, "text", None)
    if isinstance(texto_pronto, str) and texto_pronto.strip():
        return texto_pronto
    if callable(texto_pronto):
        try:
            valor = texto_pronto()
            if isinstance(valor, str) and valor.strip():
                return valor
        except Exception:
            pass

    conteudo = getattr(resposta, "content", resposta)

    if isinstance(conteudo, str):
        return conteudo

    if isinstance(conteudo, (list, tuple)):
        partes: list[str] = []
        for bloco in conteudo:
            if isinstance(bloco, str):
                partes.append(bloco)
            elif isinstance(bloco, dict):
                if bloco.get("type") in (None, "text") and isinstance(
                    bloco.get("text"), str
                ):
                    partes.append(bloco["text"])
        if partes:
            return "\n".join(partes)

    return str(conteudo)


def _extrair_json(texto: str) -> dict:
    """Extrai o primeiro objeto JSON válido de uma resposta de LLM."""
    texto = texto.strip()

    # remove cercas de código markdown
    if texto.startswith("```"):
        texto = re.sub(r"^```(?:json)?\s*", "", texto)
        texto = re.sub(r"\s*```$", "", texto)

    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        pass

    # último recurso: maior bloco entre a primeira { e a última }
    inicio, fim = texto.find("{"), texto.rfind("}")
    if inicio != -1 and fim > inicio:
        try:
            return json.loads(texto[inicio : fim + 1])
        except json.JSONDecodeError as exc:
            raise ErroLLM(
                "O modelo não devolveu JSON válido. Tente novamente ou reduza o documento."
            ) from exc

    raise ErroLLM("O modelo não devolveu nenhum JSON reconhecível.")


class ClienteGemini:
    """Encapsula a chamada ao Gemini e informa qual caminho está ativo."""

    def __init__(self, temperatura: float = 0.3) -> None:
        self._cfg = get_settings()
        self.temperatura = temperatura
        self.caminho = "indisponivel"
        self._chat = None
        self._genai_model = None

        if not self._cfg.gemini_configurado:
            return

        # 1) LangChain
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI

            # response_mime_type força o modo JSON nativo do Gemini.
            # max_output_tokens é generoso porque os modelos atuais consomem
            # boa parte do orçamento em tokens de raciocínio antes da resposta.
            self._chat = ChatGoogleGenerativeAI(
                model=self._cfg.gemini_model,
                google_api_key=self._cfg.google_api_key,
                temperature=temperatura,
                max_output_tokens=16384,
                response_mime_type="application/json",
                timeout=180,
            )
            self.caminho = f"langchain:{self._cfg.gemini_model}"
            return
        except Exception as exc:
            logger.warning("ChatGoogleGenerativeAI indisponível: %s", exc)

        # 2) SDK direto
        try:
            import google.generativeai as genai

            genai.configure(api_key=self._cfg.google_api_key)
            self._genai_model = genai.GenerativeModel(self._cfg.gemini_model)
            self.caminho = f"google-generativeai:{self._cfg.gemini_model}"
        except Exception as exc:
            logger.warning("SDK google-generativeai indisponível: %s", exc)

    @property
    def disponivel(self) -> bool:
        return self._chat is not None or self._genai_model is not None

    def gerar_texto(self, prompt_sistema: str, prompt_usuario: str) -> str:
        if not self.disponivel:
            raise ErroLLM(
                "Gemini não configurado. Defina GOOGLE_API_KEY no arquivo .env "
                "(obtenha a chave em https://aistudio.google.com/apikey)."
            )

        if self._chat is not None:
            try:
                resposta = self._chat.invoke(
                    [
                        ("system", prompt_sistema),
                        ("human", prompt_usuario),
                    ]
                )
                return _texto_da_resposta(resposta)
            except Exception as exc:
                quota = _erro_de_quota(exc)
                if quota is not None:
                    # Não tentar o SDK direto: a segunda chamada falharia pelo
                    # mesmo motivo e consumiria mais saldo diário.
                    raise quota from exc
                logger.warning("Falha via LangChain, tentando SDK direto: %s", exc)
                try:
                    import google.generativeai as genai

                    genai.configure(api_key=self._cfg.google_api_key)
                    self._genai_model = genai.GenerativeModel(self._cfg.gemini_model)
                    self._chat = None
                    self.caminho = f"google-generativeai:{self._cfg.gemini_model}"
                except Exception as exc2:
                    raise ErroLLM(f"Falha ao chamar o Gemini: {exc}") from exc2

        try:
            resposta = self._genai_model.generate_content(  # type: ignore[union-attr]
                f"{prompt_sistema}\n\n---\n\n{prompt_usuario}",
                generation_config={
                    "temperature": self.temperatura,
                    "max_output_tokens": 16384,
                    "response_mime_type": "application/json",
                },
                request_options={"timeout": 180},
            )
            return resposta.text or ""
        except Exception as exc:
            quota = _erro_de_quota(exc)
            if quota is not None:
                raise quota from exc
            raise ErroLLM(f"Falha ao chamar o Gemini: {exc}") from exc

    def gerar_json(self, prompt_sistema: str, prompt_usuario: str) -> dict:
        bruto = self.gerar_texto(prompt_sistema, prompt_usuario)
        return _extrair_json(bruto)


class ClienteNvidia:
    """Cliente da API compatível com OpenAI de build.nvidia.com.

    Mesma interface do `ClienteGemini`. Duas decisões deliberadas:

    - Uma chamada, sem cair para "outro caminho" em caso de falha. Num 429 isso
      só gastaria mais requisições do limite por minuto à toa.
    - O raciocínio do modelo é opcional (`NVIDIA_THINKING`). Desligado, a mesma
      pergunta leva cerca de um terço do tempo e dos tokens.
    """

    # Falhas transitórias do servidor, que valem uma segunda tentativa. O 429 não
    # entra aqui de propósito.
    _TRANSITORIOS = (502, 503, 504)

    def __init__(self, temperatura: float = 0.3) -> None:
        self._cfg = get_settings()
        self.temperatura = temperatura
        self.caminho = (
            f"nvidia:{self._cfg.nvidia_model}"
            if self._cfg.nvidia_configurado
            else "indisponivel"
        )

    @property
    def disponivel(self) -> bool:
        return self._cfg.nvidia_configurado

    def _cabecalhos(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._cfg.nvidia_api_key.strip()}",
            "Accept": "application/json",
        }

    def _corpo(
        self, prompt_sistema: str, prompt_usuario: str, com_modo_json: bool
    ) -> dict:
        corpo: dict = {
            "model": self._cfg.nvidia_model,
            "messages": [
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario},
            ],
            "temperature": self.temperatura,
            # Generoso pelo mesmo motivo do Gemini: com o raciocínio ligado, boa
            # parte do orçamento vai para o pensamento antes da resposta.
            "max_tokens": 16384,
            "stream": False,
            "chat_template_kwargs": {"enable_thinking": self._cfg.nvidia_thinking},
        }
        if com_modo_json:
            corpo["response_format"] = {"type": "json_object"}
        return corpo

    def _enviar(self, corpo: dict):
        import requests

        url = f"{self._cfg.nvidia_base_url.rstrip('/')}/chat/completions"
        try:
            return requests.post(
                url,
                headers=self._cabecalhos(),
                json=corpo,
                timeout=self._cfg.nvidia_timeout,
            )
        except requests.Timeout as exc:
            raise ErroLLM(
                f"A NVIDIA não respondeu em {self._cfg.nvidia_timeout}s "
                f"({self._cfg.nvidia_model}). O modelo pode estar sobrecarregado."
            ) from exc
        except requests.RequestException as exc:
            raise ErroLLM(f"Falha de rede ao chamar a NVIDIA: {exc}") from exc

    @staticmethod
    def _espera(resposta) -> int | None:
        """Segundos de espera sugeridos pelo cabeçalho `Retry-After`, se houver."""
        bruto = resposta.headers.get("Retry-After")
        try:
            return int(float(bruto)) if bruto else None
        except ValueError:
            return None

    def gerar_texto(self, prompt_sistema: str, prompt_usuario: str) -> str:
        if not self.disponivel:
            raise ErroLLM(
                "NVIDIA não configurada. Defina NVIDIA_API_KEY no arquivo .env "
                "(chave gratuita em https://build.nvidia.com)."
            )

        resposta = self._enviar(self._corpo(prompt_sistema, prompt_usuario, True))

        # Nem todo modelo aceita `response_format`: sem ele, o `_extrair_json`
        # abaixo já desembrulha cercas de markdown e acha o objeto.
        if resposta.status_code in (400, 422) and "response_format" in resposta.text:
            resposta = self._enviar(self._corpo(prompt_sistema, prompt_usuario, False))

        if resposta.status_code in self._TRANSITORIOS:
            logger.warning("NVIDIA devolveu %s; uma nova tentativa.", resposta.status_code)
            resposta = self._enviar(self._corpo(prompt_sistema, prompt_usuario, True))

        if resposta.status_code == 429:
            raise ErroQuota(
                "Limite de requisições da NVIDIA atingido.",
                self._espera(resposta),
                provedor="NVIDIA",
            )
        if resposta.status_code in (401, 403):
            raise ErroLLM(
                f"A NVIDIA recusou a chave (HTTP {resposta.status_code}). "
                "Confira NVIDIA_API_KEY no .env."
            )
        if resposta.status_code != 200:
            raise ErroLLM(
                f"Falha ao chamar a NVIDIA: HTTP {resposta.status_code} — "
                f"{resposta.text[:200]}"
            )

        try:
            escolha = resposta.json()["choices"][0]
            texto = escolha["message"].get("content") or ""
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise ErroLLM("A NVIDIA devolveu uma resposta fora do formato esperado.") from exc

        if not texto.strip():
            motivo = escolha.get("finish_reason")
            raise ErroLLM(
                "A NVIDIA devolveu a resposta vazia"
                + (
                    " — o orçamento de tokens acabou antes do fim do raciocínio. "
                    "Desligue NVIDIA_THINKING."
                    if motivo == "length"
                    else "."
                )
            )
        return texto

    def gerar_json(self, prompt_sistema: str, prompt_usuario: str) -> dict:
        return _extrair_json(self.gerar_texto(prompt_sistema, prompt_usuario))


_cliente: ClienteGemini | ClienteNvidia | None = None


def get_cliente_llm() -> ClienteGemini | ClienteNvidia:
    """Cliente do provedor escolhido em `LLM_PROVIDER`, criado uma única vez."""
    global _cliente
    if _cliente is None:
        if get_settings().provedor_llm == "nvidia":
            _cliente = ClienteNvidia()
        else:
            _cliente = ClienteGemini()
    return _cliente
