"""Geração de embeddings vetoriais.

Provedor escolhido por `EMBEDDING_PROVIDER` (ou, se vazio, por `LLM_PROVIDER`):
Google Gemini (padrão) ou NVIDIA.
Fallback: embedding léxico determinístico (hashing trick), usado quando não há
chave do provedor escolhido ou quando a API falha — mantém o pipeline
executável offline, com qualidade de recuperação inferior. O backend em uso é
sempre reportado.
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
        self._nvidia = False
        self.backend = "lexico-fallback"

        provedor = self._cfg.provedor_embeddings
        if provedor == "nvidia":
            # Provedor escolhido sem chave: cai para o léxico, e não para o
            # Gemini — trocar de provedor às escondidas mascararia a config.
            if self._cfg.nvidia_configurado:
                self._nvidia = True
                self.backend = f"nvidia:{self._cfg.nvidia_embedding_model}"
        elif self._cfg.gemini_configurado:
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

    @property
    def usando_api(self) -> bool:
        return self._cliente is not None or self._nvidia

    def _degradar(self) -> None:
        nome = "NVIDIA" if self._nvidia else "Gemini"
        self._cliente = None
        self._nvidia = False
        self.backend = f"lexico-fallback (degradado da API {nome})"

    def _embed_nvidia(self, textos: list[str], tipo: str) -> list[list[float]]:
        """Embeddings via NVIDIA, em lotes.

        O modelo é assimétrico: exige `input_type` (`passage` para indexar,
        `query` para buscar) e responde 400 sem ele. Aceita vários textos por
        chamada, então um documento inteiro custa poucas requisições, contra uma
        por trecho no Gemini.
        """
        import requests

        url = f"{self._cfg.nvidia_base_url.rstrip('/')}/embeddings"
        cabecalhos = {
            "Authorization": f"Bearer {self._cfg.nvidia_api_key.strip()}",
            "Accept": "application/json",
        }
        vetores: list[list[float]] = []
        tamanho_lote = 16
        for i in range(0, len(textos), tamanho_lote):
            lote = textos[i : i + tamanho_lote]
            resposta = requests.post(
                url,
                headers=cabecalhos,
                json={
                    "model": self._cfg.nvidia_embedding_model,
                    "input": lote,
                    "input_type": tipo,
                    "encoding_format": "float",
                    "truncate": "END",
                },
                timeout=90,
            )
            if resposta.status_code != 200:
                raise ErroEmbedding(
                    f"NVIDIA embeddings: HTTP {resposta.status_code} — "
                    f"{resposta.text[:160]}"
                )
            itens = sorted(resposta.json()["data"], key=lambda d: d["index"])
            if len(itens) != len(lote):
                raise ErroEmbedding("NVIDIA embeddings: número de vetores inesperado.")
            vetores.extend(list(item["embedding"]) for item in itens)
        return vetores

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
        if self.usando_api:
            try:
                if self._nvidia:
                    return self._embed_nvidia(textos, "passage")
                return self._embed_gemini(textos, "retrieval_document")
            except Exception:
                # degrada para o fallback em vez de derrubar o pipeline
                self._degradar()
        return [_embedding_lexico(t) for t in textos]

    def embed_consulta(self, texto: str) -> list[float]:
        """Embedding da pergunta/consulta de recuperação."""
        if self.usando_api:
            try:
                if self._nvidia:
                    return self._embed_nvidia([texto], "query")[0]
                return self._embed_gemini([texto], "retrieval_query")[0]
            except Exception:
                self._degradar()
        return _embedding_lexico(texto)


_servico: ServicoEmbeddings | None = None


def get_servico_embeddings() -> ServicoEmbeddings:
    global _servico
    if _servico is None:
        _servico = ServicoEmbeddings()
    return _servico
