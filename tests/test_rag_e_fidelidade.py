"""Testes do pipeline de RAG (chunking) e da verificação anti-alucinação.

Estes testes não chamam a API do Gemini: exercitam a lógica determinística.
"""

from __future__ import annotations

from app.agents.fidelity import combinar_scores, verificar_fidelidade
from app.export.exporters import para_csv_anki, para_markdown
from app.ingestion.loader import carregar_texto
from app.rag.chunking import estatisticas, segmentar
from app.schemas.content import RespostaAdaptacao
from tests.test_contrato import RESPOSTA_BRIEFING

TEXTO_FONTE = (
    "A Virtual Cloud Network (VCN) e uma rede privada na Oracle Cloud Infrastructure. "
    "O Internet Gateway permite trafego bidirecional com a internet. "
    "O NAT Gateway permite que recursos de uma sub-rede privada iniciem conexoes de "
    "saida sem se tornarem alcancaveis de fora. "
    "As Security Lists definem regras de entrada (ingress) e de saida (egress). "
    "O bloco CIDR delimita a faixa de enderecos IP privados da rede."
) * 6


class TestChunking:
    def test_segmenta_e_respeita_o_tamanho(self):
        chunks = segmentar(TEXTO_FONTE, "VCN", tamanho=400, sobreposicao=50)
        assert len(chunks) > 1
        # tamanho + sobreposição é o teto possível de um chunk
        assert all(len(c.texto) <= 400 + 50 + 1 for c in chunks)

    def test_ids_sao_unicos_e_ordenados(self):
        chunks = segmentar(TEXTO_FONTE, "VCN", tamanho=300, sobreposicao=30)
        ids = [c.id for c in chunks]
        assert len(ids) == len(set(ids))
        assert [c.indice for c in chunks] == list(range(len(chunks)))

    def test_texto_vazio_gera_lista_vazia(self):
        assert segmentar("   ", "x") == []

    def test_sobreposicao_maior_que_tamanho_e_erro(self):
        try:
            segmentar(TEXTO_FONTE, "x", tamanho=100, sobreposicao=200)
        except ValueError:
            return
        raise AssertionError("deveria ter levantado ValueError")

    def test_estatisticas(self):
        chunks = segmentar(TEXTO_FONTE, "VCN", tamanho=400, sobreposicao=40)
        est = estatisticas(chunks)
        assert est["total_chunks"] == len(chunks)
        assert est["min"] > 0


class TestIngestao:
    def test_carrega_texto(self):
        doc = carregar_texto(TEXTO_FONTE, "VCN na OCI")
        assert doc.formato == "texto"
        assert doc.num_caracteres > 100


class TestFidelidade:
    def test_material_ancorado_tem_score_alto(self):
        material = {
            "titulo": "Redes na OCI",
            "itens": [
                {
                    "frente": "O que faz o NAT Gateway?",
                    "verso": (
                        "Permite que recursos de uma sub-rede privada iniciem conexoes "
                        "de saida sem se tornarem alcancaveis de fora."
                    ),
                }
            ],
        }
        rel = verificar_fidelidade(material, TEXTO_FONTE)
        assert rel.cobertura_termos > 0.7
        assert not rel.numeros_orfaos

    def test_numero_inventado_e_detectado(self):
        material = {
            "itens": [
                {
                    "frente": "Qual o limite de sub-redes?",
                    "verso": "O limite e de 3000 sub-redes por VCN.",
                }
            ]
        }
        rel = verificar_fidelidade(material, TEXTO_FONTE)
        assert "3000" in rel.numeros_orfaos
        assert rel.tem_suspeita

    def test_numero_inventado_derruba_o_score_combinado(self):
        material = {"itens": [{"frente": "p", "verso": "O custo e de 4500 dolares."}]}
        rel = verificar_fidelidade(material, TEXTO_FONTE)
        # ainda que o LLM diga que está perfeito, o veto léxico limita o score
        assert combinar_scores(1.0, rel) <= 0.79

    def test_score_combinado_fica_no_intervalo(self):
        rel = verificar_fidelidade({"itens": [{"frente": "a", "verso": "b"}]}, TEXTO_FONTE)
        assert 0.0 <= combinar_scores(0.9, rel) <= 1.0


class TestExportacao:
    def test_markdown_contem_titulo_e_itens(self):
        resp = RespostaAdaptacao.model_validate(RESPOSTA_BRIEFING)
        md = para_markdown(resp)
        assert resp.conteudo_adaptado.titulo in md
        assert "O que e uma VCN na Oracle Cloud?" in md
        assert "Ancoragem na fonte" in md

    def test_csv_anki_tem_cabecalho_e_linhas(self):
        resp = RespostaAdaptacao.model_validate(RESPOSTA_BRIEFING)
        csv_texto = para_csv_anki(resp)
        linhas = [linha for linha in csv_texto.splitlines() if linha.strip()]
        assert linhas[0].startswith("Frente;Verso")
        assert len(linhas) == 3  # cabeçalho + 2 flashcards
