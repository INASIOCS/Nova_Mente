"""Provedor NVIDIA — não consome requisição de verdade e não lê o .env.

Todas as respostas HTTP são simuladas. As configurações são construídas com
`_env_file=None`, de modo que a suíte dá o mesmo resultado em qualquer máquina,
tenha ou não um `.env` local apontando para um provedor ou outro.
"""

from __future__ import annotations

import json

import pytest

from app.agents import llm
from app.core.config import Settings
from app.rag import embeddings

CHAVE_FALSA = "nvapi-chave-de-teste-que-nao-existe"


def _cfg(**extra) -> Settings:
    base = dict(
        llm_provider="nvidia",
        nvidia_api_key=CHAVE_FALSA,
        google_api_key="",
    )
    base.update(extra)
    return Settings(_env_file=None, **base)


class RespostaFalsa:
    """O mínimo de `requests.Response` que o código usa."""

    def __init__(self, status=200, corpo=None, texto="", cabecalhos=None):
        self.status_code = status
        self._corpo = corpo
        self.text = texto or (json.dumps(corpo) if corpo is not None else "")
        self.headers = cabecalhos or {}

    def json(self):
        if self._corpo is None:
            raise ValueError("sem corpo")
        return self._corpo


def _chat(conteudo: str, finish: str = "stop") -> dict:
    return {
        "choices": [{"message": {"content": conteudo}, "finish_reason": finish}],
        "usage": {"completion_tokens": 10},
    }


class Chamadas(list):
    """Lista das chamadas feitas a `requests.post`, com a fila de respostas."""

    def __init__(self) -> None:
        super().__init__()
        self.fila: list[RespostaFalsa] = []


@pytest.fixture
def chamadas(monkeypatch):
    """Substitui `requests.post`; devolve as chamadas feitas e a fila de respostas."""
    registro = Chamadas()

    def falso(url, headers=None, json=None, timeout=None):
        registro.append({"url": url, "headers": headers, "json": json})
        return registro.fila.pop(0)

    monkeypatch.setattr("requests.post", falso)
    return registro


def _cliente(monkeypatch, **extra) -> llm.ClienteNvidia:
    monkeypatch.setattr(llm, "get_settings", lambda: _cfg(**extra))
    return llm.ClienteNvidia()


# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------


def test_o_padrao_continua_sendo_o_gemini():
    cfg = Settings(_env_file=None)
    assert cfg.provedor_llm == "gemini"
    assert cfg.nome_provedor_llm == "Gemini"
    assert cfg.modelo_llm_ativo == cfg.gemini_model


def test_provedor_nvidia_usa_o_modelo_da_nvidia():
    cfg = _cfg()
    assert cfg.provedor_llm == "nvidia"
    assert cfg.modelo_llm_ativo == "nvidia/nemotron-3.5-lightning-30b-a3b"
    assert cfg.llm_configurado is True


def test_sem_chave_o_provedor_escolhido_nao_esta_configurado():
    # ter a chave do OUTRO provedor não conta
    cfg = Settings(_env_file=None, llm_provider="nvidia", google_api_key="x")
    assert cfg.llm_configurado is False


def test_embeddings_seguem_o_provedor_de_geracao_salvo_pedido_em_contrario():
    assert _cfg().provedor_embeddings == "nvidia"
    assert _cfg(embedding_provider="gemini").provedor_embeddings == "gemini"


def test_a_fabrica_devolve_o_cliente_do_provedor_escolhido(monkeypatch):
    monkeypatch.setattr(llm, "get_settings", lambda: _cfg())
    monkeypatch.setattr(llm, "_cliente", None)
    assert isinstance(llm.get_cliente_llm(), llm.ClienteNvidia)

    monkeypatch.setattr(llm, "get_settings", lambda: _cfg(llm_provider="gemini"))
    monkeypatch.setattr(llm, "_cliente", None)
    assert isinstance(llm.get_cliente_llm(), llm.ClienteGemini)


