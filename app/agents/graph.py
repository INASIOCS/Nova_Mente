"""Orquestração multi-agentes com LangGraph.

Grafo de decisão:

    roteador → pesquisador_rag → redator_pedagogico → critico_revisor
                                        ↑                    │
                                        └──── revisar ───────┤
                                                             └── finalizar → END

- **Roteador**: lê o documento e monta o plano didático.
- **Pesquisador RAG**: chunking + embeddings + busca vetorial (ancoragem).
- **Redator Pedagógico**: gera o material no formato pedido.
- **Crítico/Revisor**: audita fidelidade e clareza; pode devolver para revisão
  uma única vez (evita laço infinito e gasto de quota).

Se o LangGraph não estiver disponível no ambiente, o mesmo fluxo roda em modo
sequencial com idêntica lógica de decisão.
"""

from __future__ import annotations

import json
import logging
from typing import Any, TypedDict

from app.agents import prompts
from app.agents.fidelity import (
    RelatorioFidelidade,
    combinar_scores,
    verificar_fidelidade,
)
from app.agents.llm import ErroLLM, get_cliente_llm
from app.core.config import get_settings
from app.rag.retriever import ContextoRecuperado, recuperar_contexto

logger = logging.getLogger(__name__)


class EstadoNovaMente(TypedDict, total=False):
    """Estado compartilhado entre os agentes."""

    # entrada
    titulo: str
    conteudo: str
    perfil: str
    formato: str
    nicho: str
    nivel: str
    # etapas
    plano: dict[str, Any]
    contexto: ContextoRecuperado
    material: dict[str, Any]
    avaliacao: dict[str, Any]
    relatorio: RelatorioFidelidade
    # controle
    revisoes: int
    feedback: str
    trace: list[str]
    erros: list[str]


# ---------------------------------------------------------------------------
# Nós do grafo
# ---------------------------------------------------------------------------


def no_roteador(estado: EstadoNovaMente) -> EstadoNovaMente:
    """Agente Roteador: monta o plano didático a partir de uma amostra do doc."""
    trace = list(estado.get("trace", []))

    if not get_settings().agente_roteador_ativo:
        trace.append("roteador: desativado (modo econômico de quota)")
        return {**estado, "plano": {}, "trace": trace}

    cliente = get_cliente_llm()

    amostra = estado["conteudo"][:6000]
    prompt = f"""DOCUMENTO: "{estado["titulo"]}"

=== AMOSTRA DO DOCUMENTO ===
{amostra}
=== FIM DA AMOSTRA ===

Perfil alvo: {estado["perfil"]}
Formato alvo: {estado["formato"]}
Nicho: {estado["nicho"]}

Monte o plano didático."""

    try:
        plano = cliente.gerar_json(prompts.ROTEADOR_SISTEMA, prompt)
        trace.append(f"roteador: plano gerado ({cliente.caminho})")
    except ErroLLM as exc:
        logger.warning("Roteador falhou, seguindo sem plano: %s", exc)
        plano = {}
        trace.append(f"roteador: falhou, seguindo sem plano ({exc})")

    return {**estado, "plano": plano, "trace": trace}


def no_pesquisador_rag(estado: EstadoNovaMente) -> EstadoNovaMente:
    """Agente Pesquisador: executa o pipeline de RAG e ancora o conteúdo."""
    trace = list(estado.get("trace", []))

    contexto = recuperar_contexto(
        conteudo=estado["conteudo"],
        titulo=estado["titulo"],
        perfil=estado["perfil"],
        formato=estado["formato"],
        nicho=estado["nicho"],
    )
    trace.append(
        f"pesquisador_rag: {contexto.chunks_indexados} chunks indexados em "
        f"{contexto.backend_vetorial} · embeddings {contexto.backend_embeddings} · "
        f"{len(contexto.trechos)} trechos recuperados (sim. média {contexto.score_medio})"
    )
    return {**estado, "contexto": contexto, "trace": trace}


