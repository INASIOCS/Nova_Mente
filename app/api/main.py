"""API REST do NovaMente (FastAPI)."""

from __future__ import annotations

import logging

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from app.core.config import get_settings
from app.export.exporters import (
    para_csv_anki,
    para_markdown,
    para_pdf,
    para_pptx,
)
from app.ingestion.loader import ErroIngestao, carregar_bytes
from app.pipeline import ErroPipeline, adaptar_conteudo
from app.schemas.content import (
    FormatoSaida,
    NichoSetor,
    NivelDetalhe,
    PerfilDestinatario,
    RequisicaoAdaptacao,
    RespostaAdaptacao,
    RespostaErro,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("novamente.api")

app = FastAPI(
    title="NovaMente API",
    description=(
        "Sistema Inteligente de Adaptação e Geração de Conteúdo Educacional.\n\n"
        "Transforma documentação técnica em material didático personalizado "
        "usando RAG + orquestração de agentes, com persistência em "
        "OCI Object Storage.\n\n"
        "Hackathon ONE G10 — Oracle Next Education & Alura."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


# ---------------------------------------------------------------------------
# Tratamento de erros amigável
# ---------------------------------------------------------------------------


@app.exception_handler(ErroIngestao)
async def _erro_ingestao(_, exc: ErroIngestao):
    return JSONResponse(
        status_code=422,
        content=RespostaErro(
            mensagem="Não foi possível ler o documento enviado.", detalhe=str(exc)
        ).model_dump(),
    )


@app.exception_handler(ErroPipeline)
async def _erro_pipeline(_, exc: ErroPipeline):
    return JSONResponse(
        status_code=502,
        content=RespostaErro(
            mensagem="Falha ao gerar o conteúdo educacional.", detalhe=str(exc)
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def _erro_generico(_, exc: Exception):
    logger.exception("Erro não tratado")
    return JSONResponse(
        status_code=500,
        content=RespostaErro(
            mensagem="Erro interno inesperado. Tente novamente.", detalhe=str(exc)
        ).model_dump(),
    )


# ---------------------------------------------------------------------------
# Endpoints de apoio
# ---------------------------------------------------------------------------


@app.get("/", tags=["status"])
def raiz() -> dict:
    return {
        "servico": "NovaMente",
        "versao": "1.0.0",
        "documentacao": "/docs",
        "endpoint_principal": "POST /adaptar",
    }


@app.get("/saude", tags=["status"])
def saude(profundo: bool = False) -> dict:
    """Diagnóstico de configuração — útil para validar o deploy.

    Com `?profundo=true`, confirma também que o bucket responde. Essa checagem
    é opcional de propósito: este endpoint é o healthcheck do deploy e a camada
    Always Free tem cota de requisições de API, que um ping a cada poucos
    segundos consumiria sem necessidade.
    """
    cfg = get_settings()
    from app.agents.llm import get_cliente_llm
    from app.storage.factory import criar_storage

    storage, aviso = criar_storage()

    bucket_acessivel: bool | None = None
    if profundo:
        try:
            bucket_acessivel = storage.disponivel()
        except Exception as exc:  # nunca derruba o healthcheck
            bucket_acessivel = False
            aviso = f"{aviso + ' | ' if aviso else ''}Falha ao checar o bucket: {exc}"

    return {
        "status": "ok",
        "provedor_llm": cfg.provedor_llm,
        "llm_configurado": cfg.llm_configurado,
        "gemini_configurado": cfg.gemini_configurado,
        "nvidia_configurado": cfg.nvidia_configurado,
        "modelo_llm": cfg.modelo_llm_ativo,
        "caminho_llm": get_cliente_llm().caminho,
        "storage_backend_configurado": cfg.storage_backend,
        "storage_backend_ativo": storage.nome,
        "bucket": storage.bucket,
        "bucket_acessivel": bucket_acessivel,
        "aviso_storage": aviso,
    }


@app.get("/opcoes", tags=["status"])
def opcoes() -> dict:
    """Valores aceitos em cada eixo de parametrização."""
    return {
        "perfil_destinatario": [e.value for e in PerfilDestinatario],
        "formato_saida": [e.value for e in FormatoSaida],
        "nicho_setor": [e.value for e in NichoSetor],
        "nivel_detalhe": [e.value for e in NivelDetalhe],
    }


# ---------------------------------------------------------------------------
# Endpoint principal
# ---------------------------------------------------------------------------


@app.post(
    "/adaptar",
    response_model=RespostaAdaptacao,
    tags=["adaptacao"],
    summary="Adaptação de Conteúdo Educacional",
)
def adaptar(requisicao: RequisicaoAdaptacao) -> RespostaAdaptacao:
    """Recebe o material técnico e os parâmetros, devolve o pacote educativo."""
    resposta, diag = adaptar_conteudo(requisicao)
    logger.info(
        "adaptado | perfil=%s formato=%s score=%.2f backend_storage=%s",
        requisicao.perfil_destinatario,
        requisicao.formato_saida,
        resposta.avaliacao_qualidade.ancoragem_fonte_score,
        diag.backend_storage,
    )
    return resposta


@app.post(
    "/adaptar/upload",
    response_model=RespostaAdaptacao,
    tags=["adaptacao"],
    summary="Adaptação a partir de upload de arquivo (PDF, Markdown ou texto)",
)
async def adaptar_upload(
    arquivo: UploadFile = File(..., description="PDF, .md ou .txt"),
    perfil_destinatario: PerfilDestinatario = Form(...),
    formato_saida: FormatoSaida = Form(...),
    nicho_setor: NichoSetor = Form(NichoSetor.GERAL),
    nivel_detalhe: NivelDetalhe = Form(NivelDetalhe.DIDATICO),
    documento_titulo: str | None = Form(None),
) -> RespostaAdaptacao:
    dados = await arquivo.read()
    if not dados:
        raise HTTPException(status_code=422, detail="Arquivo vazio.")
    if len(dados) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Arquivo maior que o limite de {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
        )

    documento = carregar_bytes(
        dados, arquivo.filename or "documento.txt", titulo=documento_titulo
    )

    requisicao = RequisicaoAdaptacao(
        documento_titulo=documento.titulo,
        documento_conteudo=documento.conteudo,
        perfil_destinatario=perfil_destinatario,
        formato_saida=formato_saida,
        nicho_setor=nicho_setor,
        nivel_detalhe=nivel_detalhe,
    )
    resposta, _ = adaptar_conteudo(
        requisicao,
        documento_original=dados,
        nome_documento_original=arquivo.filename,
    )
    return resposta


# ---------------------------------------------------------------------------
# Exportação multiformato
# ---------------------------------------------------------------------------


@app.post("/exportar/markdown", tags=["exportacao"])
def exportar_markdown(resposta: RespostaAdaptacao) -> Response:
    return Response(
        content=para_markdown(resposta),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="novamente.md"'},
    )


@app.post("/exportar/csv-anki", tags=["exportacao"])
def exportar_csv(resposta: RespostaAdaptacao) -> Response:
    return Response(
        content=para_csv_anki(resposta),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="novamente-anki.csv"'},
    )


@app.post("/exportar/pptx", tags=["exportacao"])
def exportar_pptx(resposta: RespostaAdaptacao) -> Response:
    """Apresentação de aula em PowerPoint, um slide por item de conteúdo."""
    try:
        conteudo = para_pptx(resposta)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return Response(
        content=conteudo,
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "presentationml.presentation"
        ),
        headers={"Content-Disposition": 'attachment; filename="novamente.pptx"'},
    )


@app.post("/exportar/pdf", tags=["exportacao"])
def exportar_pdf(resposta: RespostaAdaptacao) -> Response:
    try:
        conteudo = para_pdf(resposta)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return Response(
        content=conteudo,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="novamente.pdf"'},
    )
