"""Cliente de LLM (Google Gemini) com saída JSON garantida.

Primário: LangChain (`ChatGoogleGenerativeAI`) — alinhado ao edital.
Fallback: SDK `google-generativeai` direto, caso o wrapper LangChain falhe.
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
    """Cota da API do Gemini esgotada (HTTP 429 / RESOURCE_EXHAUSTED).

    Separada de ErroLLM porque o tratamento é outro: não adianta tentar de
    novo, nem cair para outro caminho de chamada — toda tentativa, inclusive a
    que falha, consome o saldo diário. Quem captura decide quando voltar a
    partir de `segundos`, que vem do próprio `retry_delay` da resposta.
    """

    # Marca reconhecível sem importar esta classe. A interface roda como script
    # do Streamlit, onde o nome "app" é disputado pelo próprio arquivo; quanto
    # menos ela precisar importar do pacote no topo, menos frágil ela fica.
    cota_esgotada = True

    def __init__(self, mensagem: str, segundos: int | None = None) -> None:
        super().__init__(mensagem)
        self.segundos = segundos


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


_cliente: ClienteGemini | None = None


def get_cliente_llm() -> ClienteGemini:
    global _cliente
    if _cliente is None:
        _cliente = ClienteGemini()
    return _cliente