def no_redator(estado: EstadoNovaMente) -> EstadoNovaMente:
    """Agente Redator Pedagógico: gera o material no formato pedido."""
    trace = list(estado.get("trace", []))
    cliente = get_cliente_llm()
    contexto: ContextoRecuperado = estado["contexto"]

    prompt = prompts.montar_prompt_redator(
        titulo=estado["titulo"],
        perfil=estado["perfil"],
        formato=estado["formato"],
        nicho=estado["nicho"],
        nivel=estado["nivel"],
        contexto=contexto.texto_contexto,
        plano=estado.get("plano"),
        feedback_revisao=estado.get("feedback") or None,
    )

    material = cliente.gerar_json(prompts.REDATOR_SISTEMA, prompt)
    revisao_num = estado.get("revisoes", 0)
    trace.append(
        f"redator_pedagogico: material gerado "
        f"({'revisão ' + str(revisao_num) if revisao_num else 'primeira versão'}) "
        f"com {len(material.get('itens', []))} itens"
    )
    return {**estado, "material": material, "trace": trace}


def no_critico(estado: EstadoNovaMente) -> EstadoNovaMente:
    """Agente Crítico/Revisor: audita fidelidade e clareza pedagógica."""
    trace = list(estado.get("trace", []))
    cliente = get_cliente_llm()
    contexto: ContextoRecuperado = estado["contexto"]
    material = estado["material"]

    # 1) verificação determinística (independe do LLM)
    relatorio = verificar_fidelidade(material, contexto.texto_contexto)

    # 2) auditoria semântica pelo LLM
    prompt = prompts.montar_prompt_critico(
        perfil=estado["perfil"],
        formato=estado["formato"],
        contexto=contexto.texto_contexto,
        material_gerado=json.dumps(material, ensure_ascii=False, indent=2)[:12000],
    )
    try:
        avaliacao = cliente.gerar_json(prompts.CRITICO_SISTEMA, prompt)
    except ErroLLM as exc:
        logger.warning("Crítico falhou, usando apenas o score léxico: %s", exc)
        avaliacao = {
            "ancoragem_fonte_score": relatorio.score_lexico,
            "clareza_pedagogica": "Média",
            "observacoes": f"Auditoria por LLM indisponível ({exc}). "
            f"Score baseado apenas na verificação léxica: {relatorio.resumo()}.",
            "precisa_revisao": False,
            "feedback_para_revisao": "",
        }

    # 3) score combinado
    score_llm = float(avaliacao.get("ancoragem_fonte_score", 0.0) or 0.0)
    score_final = combinar_scores(score_llm, relatorio)
    avaliacao["ancoragem_fonte_score"] = score_final
    avaliacao["score_llm"] = round(score_llm, 2)
    avaliacao["score_lexico"] = relatorio.score_lexico

    observacoes = str(avaliacao.get("observacoes", "")).strip()
    avaliacao["observacoes"] = (
        f"{observacoes} Verificação léxica: {relatorio.resumo()}."
    ).strip()

    feedback = str(avaliacao.get("feedback_para_revisao", "") or "")
    if relatorio.numeros_orfaos:
        feedback += (
            "\n- Remova ou corrija estes números, que não existem no documento de "
            f"origem: {', '.join(relatorio.numeros_orfaos[:8])}."
        )
    if relatorio.identificadores_orfaos:
        feedback += (
            "\n- Remova estes identificadores/termos que não constam na fonte: "
            f"{', '.join(relatorio.identificadores_orfaos[:8])}."
        )

    trace.append(
        f"critico_revisor: score final {score_final} "
        f"(LLM {round(score_llm, 2)} · léxico {relatorio.score_lexico}) · "
        f"clareza {avaliacao.get('clareza_pedagogica', 'n/d')}"
    )

    return {
        **estado,
        "avaliacao": avaliacao,
        "relatorio": relatorio,
        "feedback": feedback.strip(),
        "trace": trace,
    }


