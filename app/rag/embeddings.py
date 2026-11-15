"""Geração de embeddings vetoriais.

Primário: Google Gemini (`text-embedding-004`).
Fallback: embedding léxico determinístico (hashing trick), usado apenas quando
não há API key configurada — mantém o pipeline executável offline, com
qualidade de recuperação inferior. O backend em uso é sempre reportado.
"""

from __future__ import annotations

import hashlib
import math
import re

from app.core.config import get_settings

DIMENSAO_FALLBACK = 512


class ErroEmbedding(Exception):
    """Falha ao gerar embeddings."""


# ---------------------------------------------------------------------------
# Fallback léxico
# ---------------------------------------------------------------------------


def _tokenizar(texto: str) -> list[str]:
    return re.findall(r"[a-zà-ú0-9_]+", texto.lower())


def _embedding_lexico(texto: str, dim: int = DIMENSAO_FALLBACK) -> list[float]:
    """Hashing trick com normalização L2 — determinístico e sem dependências."""
    vetor = [0.0] * dim
    tokens = _tokenizar(texto)
    for token in tokens:
        h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
        vetor[h % dim] += 1.0
    norma = math.sqrt(sum(v * v for v in vetor))
    if norma == 0:
        return vetor
    return [v / norma for v in vetor]


# ---------------------------------------------------------------------------
# Serviço de embeddings
# ---------------------------------------------------------------------------


class ServicoEmbeddings:
    """Encapsula a geração de embeddings e informa qual backend está ativo."""

    def __init__(self) -> None:
        self._cfg = get_settings()
        self._cliente = None
        self.backend = "lexico-fallback"

        if self._cfg.gemini_configurado:
            try:
                import google.generativeai as genai

                genai.configure(api_key=self._cfg.google_api_key)
                self._cliente = genai
                self.backend = f"gemini:{self._cfg.gemini_embedding_model}"
            except Exception:
                self._cliente = None
                self.backend = "lexico-fallback"

    @property
    def usando_gemini(self) -> bool:
        return self._cliente is not None

    def _embed_gemini(self, textos: list[str], tipo: str) -> list[list[float]]:
        vetores: list[list[float]] = []
        for texto in textos:
            resposta = self._cliente.embed_content(  # type: ignore[union-attr]
                model=self._cfg.gemini_embedding_model,
                content=texto,
                task_type=tipo,
            )
            vetores.append(list(resposta["embedding"]))
        return vetores

    def embed_documentos(self, textos: list[str]) -> list[list[float]]:
        """Embeddings para indexação."""
        if not textos:
            return []
        if self._cliente is not None:
            try:
                return self._embed_gemini(textos, "retrieval_document")
            except Exception:
                # degrada para o fallback em vez de derrubar o pipeline
                self._cliente = None
                self.backend = "lexico-fallback (degradado da API Gemini)"
        return [_embedding_lexico(t) for t in textos]

    def embed_consulta(self, texto: str) -> list[float]:
        """Embedding da pergunta/consulta de recuperação."""
        if self._cliente is not None:
            try:
                return self._embed_gemini([texto], "retrieval_query")[0]
            except Exception:
                self._cliente = None
                self.backend = "lexico-fallback (degradado da API Gemini)"
        return _embedding_lexico(texto)


_servico: ServicoEmbeddings | None = None


def get_servico_embeddings() -> ServicoEmbeddings:
    global _servico
    if _servico is None:
        _servico = ServicoEmbeddings()
    return _servico
