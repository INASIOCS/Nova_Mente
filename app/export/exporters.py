"""Exportação multiformato: Markdown, PDF didático e CSV compatível com Anki."""

from __future__ import annotations

import csv
import io
from typing import Any

from app.export.slides import para_pptx  # noqa: F401  (reexport público)
from app.schemas.content import RespostaAdaptacao


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------


def para_markdown(resposta: RespostaAdaptacao) -> str:
    """Documento Markdown pronto para publicar."""
    c = resposta.conteudo_adaptado
    m = resposta.metadados
    a = resposta.avaliacao_qualidade

    linhas: list[str] = [
        f"# {c.titulo}",
        "",
        f"> {c.introducao_contextualizada}",
        "",
        "## Ficha do material",
        "",
        f"- **Perfil:** {m.perfil_aplicado}",
        f"- **Formato:** {m.formato_gerado}",
        f"- **Tempo estimado de estudo:** {m.tempo_estimado_estudo_minutos} min",
    ]
    if m.conceitos_chave:
        linhas.append(f"- **Conceitos-chave:** {', '.join(m.conceitos_chave)}")
    if m.pre_requisitos:
        linhas.append(f"- **Pré-requisitos:** {', '.join(m.pre_requisitos)}")
    linhas += [
        f"- **Ancoragem na fonte:** {a.ancoragem_fonte_score:.2f}",
        f"- **Clareza pedagógica:** {a.clareza_pedagogica}",
        "",
        f"## Conteúdo — {m.formato_gerado}",
        "",
    ]

    for i, item in enumerate(c.itens, start=1):
        dados: dict[str, Any] = item.model_dump()

        if "frente" in dados:  # Flashcard
            linhas += [
                f"### {i}. {dados['frente']}",
                "",
                dados["verso"],
                "",
            ]
            if dados.get("dica_didatica"):
                linhas += [f"*Dica:* {dados['dica_didatica']}", ""]

        elif "pergunta" in dados:  # Quiz
            linhas += [f"### {i}. {dados['pergunta']}", ""]
            for j, opcao in enumerate(dados["opcoes"]):
                marca = "x" if j == dados["indice_resposta_correta"] else " "
                linhas.append(f"- [{marca}] {opcao}")
            linhas += ["", f"*Justificativa:* {dados['justificativa']}", ""]

        elif "passo" in dados:  # Tutorial
            linhas += [
                f"### Passo {dados['passo']} — {dados['titulo']}",
                "",
                dados["conteudo"],
                "",
            ]
            if dados.get("comando"):
                linhas += ["```bash", str(dados["comando"]), "```", ""]

        elif "topico" in dados:  # Resumo executivo
            linhas += [f"### {i}. {dados['topico']}", "", dados["descricao"], ""]
            if dados.get("impacto_negocio"):
                linhas += [f"**Impacto:** {dados['impacto_negocio']}", ""]

        elif "bloco" in dados:  # Roteiro de aula
            linhas += [
                f"### {dados['bloco']} ({dados['tempo_estimado_min']} min)",
                "",
                dados["fala"],
                "",
            ]
            if dados.get("recurso_visual"):
                linhas += [f"**Recurso visual:** {dados['recurso_visual']}", ""]

    linhas += [
        "---",
        "",
        f"*Observações da auditoria:* {a.observacoes}",
        "",
        "*Gerado por NovaMente — Hackathon ONE G10 (Oracle Next Education & Alura).*",
    ]
    return "\n".join(linhas)


# ---------------------------------------------------------------------------
# CSV para Anki
# ---------------------------------------------------------------------------


def para_csv_anki(resposta: RespostaAdaptacao) -> str:
    """CSV de duas colunas (frente; verso), importável no Anki."""
    buffer = io.StringIO()
    escritor = csv.writer(buffer, delimiter=";", quoting=csv.QUOTE_MINIMAL)
    escritor.writerow(["Frente", "Verso"])

    for item in resposta.conteudo_adaptado.itens:
        dados: dict[str, Any] = item.model_dump()

        if "frente" in dados:
            verso = dados["verso"]
            if dados.get("dica_didatica"):
                verso = f"{verso}<br><br><i>Dica: {dados['dica_didatica']}</i>"
            escritor.writerow([dados["frente"], verso])

        elif "pergunta" in dados:
            opcoes = "<br>".join(
                f"{chr(65 + j)}) {o}" for j, o in enumerate(dados["opcoes"])
            )
            correta = dados["opcoes"][dados["indice_resposta_correta"]]
            escritor.writerow(
                [
                    f"{dados['pergunta']}<br><br>{opcoes}",
                    f"<b>{correta}</b><br><br>{dados['justificativa']}",
                ]
            )

        elif "passo" in dados:
            escritor.writerow(
                [f"Passo {dados['passo']}: {dados['titulo']}", dados["conteudo"]]
            )

        elif "topico" in dados:
            escritor.writerow([dados["topico"], dados["descricao"]])

        elif "bloco" in dados:
            escritor.writerow([dados["bloco"], dados["fala"]])

    return buffer.getvalue()


# ---------------------------------------------------------------------------
# PDF didático
# ---------------------------------------------------------------------------


