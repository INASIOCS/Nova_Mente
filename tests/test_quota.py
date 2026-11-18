"""Reconhecimento do 429 de cota do Gemini — não consome quota de verdade.

A mensagem usada aqui é a resposta real que a API devolveu em 17/11/2026,
quando o limite diário do free tier estourou durante um teste no ar.
"""

from __future__ import annotations

from app.agents.llm import ErroLLM, ErroQuota, _erro_de_quota

MENSAGEM_REAL = (
    "429 You exceeded your current quota, please check your plan and billing "
    "details. For more information on this error, head to: "
    "https://aistudio.google.com/docs/rate-limits. "
    "[violations { quota_metric: "
    '"generativelanguage.googleapis.com/generate_content_free_tier_requests" '
    'quota_id: "GenerateRequestsPerDayPerProjectPerModel-FreeTier" '
    'quota_dimensions { key: "model" value: "gemini-3.6-flash" } '
    "quota_value: 20 } , retry_delay { seconds: 21171 } ]"
)


def test_reconhece_a_cota_e_le_o_tempo_de_espera():
    erro = _erro_de_quota(Exception(MENSAGEM_REAL))
    assert isinstance(erro, ErroQuota)
    assert erro.segundos == 21171


def test_reconhece_a_cota_sem_tempo_de_espera():
    erro = _erro_de_quota(Exception("429 RESOURCE_EXHAUSTED: quota exceeded"))
    assert isinstance(erro, ErroQuota)
    assert erro.segundos is None


def test_formato_alternativo_do_tempo_de_espera():
    erro = _erro_de_quota(
        Exception("429 Too Many Requests. Please retry in 58.4s.")
    )
    assert erro is not None
    assert erro.segundos == 58


def test_nao_confunde_outras_falhas_com_cota():
    assert _erro_de_quota(Exception("400 API_KEY_INVALID")) is None
    assert _erro_de_quota(Exception("timeout ao chamar o modelo")) is None
    assert _erro_de_quota(Exception("500 internal error")) is None


def test_erro_de_cota_continua_sendo_um_erro_de_llm():
    # Quem só quer saber que a geração falhou segue capturando ErroLLM.
    assert issubclass(ErroQuota, ErroLLM)