# ---------------------------------------------------------------------------
# Geração
# ---------------------------------------------------------------------------


def test_gera_json_e_envia_o_que_deve(monkeypatch, chamadas):
    chamadas.fila.append(RespostaFalsa(corpo=_chat('{"titulo": "VCN"}')))
    cliente = _cliente(monkeypatch)

    assert cliente.gerar_json("sistema", "usuario") == {"titulo": "VCN"}

    envio = chamadas[0]
    assert envio["url"] == "https://integrate.api.nvidia.com/v1/chat/completions"
    assert envio["headers"]["Authorization"] == f"Bearer {CHAVE_FALSA}"
    corpo = envio["json"]
    assert corpo["model"] == "nvidia/nemotron-3.5-lightning-30b-a3b"
    assert corpo["stream"] is False
    assert corpo["max_tokens"] == 16384  # não reduzir: ver HANDOFF
    assert corpo["response_format"] == {"type": "json_object"}
    assert corpo["messages"][0] == {"role": "system", "content": "sistema"}


def test_o_raciocinio_vem_desligado_e_pode_ser_ligado(monkeypatch, chamadas):
    chamadas.fila.append(RespostaFalsa(corpo=_chat("{}")))
    _cliente(monkeypatch).gerar_json("s", "u")
    assert chamadas[0]["json"]["chat_template_kwargs"] == {"enable_thinking": False}

    chamadas.fila.append(RespostaFalsa(corpo=_chat("{}")))
    _cliente(monkeypatch, nvidia_thinking=True).gerar_json("s", "u")
    assert chamadas[1]["json"]["chat_template_kwargs"] == {"enable_thinking": True}


def test_desembrulha_json_em_cerca_de_markdown(monkeypatch, chamadas):
    chamadas.fila.append(RespostaFalsa(corpo=_chat('```json\n{"a": 1}\n```')))
    assert _cliente(monkeypatch).gerar_json("s", "u") == {"a": 1}


def test_429_vira_erro_de_quota_e_nao_e_repetido(monkeypatch, chamadas):
    chamadas.fila.append(RespostaFalsa(429, texto="rate limit", cabecalhos={"Retry-After": "37"}))
    cliente = _cliente(monkeypatch)

    with pytest.raises(llm.ErroQuota) as info:
        cliente.gerar_json("s", "u")

    assert info.value.segundos == 37
    assert info.value.provedor == "NVIDIA"
    assert info.value.cota_esgotada is True
    # Uma tentativa só: repetir um 429 gasta o limite por minuto à toa.
    assert len(chamadas) == 1


def test_429_sem_cabecalho_de_espera(monkeypatch, chamadas):
    chamadas.fila.append(RespostaFalsa(429, texto="rate limit"))
    with pytest.raises(llm.ErroQuota) as info:
        _cliente(monkeypatch).gerar_json("s", "u")
    assert info.value.segundos is None


def test_chave_recusada_nao_vaza_a_chave_na_mensagem(monkeypatch, chamadas):
    chamadas.fila.append(RespostaFalsa(401, texto="unauthorized"))
    with pytest.raises(llm.ErroLLM) as info:
        _cliente(monkeypatch).gerar_json("s", "u")
    mensagem = str(info.value)
    assert "NVIDIA_API_KEY" in mensagem
    assert CHAVE_FALSA not in mensagem
    assert not isinstance(info.value, llm.ErroQuota)


def test_sem_response_format_tenta_de_novo_sem_ele(monkeypatch, chamadas):
    chamadas.fila.append(RespostaFalsa(400, texto="unsupported response_format"))
    chamadas.fila.append(RespostaFalsa(corpo=_chat('{"ok": true}')))

    assert _cliente(monkeypatch).gerar_json("s", "u") == {"ok": True}
    assert len(chamadas) == 2
    assert "response_format" in chamadas[0]["json"]
    assert "response_format" not in chamadas[1]["json"]