def para_pdf(resposta: RespostaAdaptacao) -> bytes:
    """PDF didático formatado. Requer reportlab."""
    try:
        from reportlab.lib.enums import TA_JUSTIFY
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            ListFlowable,
            ListItem,
            PageBreak,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
        )
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "reportlab não instalado. Rode: pip install -r requirements.txt"
        ) from exc

    def esc(texto: Any) -> str:
        return (
            str(texto)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2.2 * cm,
        rightMargin=2.2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=resposta.conteudo_adaptado.titulo,
        author="NovaMente",
    )

    base = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle(
        "TituloNM", parent=base["Title"], fontSize=20, leading=24, spaceAfter=6
    )
    estilo_sub = ParagraphStyle(
        "SubNM", parent=base["Normal"], fontSize=10, textColor="#555555", spaceAfter=14
    )
    estilo_h2 = ParagraphStyle(
        "H2NM", parent=base["Heading2"], fontSize=13, spaceBefore=12, spaceAfter=4
    )
    estilo_corpo = ParagraphStyle(
        "CorpoNM",
        parent=base["Normal"],
        fontSize=10.5,
        leading=15,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
    )
    estilo_nota = ParagraphStyle(
        "NotaNM",
        parent=base["Normal"],
        fontSize=9.5,
        leading=13,
        textColor="#444444",
        leftIndent=10,
        spaceAfter=10,
    )

    c = resposta.conteudo_adaptado
    m = resposta.metadados
    a = resposta.avaliacao_qualidade

    historia: list[Any] = [
        Paragraph(esc(c.titulo), estilo_titulo),
        Paragraph(
            f"{esc(m.formato_gerado)} · perfil {esc(m.perfil_aplicado)} · "
            f"{m.tempo_estimado_estudo_minutos} min de estudo",
            estilo_sub,
        ),
        Paragraph(esc(c.introducao_contextualizada), estilo_corpo),
        Spacer(1, 10),
    ]

    if m.conceitos_chave:
        historia.append(Paragraph("Conceitos-chave", estilo_h2))
        historia.append(
            ListFlowable(
                [
                    ListItem(Paragraph(esc(t), estilo_corpo))
                    for t in m.conceitos_chave
                ],
                bulletType="bullet",
                leftIndent=14,
            )
        )
    if m.pre_requisitos:
        historia.append(Paragraph("Pré-requisitos", estilo_h2))
        historia.append(
            ListFlowable(
                [
                    ListItem(Paragraph(esc(t), estilo_corpo))
                    for t in m.pre_requisitos
                ],
                bulletType="bullet",
                leftIndent=14,
            )
        )

    historia += [PageBreak(), Paragraph(esc(m.formato_gerado), estilo_h2)]

    for i, item in enumerate(c.itens, start=1):
        dados: dict[str, Any] = item.model_dump()

        if "frente" in dados:
            historia.append(Paragraph(f"{i}. {esc(dados['frente'])}", estilo_h2))
            historia.append(Paragraph(esc(dados["verso"]), estilo_corpo))
            if dados.get("dica_didatica"):
                historia.append(
                    Paragraph(f"Dica: {esc(dados['dica_didatica'])}", estilo_nota)
                )

        elif "pergunta" in dados:
            historia.append(Paragraph(f"{i}. {esc(dados['pergunta'])}", estilo_h2))
            for j, opcao in enumerate(dados["opcoes"]):
                marcador = "✔" if j == dados["indice_resposta_correta"] else "○"
                historia.append(
                    Paragraph(f"{marcador} {esc(opcao)}", estilo_corpo)
                )
            historia.append(
                Paragraph(
                    f"Justificativa: {esc(dados['justificativa'])}", estilo_nota
                )
            )

        elif "passo" in dados:
            historia.append(
                Paragraph(
                    f"Passo {dados['passo']} — {esc(dados['titulo'])}", estilo_h2
                )
            )
            historia.append(Paragraph(esc(dados["conteudo"]), estilo_corpo))
            if dados.get("comando"):
                historia.append(
                    Paragraph(
                        f'<font face="Courier">{esc(dados["comando"])}</font>',
                        estilo_nota,
                    )
                )

        elif "topico" in dados:
            historia.append(Paragraph(f"{i}. {esc(dados['topico'])}", estilo_h2))
            historia.append(Paragraph(esc(dados["descricao"]), estilo_corpo))
            if dados.get("impacto_negocio"):
                historia.append(
                    Paragraph(
                        f"Impacto: {esc(dados['impacto_negocio'])}", estilo_nota
                    )
                )

        elif "bloco" in dados:
            historia.append(
                Paragraph(
                    f"{esc(dados['bloco'])} ({dados['tempo_estimado_min']} min)",
                    estilo_h2,
                )
            )
            historia.append(Paragraph(esc(dados["fala"]), estilo_corpo))
            if dados.get("recurso_visual"):
                historia.append(
                    Paragraph(
                        f"Recurso visual: {esc(dados['recurso_visual'])}", estilo_nota
                    )
                )

    historia += [
        Spacer(1, 18),
        Paragraph(
            f"Ancoragem na fonte: {a.ancoragem_fonte_score:.2f} · "
            f"Clareza: {esc(a.clareza_pedagogica)}<br/>{esc(a.observacoes)}",
            estilo_nota,
        ),
        Paragraph(
            "Gerado por NovaMente — Hackathon ONE G10 "
            "(Oracle Next Education &amp; Alura).",
            estilo_nota,
        ),
    ]

    doc.build(historia)
    return buffer.getvalue()
