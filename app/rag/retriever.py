"""Camada de recuperação: indexa um documento e devolve o contexto ancorado."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.config import get_settings
from app.rag.chunking import Chunk, estatisticas, segmentar
from app.rag.embeddings import get_servico_embeddings
from app.rag.vector_store import ResultadoBusca, criar_vector_store


@dataclass
class ContextoRecuperado:
    """Resultado da etapa de recuperação do RAG."""

    trechos: list[ResultadoBusca]
    chunks_indexados: int
    backend_vetorial: str
    backend_embeddings: str
    estatisticas_chunks: dict[str, float | int] = field(default_factory=dict)

    @property
    def texto_contexto(self) -> str:
        """Contexto formatado para injeção no prompt, com rótulos de origem."""
        return "\n\n".join(
            f"[FONTE {i + 1} · chunk {t.chunk_id} · similaridade {t.score}]\n{t.texto}"
            for i, t in enumerate(self.trechos)
        )

    @property
    def score_medio(self) -> float:
        if not self.trechos:
            return 0.0
        return round(sum(t.score for t in self.trechos) / len(self.trechos), 4)


# Consultas de recuperação por formato pedagógico: cada formato precisa de
# aspectos diferentes do documento original.
_CONSULTA_POR_FORMATO = {
    "Flashcards": "definições, conceitos-chave, termos técnicos e suas explicações",
    "Quiz": "fatos verificáveis, regras, limites, comportamentos e exceções",
    "Tutorial": "passos de configuração, procedimentos, comandos e ordem de execução",
    "Resumo Executivo": "propósito, benefícios, custos, riscos e impacto de negócio",
    "Roteiro de Aula": "estrutura conceitual, progressão didática e exemplos",
}

_CONSULTA_POR_PERFIL = {
    "Iniciante": "explicações introdutórias, analogias e fundamentos",
    "Transição de Carreira": "fundamentos e vocabulário essencial",
    "Desenvolvedor Júnior / Pleno": "implementação prática, parâmetros e exemplos de uso",
    "Líder Técnico / Arquiteto": "arquitetura, trade-offs, escalabilidade e segurança",
    "Gestor / Executivo (Não Técnico)": "valor de negócio, custos e riscos",
}


def montar_consulta(titulo: str, perfil: str, formato: str, nicho: str) -> str:
    """Combina os eixos de parametrização em uma consulta de recuperação."""
    partes = [
        titulo,
        _CONSULTA_POR_FORMATO.get(formato, "conceitos principais"),
        _CONSULTA_POR_PERFIL.get(perfil, "conteúdo técnico central"),
    ]
    if nicho and nicho != "Geral":
        partes.append(f"aplicação no setor de {nicho}")
    return " · ".join(p for p in partes if p)


def recuperar_contexto(
    conteudo: str,
    titulo: str,
    perfil: str,
    formato: str,
    nicho: str = "Geral",
    top_k: int | None = None,
) -> ContextoRecuperado:
    """Executa o pipeline de RAG: chunking -> embeddings -> busca vetorial."""
    cfg = get_settings()
    top_k = top_k or cfg.top_k

    chunks: list[Chunk] = segmentar(conteudo, titulo_documento=titulo)
    if not chunks:
        raise ValueError("Não foi possível segmentar o documento (conteúdo vazio).")

    store = criar_vector_store()
    indexados = store.indexar(chunks)

    consulta = montar_consulta(titulo, perfil, formato, nicho)
    trechos = store.buscar(consulta, k=min(top_k, indexados))

    return ContextoRecuperado(
        trechos=trechos,
        chunks_indexados=indexados,
        backend_vetorial=store.backend,
        backend_embeddings=get_servico_embeddings().backend,
        estatisticas_chunks=estatisticas(chunks),
    )
