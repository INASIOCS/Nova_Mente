"""Gera os exemplos de execução exigidos pelo checklist do hackathon.

Cobre, em uma única rodada:
- os 3 formatos de ingestão suportados (Markdown, texto bruto e PDF);
- o MESMO documento adaptado para perfis e formatos diferentes (cenários 1 a 3);
- 5 execuções reais, acima do mínimo de 3 exigido.

Uso:
    python scripts/gerar_exemplos.py            # todos os cenários
    python scripts/gerar_exemplos.py 1 3        # apenas os cenários 1 e 3
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from app.export.exporters import para_markdown  # noqa: E402
from app.ingestion.loader import carregar_arquivo  # noqa: E402
from app.pipeline import adaptar_conteudo  # noqa: E402
from app.schemas.content import RequisicaoAdaptacao  # noqa: E402

FONTES = RAIZ / "docs" / "fontes"
# Pasta de saída. EXEMPLOS_SAIDA permite gerar uma rodada paralela (por exemplo
# com outro provedor de LLM, para comparar) sem sobrescrever os exemplos
# versionados em examples/, que são o estado entregue.
SAIDA = RAIZ / os.environ.get("EXEMPLOS_SAIDA", "examples")

VCN = FONTES / "oci_vcn_arquitetura_de_redes.md"
OBJ = FONTES / "oci_object_storage_conceitos.txt"
IAM = FONTES / "oci_iam_identidade_e_politicas.pdf"

CENARIOS: list[dict] = [
    {
        "id": 1,
        "slug": "vcn-iniciante-flashcards",
        "fonte": VCN,
        "descricao": "Mesmo documento (VCN) para público iniciante, em flashcards.",
        "perfil_destinatario": "Iniciante",
        "formato_saida": "Flashcards",
        "nicho_setor": "Geral",
        "nivel_detalhe": "Didatico",
    },
    {
        "id": 2,
        "slug": "vcn-arquiteto-resumo-executivo",
        "fonte": VCN,
        "descricao": "MESMO documento (VCN) para líder técnico, em resumo executivo.",
        "perfil_destinatario": "Líder Técnico / Arquiteto",
        "formato_saida": "Resumo Executivo",
        "nicho_setor": "Fintech",
        "nivel_detalhe": "Aprofundado",
    },
    {
        "id": 3,
        "slug": "vcn-desenvolvedor-quiz",
        "fonte": VCN,
        "descricao": "MESMO documento (VCN) para desenvolvedor, em quiz avaliativo.",
        "perfil_destinatario": "Desenvolvedor Júnior / Pleno",
        "formato_saida": "Quiz",
        "nicho_setor": "Geral",
        "nivel_detalhe": "Intermediario",
    },
    {
        "id": 4,
        "slug": "object-storage-gestor-resumo",
        "fonte": OBJ,
        "descricao": "Ingestão de TEXTO BRUTO, adaptado para público executivo.",
        "perfil_destinatario": "Gestor / Executivo (Não Técnico)",
        "formato_saida": "Resumo Executivo",
        "nicho_setor": "Saúde",
        "nivel_detalhe": "Didatico",
    },
    {
        "id": 5,
        "slug": "iam-desenvolvedor-tutorial",
        "fonte": IAM,
        "descricao": "Ingestão de PDF, adaptado como tutorial passo a passo.",
        "perfil_destinatario": "Desenvolvedor Júnior / Pleno",
        "formato_saida": "Tutorial",
        "nicho_setor": "Geral",
        "nivel_detalhe": "Intermediario",
    },
]


def executar(cenario: dict) -> dict:
    fonte: Path = cenario["fonte"]
    print(f"\n{'=' * 70}")
    print(f"CENÁRIO {cenario['id']} — {cenario['slug']}")
    print(f"{cenario['descricao']}")
    print(f"Fonte: {fonte.name}")
    print(
        f"Perfil: {cenario['perfil_destinatario']} | "
        f"Formato: {cenario['formato_saida']} | "
        f"Nicho: {cenario['nicho_setor']}"
    )
    print("=" * 70)

    if not fonte.exists():
        print(f"  !! fonte ausente: {fonte}")
        return {"id": cenario["id"], "status": "fonte_ausente"}

    documento = carregar_arquivo(fonte)
    print(
        f"  ingestão: {documento.formato} · {documento.num_caracteres:,} caracteres"
    )

    requisicao = RequisicaoAdaptacao(
        documento_titulo=documento.titulo,
        documento_conteudo=documento.conteudo,
        perfil_destinatario=cenario["perfil_destinatario"],
        formato_saida=cenario["formato_saida"],
        nicho_setor=cenario["nicho_setor"],
        nivel_detalhe=cenario["nivel_detalhe"],
    )

    inicio = time.perf_counter()
    resposta, diag = adaptar_conteudo(
        requisicao,
        documento_original=fonte.read_bytes(),
        nome_documento_original=fonte.name,
    )
    duracao = time.perf_counter() - inicio

    for linha in diag.trace:
        print(f"    · {linha}")
    for aviso in diag.avisos:
        print(f"    ! {aviso}")

    print(
        f"  resultado: {len(resposta.conteudo_adaptado.itens)} itens · "
        f"ancoragem {resposta.avaliacao_qualidade.ancoragem_fonte_score:.2f} · "
        f"clareza {resposta.avaliacao_qualidade.clareza_pedagogica} · "
        f"{duracao:.1f}s"
    )

    SAIDA.mkdir(parents=True, exist_ok=True)
    base = SAIDA / f"cenario-{cenario['id']}-{cenario['slug']}"

    pacote = {
        "cenario": {
            "id": cenario["id"],
            "descricao": cenario["descricao"],
            "documento_fonte": fonte.name,
            "formato_ingestao": documento.formato,
            "duracao_segundos": round(duracao, 1),
        },
        "requisicao": requisicao.model_dump(mode="json"),
        "resposta": resposta.model_dump(mode="json"),
        "diagnostico_pipeline": {
            "trace": diag.trace,
            "backend_llm": diag.backend_llm,
            "backend_embeddings": diag.backend_embeddings,
            "backend_vetorial": diag.backend_vetorial,
            "backend_storage": diag.backend_storage,
            "chunks_indexados": diag.chunks_indexados,
            "trechos_recuperados": diag.trechos_recuperados,
            "similaridade_media": diag.similaridade_media,
            "rodadas_de_revisao": diag.revisoes,
            "estatisticas_chunks": diag.estatisticas_chunks,
            "avisos": diag.avisos,
        },
    }

    base.with_suffix(".json").write_text(
        json.dumps(pacote, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    base.with_suffix(".md").write_text(para_markdown(resposta), encoding="utf-8")
    print(f"  salvo: {base.name}.json / {base.name}.md")

    return {
        "id": cenario["id"],
        "slug": cenario["slug"],
        "status": "ok",
        "fonte": fonte.name,
        "formato_ingestao": documento.formato,
        "perfil": cenario["perfil_destinatario"],
        "formato": cenario["formato_saida"],
        "itens": len(resposta.conteudo_adaptado.itens),
        "ancoragem": resposta.avaliacao_qualidade.ancoragem_fonte_score,
        "clareza": resposta.avaliacao_qualidade.clareza_pedagogica,
        "duracao_segundos": round(duracao, 1),
    }


def main() -> int:
    pedidos = {int(a) for a in sys.argv[1:] if a.isdigit()}
    cenarios = [c for c in CENARIOS if not pedidos or c["id"] in pedidos]

    resumo = []
    for cenario in cenarios:
        try:
            resumo.append(executar(cenario))
        except Exception as exc:  # noqa: BLE001
            print(f"  !! FALHOU: {type(exc).__name__}: {exc}")
            resumo.append(
                {"id": cenario["id"], "status": "erro", "erro": f"{type(exc).__name__}: {exc}"}
            )

    SAIDA.mkdir(parents=True, exist_ok=True)
    caminho_resumo = SAIDA / "RESUMO.json"

    # Rodar um subconjunto (ex.: `gerar_exemplos.py 5`) não pode apagar o
    # registro dos outros cenários, cujos arquivos continuam em examples/.
    # Regra: um resultado novo "ok" sempre substitui o anterior; um "erro"
    # só ocupa a vaga se ainda não houver um "ok" ali — senão uma falha de
    # cota deixaria o RESUMO em desacordo com os arquivos presentes.
    anteriores: list[dict] = []
    if caminho_resumo.exists():
        try:
            carregado = json.loads(caminho_resumo.read_text(encoding="utf-8"))
            anteriores = [r for r in carregado if isinstance(r, dict) and "id" in r]
        except (OSError, ValueError):
            anteriores = []

    por_id = {r["id"]: r for r in anteriores}
    for novo in resumo:
        antigo = por_id.get(novo["id"])
        if novo.get("status") == "ok" or antigo is None or antigo.get("status") != "ok":
            por_id[novo["id"]] = novo

    caminho_resumo.write_text(
        json.dumps([por_id[i] for i in sorted(por_id)], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\n{'=' * 70}")
    print("RESUMO")
    print("=" * 70)
    for r in resumo:
        if r.get("status") == "ok":
            print(
                f"  cenário {r['id']}: {r['perfil']} / {r['formato']} "
                f"({r['formato_ingestao']}) -> {r['itens']} itens · "
                f"ancoragem {r['ancoragem']:.2f} · {r['duracao_segundos']}s"
            )
        else:
            print(f"  cenário {r['id']}: {r.get('status')} {r.get('erro', '')}")

    ok = sum(1 for r in resumo if r.get("status") == "ok")
    print(f"\n{ok}/{len(resumo)} cenários concluídos.")
    return 0 if ok == len(resumo) else 1


if __name__ == "__main__":
    raise SystemExit(main())
