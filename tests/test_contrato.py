"""Testes do contrato de dados — valida o exemplo oficial do briefing.

Rode com:
    python -m pytest tests -v
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.content import (
    RequisicaoAdaptacao,
    RespostaAdaptacao,
    validar_itens_do_formato,
)

# Exemplo de requisição transcrito do briefing do Hackathon ONE G10
REQUISICAO_BRIEFING = {
    "documento_titulo": "Introducao a Arquitetura de Redes VCN na OCI",
    "documento_conteudo": (
        "A Virtual Cloud Network (VCN) e uma rede privada e personalizavel "
        "configurada na Oracle Cloud Infrastructure. Semelhante a uma rede de data "
        "center tradicional, a VCN oferece controle total sobre seu ambiente de "
        "rede, incluindo sub-redes publicas e privadas, tabelas de roteamento, "
        "Internet Gateways, NAT Gateways e Security Lists para controle de trafego "
        "via regras de entrada (ingress) e saida (egress)."
    ),
    "perfil_destinatario": "Iniciante",
    "formato_saida": "Flashcards",
    "nicho_setor": "Geral",
    "nivel_detalhe": "Didatico",
}

# Exemplo de resposta transcrito do briefing
RESPOSTA_BRIEFING = {
    "status": "sucesso",
    "metadados": {
        "perfil_aplicado": "Iniciante",
        "formato_gerado": "Flashcards",
        "tempo_estimado_estudo_minutos": 5,
        "conceitos_chave": ["VCN", "Sub-redes", "Internet Gateway", "Security Lists"],
    },
    "conteudo_adaptado": {
        "titulo": "Dominando Redes na Nuvem (VCN) do Zero",
        "introducao_contextualizada": (
            "Imagine a VCN como o seu proprio bairro particular e seguro dentro da "
            "nuvem da Oracle, onde voce decide quem entra e quem sai."
        ),
        "itens": [
            {
                "frente": "O que e uma VCN na Oracle Cloud?",
                "verso": (
                    "E a sua rede virtual privada e personalizada dentro da nuvem da "
                    "Oracle, funcionando como a infraestrutura de rede da sua empresa."
                ),
                "dica_didatica": "Pense nela como o terreno cercado onde seus servidores moram.",
            },
            {
                "frente": "Para que servem as Security Lists (Listas de Seguranca)?",
                "verso": (
                    "Sao como porteiros virtuais com listas de regras que definem "
                    "exatamente que tipo de trafego de dados pode entrar ou sair da sua rede."
                ),
                "dica_didatica": "Regras de entrada (ingress) e regras de saida (egress).",
            },
        ],
    },
    "avaliacao_qualidade": {
        "ancoragem_fonte_score": 0.98,
        "clareza_pedagogica": "Alta",
        "observacoes": (
            "Linguagem ajustada com analogias para publico iniciante, sem jargoes excessivos."
        ),
    },
    "armazenamento_oci": {
        "bucket": "novamente-conteudos-educativos",
        "objeto_id": "conteudo-vcn-iniciante-flashcards-001.json",
        "status_upload": "concluido",
    },
}


class TestRequisicao:
    def test_exemplo_do_briefing_e_valido(self):
        req = RequisicaoAdaptacao.model_validate(REQUISICAO_BRIEFING)
        assert req.documento_titulo.startswith("Introducao")
        assert req.perfil_destinatario == "Iniciante"
        assert req.formato_saida == "Flashcards"

    def test_rejeita_conteudo_curto(self):
        dados = {**REQUISICAO_BRIEFING, "documento_conteudo": "curto"}
        with pytest.raises(ValidationError):
            RequisicaoAdaptacao.model_validate(dados)

    def test_rejeita_perfil_invalido(self):
        dados = {**REQUISICAO_BRIEFING, "perfil_destinatario": "Mestre Jedi"}
        with pytest.raises(ValidationError):
            RequisicaoAdaptacao.model_validate(dados)

    def test_rejeita_campo_desconhecido(self):
        dados = {**REQUISICAO_BRIEFING, "campo_inexistente": 1}
        with pytest.raises(ValidationError):
            RequisicaoAdaptacao.model_validate(dados)


class TestResposta:
    def test_exemplo_do_briefing_e_valido(self):
        resp = RespostaAdaptacao.model_validate(RESPOSTA_BRIEFING)
        assert resp.status == "sucesso"
        assert len(resp.conteudo_adaptado.itens) == 2
        assert resp.avaliacao_qualidade.ancoragem_fonte_score == 0.98
        assert resp.armazenamento_oci.status_upload == "concluido"

    def test_itens_de_flashcard_sao_reconhecidos(self):
        resp = RespostaAdaptacao.model_validate(RESPOSTA_BRIEFING)
        primeiro = resp.conteudo_adaptado.itens[0].model_dump()
        assert "frente" in primeiro and "verso" in primeiro

    def test_score_fora_do_intervalo_e_rejeitado(self):
        dados = {
            **RESPOSTA_BRIEFING,
            "avaliacao_qualidade": {
                **RESPOSTA_BRIEFING["avaliacao_qualidade"],
                "ancoragem_fonte_score": 1.5,
            },
        }
        with pytest.raises(ValidationError):
            RespostaAdaptacao.model_validate(dados)

    def test_serializacao_preserva_nomes_do_briefing(self):
        resp = RespostaAdaptacao.model_validate(RESPOSTA_BRIEFING)
        bruto = resp.model_dump(mode="json")
        assert set(bruto) >= {
            "status",
            "metadados",
            "conteudo_adaptado",
            "avaliacao_qualidade",
            "armazenamento_oci",
        }
        assert "tempo_estimado_estudo_minutos" in bruto["metadados"]
        assert "ancoragem_fonte_score" in bruto["avaliacao_qualidade"]


class TestValidacaoPorFormato:
    def test_quiz_valido(self):
        itens = [
            {
                "pergunta": "Qual gateway permite saida sem expor a instancia?",
                "opcoes": ["NAT Gateway", "Internet Gateway", "DRG", "LPG"],
                "indice_resposta_correta": 0,
                "justificativa": "O NAT Gateway permite trafego de saida sem entrada.",
            }
        ]
        validados = validar_itens_do_formato("Quiz", itens)
        assert validados[0].indice_resposta_correta == 0

    def test_quiz_com_indice_fora_do_intervalo(self):
        itens = [
            {
                "pergunta": "Pergunta",
                "opcoes": ["a", "b"],
                "indice_resposta_correta": 5,
                "justificativa": "x",
            }
        ]
        with pytest.raises(ValidationError):
            validar_itens_do_formato("Quiz", itens)

    def test_tutorial_valido(self):
        itens = [{"passo": 1, "titulo": "Criar a VCN", "conteudo": "Abra Networking."}]
        validados = validar_itens_do_formato("Tutorial", itens)
        assert validados[0].passo == 1
