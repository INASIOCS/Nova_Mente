"""Pipeline de ponta a ponta: RAG → agentes → validação → persistência."""

from __future__ import annotations

import logging
import re
import unicodedata
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.agents.graph import executar_grafo
from app.schemas.content import (
    ArmazenamentoOCI,
    AvaliacaoQualidade,
    ConteudoAdaptado,
    MetadadosAprendizado,
    RequisicaoAdaptacao,
    RespostaAdaptacao,
    validar_itens_do_formato,
)
from app.storage.factory import criar_storage

logger = logging.getLogger(__name__)


class ErroPipeline(Exception):
    """Falha na execução do pipeline."""


@dataclass
class Diagnostico:
    """Informação de execução exibida na interface (transparência do pipeline)."""

    trace: list[str] = field(default_factory=list)
    backend_vetorial: str = ""
    backend_embeddings: str = ""
    backend_llm: str = ""
    backend_storage: str = ""
    chunks_indexados: int = 0
    trechos_recuperados: int = 0
    similaridade_media: float = 0.0
    revisoes: int = 0
    avisos: list[str] = field(default_factory=list)
    estatisticas_chunks: dict[str, Any] = field(default_factory=dict)


def slugificar(texto: str, limite: int = 60) -> str:
    """Converte um texto em slug ASCII seguro para nome de objeto."""
    normalizado = unicodedata.normalize("NFKD", texto)
    ascii_only = normalizado.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_only).strip("-").lower()
    return (slug[:limite] or "documento").strip("-")


def montar_objeto_id(titulo: str, perfil: str, formato: str) -> str:
    """Nome do objeto no bucket, no padrão sugerido pelo briefing."""
    return (
        f"conteudos/{slugificar(titulo, 40)}"
        f"-{slugificar(perfil, 20)}"
        f"-{slugificar(formato, 20)}"
        f"-{uuid.uuid4().hex[:6]}.json"
    )


def _inteiro_seguro(valor: Any, padrao: int, minimo: int = 1, maximo: int = 600) -> int:
    try:
        n = int(float(valor))
    except (TypeError, ValueError):
        return padrao
    return max(minimo, min(maximo, n))


def _clareza_valida(valor: Any) -> str:
    texto = str(valor or "").strip().lower()
    mapa = {
        "alta": "Alta",
        "high": "Alta",
        "média": "Média",
        "media": "Média",
        "medium": "Média",
        "baixa": "Baixa",
        "low": "Baixa",
    }
    return mapa.get(texto, "Média")


