"""Ingestão de documentos técnicos: PDF, Markdown e texto bruto."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

EXTENSOES_SUPORTADAS = {".pdf", ".md", ".markdown", ".txt", ".text"}


class ErroIngestao(Exception):
    """Falha ao ler ou extrair texto de um documento."""


@dataclass
class DocumentoIngerido:
    titulo: str
    conteudo: str
    origem: str
    formato: str
    num_paginas: int | None = None

    @property
    def num_caracteres(self) -> int:
        return len(self.conteudo)


def _limpar_texto(texto: str) -> str:
    """Normaliza espaços e remove artefatos comuns de extração de PDF."""
    texto = texto.replace("\x00", "")
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    # junta palavras quebradas por hifenização de fim de linha
    texto = re.sub(r"(\w)-\n(\w)", r"\1\2", texto)
    return texto.strip()


def _extrair_pdf(caminho: Path) -> tuple[str, int]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover
        raise ErroIngestao(
            "pypdf não está instalado. Rode: pip install -r requirements.txt"
        ) from exc

    try:
        leitor = PdfReader(str(caminho))
    except Exception as exc:
        raise ErroIngestao(f"Não foi possível abrir o PDF: {exc}") from exc

    partes: list[str] = []
    for pagina in leitor.pages:
        try:
            partes.append(pagina.extract_text() or "")
        except Exception:
            partes.append("")

    texto = _limpar_texto("\n\n".join(partes))
    if not texto:
        raise ErroIngestao(
            "O PDF não contém texto extraível (provavelmente é digitalizado). "
            "Converta para texto ou use OCR antes de enviar."
        )
    return texto, len(leitor.pages)


def _extrair_markdown(caminho: Path) -> str:
    bruto = caminho.read_text(encoding="utf-8", errors="replace")
    # remove blocos de código cercados? NÃO — eles são conteúdo técnico valioso.
    # Apenas tira a sintaxe de ênfase que polui o texto para o LLM.
    sem_enfase = re.sub(r"(\*\*|__|\*|_)", "", bruto)
    return _limpar_texto(sem_enfase)


def carregar_arquivo(caminho: str | Path, titulo: str | None = None) -> DocumentoIngerido:
    """Carrega um documento técnico do disco."""
    caminho = Path(caminho)
    if not caminho.exists():
        raise ErroIngestao(f"Arquivo não encontrado: {caminho}")

    sufixo = caminho.suffix.lower()
    if sufixo not in EXTENSOES_SUPORTADAS:
        raise ErroIngestao(
            f"Formato '{sufixo}' não suportado. "
            f"Use um destes: {', '.join(sorted(EXTENSOES_SUPORTADAS))}"
        )

    num_paginas: int | None = None
    if sufixo == ".pdf":
        conteudo, num_paginas = _extrair_pdf(caminho)
        formato = "pdf"
    elif sufixo in {".md", ".markdown"}:
        conteudo = _extrair_markdown(caminho)
        formato = "markdown"
    else:
        conteudo = _limpar_texto(
            caminho.read_text(encoding="utf-8", errors="replace")
        )
        formato = "texto"

    if len(conteudo) < 50:
        raise ErroIngestao(
            "O documento tem menos de 50 caracteres de texto útil — "
            "conteúdo insuficiente para gerar material didático."
        )

    return DocumentoIngerido(
        titulo=titulo or caminho.stem.replace("_", " ").replace("-", " ").strip(),
        conteudo=conteudo,
        origem=str(caminho),
        formato=formato,
        num_paginas=num_paginas,
    )


def carregar_bytes(
    dados: bytes, nome_arquivo: str, titulo: str | None = None
) -> DocumentoIngerido:
    """Carrega um documento a partir de bytes (upload via API/Streamlit)."""
    import tempfile

    sufixo = Path(nome_arquivo).suffix.lower()
    if sufixo not in EXTENSOES_SUPORTADAS:
        raise ErroIngestao(
            f"Formato '{sufixo}' não suportado. "
            f"Use um destes: {', '.join(sorted(EXTENSOES_SUPORTADAS))}"
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=sufixo) as tmp:
        tmp.write(dados)
        tmp_path = Path(tmp.name)

    try:
        doc = carregar_arquivo(tmp_path, titulo=titulo or Path(nome_arquivo).stem)
        doc.origem = nome_arquivo
        return doc
    finally:
        tmp_path.unlink(missing_ok=True)


def carregar_texto(conteudo: str, titulo: str) -> DocumentoIngerido:
    """Carrega um documento a partir de texto já em memória."""
    limpo = _limpar_texto(conteudo)
    if len(limpo) < 50:
        raise ErroIngestao("Texto muito curto (mínimo de 50 caracteres).")
    return DocumentoIngerido(
        titulo=titulo, conteudo=limpo, origem="texto_direto", formato="texto"
    )