def test_falha_transitoria_do_servidor_vale_uma_segunda_tentativa(monkeypatch, chamadas):
    chamadas.fila.append(RespostaFalsa(503, texto="unavailable"))
    chamadas.fila.append(RespostaFalsa(corpo=_chat('{"ok": true}')))
    assert _cliente(monkeypatch).gerar_json("s", "u") == {"ok": True}
    assert len(chamadas) == 2


def test_resposta_vazia_por_falta_de_tokens_orienta_a_desligar_o_raciocinio(
    monkeypatch, chamadas
):
    chamadas.fila.append(RespostaFalsa(corpo=_chat("", finish="length")))
    with pytest.raises(llm.ErroLLM) as info:
        _cliente(monkeypatch).gerar_json("s", "u")
    assert "NVIDIA_THINKING" in str(info.value)


def test_sem_chave_o_erro_diz_o_que_fazer(monkeypatch):
    cliente = _cliente(monkeypatch, nvidia_api_key="")
    assert cliente.disponivel is False
    with pytest.raises(llm.ErroLLM) as info:
        cliente.gerar_json("s", "u")
    assert "NVIDIA_API_KEY" in str(info.value)


# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------


def _resposta_de_embeddings(n: int, dim: int = 4, invertida: bool = False) -> RespostaFalsa:
    itens = [{"index": i, "embedding": [float(i)] * dim} for i in range(n)]
    if invertida:
        itens.reverse()
    return RespostaFalsa(corpo={"data": itens})


def _servico(monkeypatch, **extra) -> embeddings.ServicoEmbeddings:
    monkeypatch.setattr(embeddings, "get_settings", lambda: _cfg(**extra))
    return embeddings.ServicoEmbeddings()


def test_indexa_em_lotes_com_input_type_passage(monkeypatch, chamadas):
    for lote in (16, 16, 8):
        chamadas.fila.append(_resposta_de_embeddings(lote))
    servico = _servico(monkeypatch)
    assert servico.backend == "nvidia:nvidia/nemotron-3.5-embed-1b"

    vetores = servico.embed_documentos([f"trecho {i}" for i in range(40)])

    assert len(vetores) == 40
    assert len(chamadas) == 3  # 40 trechos em 3 requisições, não em 40
    assert all(c["json"]["input_type"] == "passage" for c in chamadas)
    assert chamadas[0]["url"].endswith("/embeddings")


def test_a_consulta_usa_input_type_query(monkeypatch, chamadas):
    chamadas.fila.append(_resposta_de_embeddings(1))
    _servico(monkeypatch).embed_consulta("o que é uma VCN?")
    assert chamadas[0]["json"]["input_type"] == "query"


def test_a_ordem_dos_vetores_segue_o_campo_index(monkeypatch, chamadas):
    chamadas.fila.append(_resposta_de_embeddings(3, invertida=True))
    vetores = _servico(monkeypatch).embed_documentos(["a", "b", "c"])
    assert [v[0] for v in vetores] == [0.0, 1.0, 2.0]


def test_falha_da_api_degrada_para_o_lexico_sem_derrubar(monkeypatch, chamadas):
    chamadas.fila.append(RespostaFalsa(500, texto="erro"))
    servico = _servico(monkeypatch)

    vetores = servico.embed_documentos(["uma vcn é uma rede privada"])

    assert len(vetores) == 1
    assert len(vetores[0]) == embeddings.DIMENSAO_FALLBACK
    assert servico.backend == "lexico-fallback (degradado da API NVIDIA)"
    assert servico.usando_api is False


def test_provedor_nvidia_sem_chave_nao_cai_escondido_no_gemini(monkeypatch):
    # Com a chave do Gemini presente, ainda assim não pode usá-la em silêncio.
    servico = _servico(monkeypatch, nvidia_api_key="", google_api_key="chave-do-gemini")
    assert servico.backend == "lexico-fallback"
    assert servico.usando_gemini is False