def adaptar_conteudo(
    requisicao: RequisicaoAdaptacao,
    persistir: bool = True,
    documento_original: bytes | None = None,
    nome_documento_original: str | None = None,
) -> tuple[RespostaAdaptacao, Diagnostico]:
    """Executa o fluxo completo e devolve a resposta validada + diagnóstico."""
    diag = Diagnostico()

    perfil = str(requisicao.perfil_destinatario)
    formato = str(requisicao.formato_saida)
    nicho = str(requisicao.nicho_setor)
    nivel = str(requisicao.nivel_detalhe)

    # 1) Orquestração de agentes (inclui o pipeline de RAG)
    estado = executar_grafo(
        titulo=requisicao.documento_titulo,
        conteudo=requisicao.documento_conteudo,
        perfil=perfil,
        formato=formato,
        nicho=nicho,
        nivel=nivel,
    )

    material: dict[str, Any] = estado.get("material") or {}
    if not material.get("itens"):
        raise ErroPipeline(
            "O modelo não produziu itens de conteúdo. "
            "Verifique a GOOGLE_API_KEY e tente um documento menor."
        )

    contexto = estado.get("contexto")
    avaliacao_bruta = estado.get("avaliacao") or {}

    diag.trace = list(estado.get("trace", []))
    diag.revisoes = int(estado.get("revisoes", 0))
    if contexto is not None:
        diag.backend_vetorial = contexto.backend_vetorial
        diag.backend_embeddings = contexto.backend_embeddings
        diag.chunks_indexados = contexto.chunks_indexados
        diag.trechos_recuperados = len(contexto.trechos)
        diag.similaridade_media = contexto.score_medio
        diag.estatisticas_chunks = dict(contexto.estatisticas_chunks)

    from app.agents.llm import get_cliente_llm

    diag.backend_llm = get_cliente_llm().caminho

    # 2) Validação estrita dos itens contra o modelo do formato
    try:
        itens_validados = validar_itens_do_formato(formato, material.get("itens", []))
    except Exception as exc:
        raise ErroPipeline(
            f"O material gerado não respeitou o formato '{formato}': {exc}"
        ) from exc

    conteudo_adaptado = ConteudoAdaptado(
        titulo=str(material.get("titulo") or requisicao.documento_titulo),
        introducao_contextualizada=str(
            material.get("introducao_contextualizada") or ""
        ),
        itens=itens_validados,
    )

    metadados = MetadadosAprendizado(
        perfil_aplicado=perfil,
        formato_gerado=formato,
        tempo_estimado_estudo_minutos=_inteiro_seguro(
            material.get("tempo_estimado_estudo_minutos"), padrao=max(3, len(itens_validados))
        ),
        conceitos_chave=[str(c) for c in (material.get("conceitos_chave") or [])][:12],
        pre_requisitos=[str(p) for p in (material.get("pre_requisitos") or [])][:8],
    )

    avaliacao = AvaliacaoQualidade(
        ancoragem_fonte_score=float(
            avaliacao_bruta.get("ancoragem_fonte_score", 0.0) or 0.0
        ),
        clareza_pedagogica=_clareza_valida(avaliacao_bruta.get("clareza_pedagogica")),
        observacoes=str(avaliacao_bruta.get("observacoes") or ""),
    )

    # 3) Persistência (OCI Object Storage, com fallback local)
    storage, aviso = criar_storage()
    if aviso:
        diag.avisos.append(aviso)
    diag.backend_storage = storage.nome

    objeto_id = montar_objeto_id(requisicao.documento_titulo, perfil, formato)

    if persistir:
        # 3a) documento técnico original
        if documento_original:
            original_id = (
                f"originais/{slugificar(nome_documento_original or requisicao.documento_titulo, 50)}"
                f"-{uuid.uuid4().hex[:6]}"
                f"{_sufixo(nome_documento_original)}"
            )
            try:
                res_orig = storage.enviar_bytes(
                    documento_original, original_id, "application/octet-stream"
                )
                diag.trace.append(
                    f"storage: documento original -> {res_orig.status_upload} "
                    f"({res_orig.objeto_id})"
                )
            except Exception as exc:
                diag.avisos.append(f"Falha ao persistir o documento original: {exc}")

        # 3b) pacote educacional gerado
        pacote = {
            "gerado_em": datetime.now(timezone.utc).isoformat(),
            "requisicao": requisicao.model_dump(mode="json"),
            "metadados": metadados.model_dump(mode="json"),
            "conteudo_adaptado": conteudo_adaptado.model_dump(mode="json"),
            "avaliacao_qualidade": avaliacao.model_dump(mode="json"),
            "diagnostico_pipeline": {
                "trace": diag.trace,
                "backend_vetorial": diag.backend_vetorial,
                "backend_embeddings": diag.backend_embeddings,
                "backend_llm": diag.backend_llm,
                "revisoes": diag.revisoes,
            },
        }
        try:
            resultado_upload = storage.enviar_json(pacote, objeto_id)
        except Exception as exc:
            diag.avisos.append(f"Falha ao persistir o pacote gerado: {exc}")
            resultado_upload = None

        if resultado_upload is not None:
            armazenamento = ArmazenamentoOCI(
                bucket=resultado_upload.bucket,
                objeto_id=resultado_upload.objeto_id,
                status_upload=resultado_upload.status_upload,  # type: ignore[arg-type]
                backend=resultado_upload.backend,
                uri=resultado_upload.uri,
            )
            if resultado_upload.erro:
                diag.avisos.append(f"Object Storage: {resultado_upload.erro}")
        else:
            armazenamento = ArmazenamentoOCI(
                bucket=storage.bucket,
                objeto_id=objeto_id,
                status_upload="falhou",
                backend=storage.nome,
            )
    else:
        armazenamento = ArmazenamentoOCI(
            bucket=storage.bucket,
            objeto_id=objeto_id,
            status_upload="pendente",
            backend=storage.nome,
        )

    resposta = RespostaAdaptacao(
        status="sucesso",
        metadados=metadados,
        conteudo_adaptado=conteudo_adaptado,
        avaliacao_qualidade=avaliacao,
        armazenamento_oci=armazenamento,
    )
    return resposta, diag


def _sufixo(nome: str | None) -> str:
    if not nome or "." not in nome:
        return ".bin"
    return "." + nome.rsplit(".", 1)[-1].lower()
