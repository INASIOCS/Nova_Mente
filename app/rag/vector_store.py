"""Vector Store para busca vetorial.

Primário: ChromaDB (recomendado pelo edital).
Fallback: índice em memória com similaridade de cosseno em NumPy, usado se o
ChromaDB não estiver disponível no ambiente. A interface é a mesma.
"""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass
from typing import Protocol

from app.rag.chunking import Chunk
from app.rag.embeddings import get_servico_embeddings


@dataclass
class ResultadoBusca:
    chunk_id: str
    texto: str
    score: float
    metadados: dict[str, str]


class VectorStore(Protocol):
    backend: str

    def indexar(self, chunks: list[Chunk]) -> int: ...

    def buscar(self, consulta: str, k: int) -> list[ResultadoBusca]: ...


# ---------------------------------------------------------------------------
# Fallback: índice em memória
# ---------------------------------------------------------------------------


def _cosseno(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    produto = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return produto / (na * nb)


class VectorStoreMemoria:
    """Índice vetorial em memória — sem dependência externa."""

    backend = "memoria-cosseno"

    def __init__(self) -> None:
        self._embeddings = get_servico_embeddings()
        self._vetores: list[list[float]] = []
        self._chunks: list[Chunk] = []

    def indexar(self, chunks: list[Chunk]) -> int:
        if not chunks:
            return 0
        self._vetores = self._embeddings.embed_documentos([c.texto for c in chunks])
        self._chunks = list(chunks)
        return len(self._chunks)

    def buscar(self, consulta: str, k: int) -> list[ResultadoBusca]:
        if not self._chunks:
            return []
        vetor_consulta = self._embeddings.embed_consulta(consulta)
        pontuados = [
            (
                _cosseno(vetor_consulta, vetor),
                chunk,
            )
            for vetor, chunk in zip(self._vetores, self._chunks)
        ]
        pontuados.sort(key=lambda par: par[0], reverse=True)
        return [
            ResultadoBusca(
                chunk_id=chunk.id,
                texto=chunk.texto,
                score=round(score, 4),
                metadados=chunk.metadados,
            )
            for score, chunk in pontuados[:k]
        ]


# ---------------------------------------------------------------------------
# Primário: ChromaDB
# ---------------------------------------------------------------------------


class VectorStoreChroma:
    """Índice vetorial em ChromaDB (coleção efêmera por documento)."""

    backend = "chromadb"

    def __init__(self) -> None:
        import chromadb

        self._embeddings = get_servico_embeddings()
        self._cliente = chromadb.EphemeralClient()
        self._colecao = self._cliente.create_collection(
            name=f"novamente-{uuid.uuid4().hex[:12]}",
            metadata={"hnsw:space": "cosine"},
        )

    def indexar(self, chunks: list[Chunk]) -> int:
        if not chunks:
            return 0
        vetores = self._embeddings.embed_documentos([c.texto for c in chunks])
        self._colecao.add(
            ids=[c.id for c in chunks],
            documents=[c.texto for c in chunks],
            embeddings=vetores,
            metadatas=[c.metadados or {"indice": str(c.indice)} for c in chunks],
        )
        return len(chunks)

    def buscar(self, consulta: str, k: int) -> list[ResultadoBusca]:
        vetor = self._embeddings.embed_consulta(consulta)
        bruto = self._colecao.query(query_embeddings=[vetor], n_results=k)

        resultados: list[ResultadoBusca] = []
        ids = (bruto.get("ids") or [[]])[0]
        docs = (bruto.get("documents") or [[]])[0]
        distancias = (bruto.get("distances") or [[]])[0]
        metadados = (bruto.get("metadatas") or [[]])[0]

        for i, chunk_id in enumerate(ids):
            distancia = distancias[i] if i < len(distancias) else 1.0
            resultados.append(
                ResultadoBusca(
                    chunk_id=chunk_id,
                    texto=docs[i] if i < len(docs) else "",
                    # distância de cosseno -> similaridade
                    score=round(max(0.0, 1.0 - float(distancia)), 4),
                    metadados=dict(metadados[i]) if i < len(metadados) else {},
                )
            )
        return resultados


def criar_vector_store() -> VectorStore:
    """Instancia o melhor Vector Store disponível no ambiente."""
    try:
        return VectorStoreChroma()
    except Exception:
        return VectorStoreMemoria()
