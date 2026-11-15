"""Segmentação (chunking) do texto técnico para o pipeline de RAG."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.core.config import get_settings


@dataclass
class Chunk:
    """Um segmento de texto indexável."""

    id: str
    texto: str
    indice: int
    metadados: dict[str, str] = field(default_factory=dict)


_SEPARADORES = ["\n\n", "\n", ". ", "; ", ", ", " "]


def _dividir_recursivo(texto: str, tamanho: int, separadores: list[str]) -> list[str]:
    """Divide respeitando a maior fronteira semântica que couber."""
    if len(texto) <= tamanho:
        return [texto] if texto.strip() else []

    if not separadores:
        # sem separador possível: corte duro
        return [texto[i : i + tamanho] for i in range(0, len(texto), tamanho)]

    sep, *resto = separadores
    partes = texto.split(sep)
    blocos: list[str] = []
    atual = ""

    for parte in partes:
        candidato = f"{atual}{sep}{parte}" if atual else parte
        if len(candidato) <= tamanho:
            atual = candidato
            continue
        if atual:
            blocos.append(atual)
        if len(parte) > tamanho:
            blocos.extend(_dividir_recursivo(parte, tamanho, resto))
            atual = ""
        else:
            atual = parte

    if atual.strip():
        blocos.append(atual)
    return [b for b in blocos if b.strip()]


def segmentar(
    texto: str,
    titulo_documento: str = "",
    tamanho: int | None = None,
    sobreposicao: int | None = None,
) -> list[Chunk]:
    """Segmenta o texto em chunks com sobreposição.

    A sobreposição preserva contexto entre fronteiras, evitando que uma
    definição técnica seja cortada ao meio e perca sentido na recuperação.
    """
    cfg = get_settings()
    tamanho = tamanho or cfg.chunk_size
    sobreposicao = sobreposicao if sobreposicao is not None else cfg.chunk_overlap

    if sobreposicao >= tamanho:
        raise ValueError("A sobreposição deve ser menor que o tamanho do chunk.")

    texto = re.sub(r"\n{3,}", "\n\n", texto.strip())
    if not texto:
        return []

    brutos = _dividir_recursivo(texto, tamanho, _SEPARADORES)

    # aplica sobreposição: cada chunk recebe a cauda do anterior
    chunks: list[Chunk] = []
    for i, bloco in enumerate(brutos):
        if i > 0 and sobreposicao > 0:
            cauda = brutos[i - 1][-sobreposicao:]
            bloco = f"{cauda} {bloco}".strip()
        chunks.append(
            Chunk(
                id=f"chunk-{i:04d}",
                texto=bloco,
                indice=i,
                metadados={"documento": titulo_documento, "indice": str(i)},
            )
        )

    return chunks


def estatisticas(chunks: list[Chunk]) -> dict[str, float | int]:
    """Métricas de segmentação, exibidas na interface para transparência."""
    if not chunks:
        return {"total_chunks": 0, "media_caracteres": 0, "min": 0, "max": 0}
    tamanhos = [len(c.texto) for c in chunks]
    return {
        "total_chunks": len(chunks),
        "media_caracteres": round(sum(tamanhos) / len(tamanhos), 1),
        "min": min(tamanhos),
        "max": max(tamanhos),
    }