def decidir_proximo(estado: EstadoNovaMente) -> str:
    """Aresta condicional: revisar ou finalizar."""
    cfg = get_settings()
    avaliacao = estado.get("avaliacao", {})
    score = float(avaliacao.get("ancoragem_fonte_score", 1.0) or 0.0)
    pediu_revisao = bool(avaliacao.get("precisa_revisao", False))
    revisoes = estado.get("revisoes", 0)

    if revisoes >= cfg.max_revisoes:
        return "finalizar"
    if score < cfg.limite_revisao or pediu_revisao:
        return "revisar"
    return "finalizar"


def no_incrementar_revisao(estado: EstadoNovaMente) -> EstadoNovaMente:
    """Contabiliza a rodada de revisão antes de voltar ao redator."""
    trace = list(estado.get("trace", []))
    revisoes = estado.get("revisoes", 0) + 1
    trace.append(f"roteador: devolvendo para revisão (rodada {revisoes})")
    return {**estado, "revisoes": revisoes, "trace": trace}


# ---------------------------------------------------------------------------
# Construção do grafo
# ---------------------------------------------------------------------------


def _executar_com_langgraph(estado_inicial: EstadoNovaMente) -> EstadoNovaMente:
    from langgraph.graph import END, StateGraph

    grafo = StateGraph(EstadoNovaMente)
    grafo.add_node("roteador", no_roteador)
    grafo.add_node("pesquisador_rag", no_pesquisador_rag)
    grafo.add_node("redator_pedagogico", no_redator)
    grafo.add_node("critico_revisor", no_critico)
    grafo.add_node("preparar_revisao", no_incrementar_revisao)

    grafo.set_entry_point("roteador")
    grafo.add_edge("roteador", "pesquisador_rag")
    grafo.add_edge("pesquisador_rag", "redator_pedagogico")
    grafo.add_edge("redator_pedagogico", "critico_revisor")
    grafo.add_conditional_edges(
        "critico_revisor",
        decidir_proximo,
        {"revisar": "preparar_revisao", "finalizar": END},
    )
    grafo.add_edge("preparar_revisao", "redator_pedagogico")

    compilado = grafo.compile()
    resultado = compilado.invoke(estado_inicial, {"recursion_limit": 12})
    trace = list(resultado.get("trace", []))
    trace.insert(0, "orquestrador: LangGraph (grafo de decisão)")
    resultado["trace"] = trace
    return resultado  # type: ignore[return-value]


def _executar_sequencial(estado: EstadoNovaMente) -> EstadoNovaMente:
    """Mesmo fluxo sem LangGraph — fallback de ambiente."""
    estado = no_roteador(estado)
    estado = no_pesquisador_rag(estado)
    estado = no_redator(estado)
    estado = no_critico(estado)

    while decidir_proximo(estado) == "revisar":
        estado = no_incrementar_revisao(estado)
        estado = no_redator(estado)
        estado = no_critico(estado)

    trace = list(estado.get("trace", []))
    trace.insert(0, "orquestrador: cadeia sequencial (LangGraph indisponível)")
    estado["trace"] = trace
    return estado


def executar_grafo(
    titulo: str,
    conteudo: str,
    perfil: str,
    formato: str,
    nicho: str = "Geral",
    nivel: str = "Didatico",
) -> EstadoNovaMente:
    """Executa a orquestração completa de agentes."""
    estado_inicial: EstadoNovaMente = {
        "titulo": titulo,
        "conteudo": conteudo,
        "perfil": perfil,
        "formato": formato,
        "nicho": nicho,
        "nivel": nivel,
        "revisoes": 0,
        "feedback": "",
        "trace": [],
        "erros": [],
    }

    try:
        return _executar_com_langgraph(estado_inicial)
    except ImportError:
        logger.warning("LangGraph não instalado — usando cadeia sequencial.")
        return _executar_sequencial(estado_inicial)
