"""Interface Streamlit do NovaMente."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

# permite rodar com `streamlit run ui/app.py` a partir da raiz do projeto
RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from app.core.config import get_settings  # noqa: E402
from app.export.exporters import para_csv_anki, para_markdown, para_pdf  # noqa: E402
from app.ingestion.loader import (  # noqa: E402
    ErroIngestao,
    carregar_arquivo,
    carregar_bytes,
    carregar_texto,
)
from app.pipeline import ErroPipeline, adaptar_conteudo  # noqa: E402
from app.schemas.content import (  # noqa: E402
    FormatoSaida,
    NichoSetor,
    NivelDetalhe,
    PerfilDestinatario,
    RequisicaoAdaptacao,
)

st.set_page_config(
    page_title="NovaMente — Adaptação de Conteúdo Educacional",
    page_icon="🧠",
    layout="wide",
)

CSS = """
<style>
.bloco-item {
    border: 1px solid rgba(128,128,128,.28);
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 12px;
}
.rotulo {
    font-size: .74rem;
    text-transform: uppercase;
    letter-spacing: .06em;
    opacity: .65;
    margin-bottom: 4px;
}
.dica { font-size: .9rem; opacity: .8; font-style: italic; margin-top: 8px; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Estado
# ---------------------------------------------------------------------------

for chave, inicial in [
    ("resposta", None),
    ("diagnostico", None),
    ("respostas_quiz", {}),
]:
    if chave not in st.session_state:
        st.session_state[chave] = inicial


# ---------------------------------------------------------------------------
# Cabeçalho
# ---------------------------------------------------------------------------

st.title("🧠 NovaMente")
st.caption(
    "Sistema Inteligente de Adaptação e Geração de Conteúdo Educacional · "
    "RAG + Orquestração de Agentes · Hackathon ONE G10"
)

cfg = get_settings()

# ---------------------------------------------------------------------------
# Barra lateral
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Parâmetros de adaptação")

    perfil = st.selectbox(
        "Perfil do destinatário",
        [e.value for e in PerfilDestinatario],
        help="Define linguagem, profundidade e tipo de exemplo.",
    )
    formato = st.selectbox(
        "Formato pedagógico de saída",
        [e.value for e in FormatoSaida],
    )
    nicho = st.selectbox("Nicho / contexto", [e.value for e in NichoSetor])
    nivel = st.selectbox("Nível de detalhe", [e.value for e in NivelDetalhe])

    st.divider()
    st.subheader("Ambiente")
    if cfg.gemini_configurado:
        st.success(f"Gemini configurado · `{cfg.gemini_model}`")
    else:
        st.error("GOOGLE_API_KEY ausente — defina no arquivo `.env`.")
    st.caption(
        f"Persistência: `{cfg.storage_backend}` · bucket `{cfg.oci_bucket_name}`"
    )
    st.caption(f"Chunk {cfg.chunk_size} / overlap {cfg.chunk_overlap} / top-k {cfg.top_k}")


# ---------------------------------------------------------------------------
# Entrada do documento
# ---------------------------------------------------------------------------

st.subheader("1. Documento técnico de entrada")

exemplos = sorted((RAIZ / "docs" / "fontes").glob("*")) if (RAIZ / "docs" / "fontes").exists() else []
nomes_exemplos = [e.name for e in exemplos if e.is_file()]

aba_upload, aba_texto, aba_exemplo = st.tabs(
    ["📎 Upload de arquivo", "📝 Colar texto", "📚 Documento de exemplo"]
)

documento = None
bytes_originais: bytes | None = None
nome_original: str | None = None

with aba_upload:
    arquivo = st.file_uploader(
        "PDF, Markdown ou texto", type=["pdf", "md", "markdown", "txt"]
    )
    if arquivo is not None:
        bytes_originais = arquivo.getvalue()
        nome_original = arquivo.name
        try:
            documento = carregar_bytes(bytes_originais, arquivo.name)
            st.success(
                f"**{documento.titulo}** · {documento.formato} · "
                f"{documento.num_caracteres:,} caracteres"
                + (f" · {documento.num_paginas} páginas" if documento.num_paginas else "")
            )
        except ErroIngestao as exc:
            st.error(str(exc))

with aba_texto:
    titulo_manual = st.text_input("Título do documento", value="")
    texto_manual = st.text_area("Conteúdo técnico", height=220)
    if texto_manual.strip() and titulo_manual.strip():
        try:
            documento = carregar_texto(texto_manual, titulo_manual)
            bytes_originais = texto_manual.encode("utf-8")
            nome_original = f"{titulo_manual}.txt"
            st.success(f"{documento.num_caracteres:,} caracteres prontos.")
        except ErroIngestao as exc:
            st.error(str(exc))

with aba_exemplo:
    if not nomes_exemplos:
        st.info("Nenhum documento em `docs/fontes/`.")
    else:
        escolhido = st.selectbox("Documento", nomes_exemplos)
        if escolhido:
            caminho = RAIZ / "docs" / "fontes" / escolhido
            try:
                documento = carregar_arquivo(caminho)
                bytes_originais = caminho.read_bytes()
                nome_original = escolhido
                st.success(
                    f"**{documento.titulo}** · {documento.formato} · "
                    f"{documento.num_caracteres:,} caracteres"
                )
                with st.expander("Prévia do documento"):
                    st.text(documento.conteudo[:2500])
            except ErroIngestao as exc:
                st.error(str(exc))


# ---------------------------------------------------------------------------
# Execução
# ---------------------------------------------------------------------------

st.subheader("2. Gerar material didático")

col_botao, col_info = st.columns([1, 3])
with col_botao:
    gerar = st.button(
        "⚡ Gerar conteúdo", type="primary", use_container_width=True,
        disabled=documento is None,
    )
with col_info:
    if documento is None:
        st.caption("Carregue um documento acima para habilitar a geração.")
    else:
        st.caption(
            f"Pronto: **{perfil}** · **{formato}** · {nicho} · {nivel}"
        )

if gerar and documento is not None:
    try:
        requisicao = RequisicaoAdaptacao(
            documento_titulo=documento.titulo,
            documento_conteudo=documento.conteudo,
            perfil_destinatario=perfil,
            formato_saida=formato,
            nicho_setor=nicho,
            nivel_detalhe=nivel,
        )
    except Exception as exc:
        st.error(f"Parâmetros inválidos: {exc}")
    else:
        with st.status("Executando o pipeline…", expanded=True) as status:
            st.write("🧭 Agente Roteador — montando o plano didático")
            st.write("🔎 Agente Pesquisador — chunking, embeddings e busca vetorial")
            st.write("✍️ Agente Redator — adaptando ao perfil")
            st.write("🕵️ Agente Crítico — auditando fidelidade à fonte")
            try:
                resposta, diag = adaptar_conteudo(
                    requisicao,
                    documento_original=bytes_originais,
                    nome_documento_original=nome_original,
                )
                st.session_state["resposta"] = resposta
                st.session_state["diagnostico"] = diag
                st.session_state["respostas_quiz"] = {}
                status.update(label="Pipeline concluído", state="complete")
            except ErroPipeline as exc:
                status.update(label="Falha no pipeline", state="error")
                st.error(str(exc))
            except Exception as exc:  # noqa: BLE001
                status.update(label="Erro inesperado", state="error")
                st.error(f"{type(exc).__name__}: {exc}")


# ---------------------------------------------------------------------------
# Resultado
# ---------------------------------------------------------------------------

resposta = st.session_state.get("resposta")
diag = st.session_state.get("diagnostico")

if resposta is not None:
    st.divider()
    st.subheader("3. Resultado")

    m = resposta.metadados
    a = resposta.avaliacao_qualidade

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ancoragem na fonte", f"{a.ancoragem_fonte_score:.2f}")
    c2.metric("Clareza pedagógica", a.clareza_pedagogica)
    c3.metric("Tempo de estudo", f"{m.tempo_estimado_estudo_minutos} min")
    c4.metric("Itens gerados", len(resposta.conteudo_adaptado.itens))

    if diag and diag.avisos:
        for aviso in diag.avisos:
            st.warning(aviso)

    abas = st.tabs(
        ["📘 Conteúdo", "🎯 Quiz interativo", "🔬 Pipeline", "🧾 JSON", "⬇️ Exportar"]
    )

    # ---------------------------- Conteúdo ----------------------------
    with abas[0]:
        c = resposta.conteudo_adaptado
        st.markdown(f"### {c.titulo}")
        st.info(c.introducao_contextualizada)

        if m.conceitos_chave:
            st.markdown("**Conceitos-chave:** " + " · ".join(f"`{t}`" for t in m.conceitos_chave))
        if m.pre_requisitos:
            st.markdown("**Pré-requisitos:** " + ", ".join(m.pre_requisitos))

        st.markdown("---")

        for i, item in enumerate(c.itens, start=1):
            d = item.model_dump()

            if "frente" in d:
                with st.container():
                    st.markdown(
                        f"<div class='bloco-item'><div class='rotulo'>Flashcard {i}</div>"
                        f"<b>{d['frente']}</b></div>",
                        unsafe_allow_html=True,
                    )
                    with st.expander("Mostrar resposta"):
                        st.write(d["verso"])
                        if d.get("dica_didatica"):
                            st.caption(f"💡 {d['dica_didatica']}")

            elif "pergunta" in d:
                st.markdown(
                    f"<div class='bloco-item'><div class='rotulo'>Questão {i}</div>"
                    f"<b>{d['pergunta']}</b></div>",
                    unsafe_allow_html=True,
                )
                for j, opcao in enumerate(d["opcoes"]):
                    marca = "✅" if j == d["indice_resposta_correta"] else "▫️"
                    st.markdown(f"{marca} {opcao}")
                st.caption(f"📌 {d['justificativa']}")

            elif "passo" in d:
                st.markdown(
                    f"<div class='bloco-item'><div class='rotulo'>Passo {d['passo']}</div>"
                    f"<b>{d['titulo']}</b></div>",
                    unsafe_allow_html=True,
                )
                st.write(d["conteudo"])
                if d.get("comando"):
                    st.code(d["comando"], language="bash")

            elif "topico" in d:
                st.markdown(
                    f"<div class='bloco-item'><div class='rotulo'>Tópico {i}</div>"
                    f"<b>{d['topico']}</b></div>",
                    unsafe_allow_html=True,
                )
                st.write(d["descricao"])
                if d.get("impacto_negocio"):
                    st.caption(f"💼 {d['impacto_negocio']}")

            elif "bloco" in d:
                st.markdown(
                    f"<div class='bloco-item'><div class='rotulo'>"
                    f"{d['tempo_estimado_min']} min</div>"
                    f"<b>{d['bloco']}</b></div>",
                    unsafe_allow_html=True,
                )
                st.write(d["fala"])
                if d.get("recurso_visual"):
                    st.caption(f"🎬 {d['recurso_visual']}")

    # ------------------------ Quiz interativo -------------------------
    with abas[1]:
        questoes = [
            item.model_dump()
            for item in resposta.conteudo_adaptado.itens
            if "pergunta" in item.model_dump()
        ]
        if not questoes:
            st.info(
                "Este material não é um quiz. Gere com o formato **Quiz** "
                "para responder as questões aqui com feedback imediato."
            )
        else:
            st.caption("Responda e receba a justificativa na hora.")
            acertos = 0
            respondidas = 0

            for i, q in enumerate(questoes):
                st.markdown(f"**{i + 1}. {q['pergunta']}**")
                escolha = st.radio(
                    "Selecione:",
                    options=list(range(len(q["opcoes"]))),
                    format_func=lambda j, _q=q: _q["opcoes"][j],
                    index=None,
                    key=f"quiz_{i}",
                    label_visibility="collapsed",
                )
                if escolha is not None:
                    respondidas += 1
                    if escolha == q["indice_resposta_correta"]:
                        acertos += 1
                        st.success(f"Correto! {q['justificativa']}")
                    else:
                        correta = q["opcoes"][q["indice_resposta_correta"]]
                        st.error(
                            f"Não é essa. A resposta correta é **{correta}**. "
                            f"{q['justificativa']}"
                        )
                st.markdown("---")

            if respondidas:
                st.metric(
                    "Desempenho",
                    f"{acertos}/{respondidas}",
                    f"{(acertos / respondidas) * 100:.0f}% de acerto",
                )

    # ---------------------------- Pipeline ----------------------------
    with abas[2]:
        if diag is None:
            st.info("Sem diagnóstico disponível.")
        else:
            d1, d2, d3 = st.columns(3)
            d1.metric("Chunks indexados", diag.chunks_indexados)
            d2.metric("Trechos recuperados", diag.trechos_recuperados)
            d3.metric("Similaridade média", f"{diag.similaridade_media:.3f}")

            st.markdown("**Backends em uso**")
            st.json(
                {
                    "llm": diag.backend_llm,
                    "embeddings": diag.backend_embeddings,
                    "vector_store": diag.backend_vetorial,
                    "storage": diag.backend_storage,
                    "rodadas_de_revisao": diag.revisoes,
                }
            )

            if diag.estatisticas_chunks:
                st.markdown("**Segmentação**")
                st.json(diag.estatisticas_chunks)

            st.markdown("**Rastro dos agentes**")
            for passo in diag.trace:
                st.markdown(f"- {passo}")

            st.markdown("**Auditoria de fidelidade**")
            st.write(a.observacoes)

    # ------------------------------ JSON ------------------------------
    with abas[3]:
        st.caption("Saída estruturada exatamente no contrato do briefing.")
        st.json(resposta.model_dump(mode="json"))

    # ---------------------------- Exportar ----------------------------
    with abas[4]:
        nome_base = resposta.conteudo_adaptado.titulo.replace(" ", "_")[:50] or "novamente"

        st.download_button(
            "⬇️ JSON estruturado",
            data=json.dumps(resposta.model_dump(mode="json"), ensure_ascii=False, indent=2),
            file_name=f"{nome_base}.json",
            mime="application/json",
            use_container_width=True,
        )
        st.download_button(
            "⬇️ Markdown",
            data=para_markdown(resposta),
            file_name=f"{nome_base}.md",
            mime="text/markdown",
            use_container_width=True,
        )
        st.download_button(
            "⬇️ CSV para Anki",
            data=para_csv_anki(resposta),
            file_name=f"{nome_base}_anki.csv",
            mime="text/csv",
            use_container_width=True,
        )
        try:
            st.download_button(
                "⬇️ PDF didático",
                data=para_pdf(resposta),
                file_name=f"{nome_base}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except RuntimeError as exc:
            st.caption(f"PDF indisponível: {exc}")

        st.divider()
        st.markdown("**Persistência**")
        st.json(resposta.armazenamento_oci.model_dump(mode="json"))
