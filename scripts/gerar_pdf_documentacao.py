"""Gera docs/NovaMente_Documentacao.pdf a partir de docs/DOCUMENTACAO_PROJETO.md.

O PDF é o entregável "Documentação" do No Country. Mantê-lo como script garante
que ele possa ser refeito sempre que o texto mudar.

Uso:
    python scripts/gerar_pdf_documentacao.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

RAIZ = Path(__file__).resolve().parents[1]
ORIGEM = RAIZ / "docs" / "DOCUMENTACAO_PROJETO.md"
DESTINO = RAIZ / "docs" / "NovaMente_Documentacao.pdf"

TINTA = "#16254C"
CINZA = "#5D6B7E"


def escapar(texto: str) -> str:
    return texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline(texto: str) -> str:
    """Converte **negrito**, *itálico* e `código` do Markdown para tags do PDF."""
    texto = escapar(texto)
    texto = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", texto)
    texto = re.sub(r"`(.+?)`", r'<font face="Courier">\1</font>', texto)
    texto = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", texto)
    return texto


def construir() -> list:
    base = getSampleStyleSheet()
    estilos = {
        "h1": ParagraphStyle(
            "h1", parent=base["Title"], fontSize=22, leading=26,
            textColor=TINTA, spaceAfter=4, alignment=0,
        ),
        "h2": ParagraphStyle(
            "h2", parent=base["Heading1"], fontSize=15, leading=19,
            textColor=TINTA, spaceBefore=18, spaceAfter=6,
        ),
        "h3": ParagraphStyle(
            "h3", parent=base["Heading2"], fontSize=12.5, leading=16,
            textColor=TINTA, spaceBefore=12, spaceAfter=4,
        ),
        "corpo": ParagraphStyle(
            "corpo", parent=base["Normal"], fontSize=10.5, leading=15.5,
            alignment=TA_JUSTIFY, spaceAfter=7,
        ),
        "apoio": ParagraphStyle(
            "apoio", parent=base["Normal"], fontSize=10, leading=14,
            textColor=CINZA, spaceAfter=3,
        ),
    }

    linhas = ORIGEM.read_text(encoding="utf-8").split("\n")
    historia: list = []
    paragrafo: list[str] = []
    marcadores: list[str] = []
    titulo_lido = False

    def descarregar() -> None:
        nonlocal paragrafo, marcadores
        if paragrafo:
            historia.append(Paragraph(inline(" ".join(paragrafo)), estilos["corpo"]))
            paragrafo = []
        if marcadores:
            historia.append(
                ListFlowable(
                    [
                        ListItem(Paragraph(inline(m), estilos["corpo"]))
                        for m in marcadores
                    ],
                    bulletType="bullet",
                    leftIndent=14,
                )
            )
            historia.append(Spacer(1, 4))
            marcadores = []

    for linha in linhas:
        nua = linha.strip()

        if not nua:
            descarregar()
            continue

        if nua.startswith("### "):
            descarregar()
            historia.append(Paragraph(inline(nua[4:]), estilos["h3"]))
        elif nua.startswith("## "):
            descarregar()
            historia.append(Paragraph(inline(nua[3:]), estilos["h2"]))
        elif nua.startswith("# "):
            descarregar()
            historia.append(Paragraph(inline(nua[2:]), estilos["h1"]))
            titulo_lido = True
        elif nua.startswith(("- ", "* ")):
            if paragrafo:
                descarregar()
            marcadores.append(nua[2:])
        elif not titulo_lido:
            # subtítulo e créditos antes do primeiro cabeçalho
            historia.append(Paragraph(inline(nua), estilos["apoio"]))
        else:
            paragrafo.append(nua)

    descarregar()
    return historia


def main() -> int:
    if not ORIGEM.exists():
        print(f"Origem nao encontrada: {ORIGEM}")
        return 1

    doc = SimpleDocTemplate(
        str(DESTINO),
        pagesize=A4,
        leftMargin=2.3 * cm,
        rightMargin=2.3 * cm,
        topMargin=2.2 * cm,
        bottomMargin=2.0 * cm,
        title="NovaMente — Documentacao do Projeto",
        author="Grupo 10 — Hackathon ONE G10",
    )
    doc.build(construir())
    print(f"PDF gerado: {DESTINO} ({DESTINO.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
