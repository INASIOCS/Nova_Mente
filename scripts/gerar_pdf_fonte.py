"""Converte um documento de texto/Markdown em PDF, para compor os documentos
técnicos de origem usados nas demonstrações.

Uso:
    python scripts/gerar_pdf_fonte.py entrada.md "Título do PDF" saida.pdf
"""

from __future__ import annotations

import sys
from pathlib import Path

from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def escapar(texto: str) -> str:
    return texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def construir(entrada: Path, titulo: str, saida: Path) -> None:
    bruto = entrada.read_text(encoding="utf-8")

    base = getSampleStyleSheet()
    s_titulo = ParagraphStyle(
        "T", parent=base["Title"], fontSize=19, leading=23, spaceAfter=16
    )
    s_h1 = ParagraphStyle(
        "H1", parent=base["Heading1"], fontSize=14, spaceBefore=14, spaceAfter=6
    )
    s_h2 = ParagraphStyle(
        "H2", parent=base["Heading2"], fontSize=12, spaceBefore=10, spaceAfter=4
    )
    s_corpo = ParagraphStyle(
        "C",
        parent=base["Normal"],
        fontSize=10.5,
        leading=15,
        alignment=TA_JUSTIFY,
        spaceAfter=7,
    )
    s_item = ParagraphStyle(
        "I", parent=s_corpo, leftIndent=14, bulletIndent=4, spaceAfter=4
    )

    historia = [Paragraph(escapar(titulo), s_titulo)]
    paragrafo: list[str] = []

    def fechar_paragrafo() -> None:
        if paragrafo:
            historia.append(Paragraph(escapar(" ".join(paragrafo)), s_corpo))
            paragrafo.clear()

    for linha in bruto.splitlines():
        crua = linha.rstrip()
        limpa = crua.strip()

        if not limpa:
            fechar_paragrafo()
            continue

        if limpa.startswith("## "):
            fechar_paragrafo()
            historia.append(Paragraph(escapar(limpa[3:]), s_h2))
        elif limpa.startswith("# "):
            fechar_paragrafo()
            historia.append(Paragraph(escapar(limpa[2:]), s_h1))
        elif limpa[0].isdigit() and limpa[1:3] in (". ", ") "):
            fechar_paragrafo()
            historia.append(Paragraph(escapar(limpa), s_h2))
        elif limpa.startswith(("- ", "* ")):
            fechar_paragrafo()
            historia.append(
                Paragraph(escapar(limpa[2:]), s_item, bulletText="•")
            )
        elif limpa.isupper() and len(limpa) > 8:
            fechar_paragrafo()
            historia.append(Paragraph(escapar(limpa), s_h1))
        else:
            paragrafo.append(limpa)

    fechar_paragrafo()
    historia.append(Spacer(1, 12))

    saida.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(saida),
        pagesize=A4,
        leftMargin=2.2 * cm,
        rightMargin=2.2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=titulo,
        author="Documento técnico de origem",
    )
    doc.build(historia)
    print(f"PDF gerado: {saida} ({saida.stat().st_size:,} bytes)")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(__doc__)
        raise SystemExit(1)
    construir(Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]))
