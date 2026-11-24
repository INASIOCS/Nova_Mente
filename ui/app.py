"""Interface Streamlit do NovaMente."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import streamlit as st

# permite rodar com `streamlit run ui/app.py` a partir da raiz do projeto
RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) in sys.path:
    sys.path.remove(str(RAIZ))
sys.path.insert(0, str(RAIZ))

# O Streamlit registra o proprio script em sys.modules com o nome do arquivo.
# Como este arquivo se chama "app.py", esse registro sequestra o nome "app" e
# quebra "import app.core". Removemos o registro quando ele nao for o pacote.
_conflito = sys.modules.get("app")
if _conflito is not None and not hasattr(_conflito, "__path__"):
    del sys.modules["app"]

from app.core.segredos_nuvem import (  # noqa: E402
    aplicar_segredos_do_streamlit,
)

# Na Streamlit Community Cloud nao existe .env: as credenciais chegam pelo
# painel (Settings -> Secrets). A ponte copia esses segredos para o ambiente
# e precisa rodar ANTES da primeira leitura da configuracao. Fora da nuvem
# ela nao faz nada e o .env segue sendo a fonte da verdade.
DIAGNOSTICO_SEGREDOS = aplicar_segredos_do_streamlit()

from app.core.config import get_settings  # noqa: E402
from app.export.exporters import (  # noqa: E402
    para_csv_anki,
    para_markdown,
    para_pdf,
    para_pptx,
)
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
    RespostaAdaptacao,
)

st.set_page_config(
    page_title="NovaMente — Núcleo de Conteúdo Educacional",
    page_icon="🎓",
    layout="wide",
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&family=Inter:wght@400;500;600&display=swap');

:root {
    --nm-tinta: #16254C;
    --nm-tinta-clara: #2E4A86;
    --nm-ouro: #C08A2E;
    --nm-grafite: #1F2733;
    --nm-cinza: #5D6B7E;
    --nm-palha: #F2F5FA;
    --nm-borda: #DCE3EE;
}

html, body, [data-testid="stAppViewContainer"], .stMarkdown, button, input, textarea {
    font-family: 'Inter', -apple-system, system-ui, sans-serif;
}
h1, h2, h3, h4 {
    font-family: 'Source Serif 4', Georgia, 'Times New Roman', serif !important;
    color: var(--nm-tinta) !important;
    letter-spacing: -.01em;
}
.block-container { padding-top: 1.4rem; max-width: 1220px; }
[data-testid="stAppDeployButton"] { display: none; }

/* ---------- cabeçalho institucional ---------- */
.nm-banner {
    display: flex; align-items: center; gap: 18px; flex-wrap: wrap;
    background: var(--nm-tinta); color: #fff;
    padding: 20px 28px; border-radius: 10px 10px 0 0;
}
.nm-brasao {
    width: 54px; height: 54px; flex: 0 0 54px; border-radius: 50%;
    background: var(--nm-ouro); color: var(--nm-tinta);
    display: flex; align-items: center; justify-content: center;
    font-family: 'Source Serif 4', serif; font-weight: 700; font-size: 21px;
}
.nm-instituicao {
    font-family: 'Source Serif 4', serif; font-size: 26px;
    font-weight: 700; line-height: 1.08; color: #fff;
}
.nm-unidade { font-size: 12.5px; color: #C9D4E8; letter-spacing: .04em; margin-top: 4px; }
.nm-selo {
    margin-left: auto; text-align: right; font-size: 10.5px;
    letter-spacing: .17em; text-transform: uppercase;
    color: var(--nm-ouro); font-weight: 700; line-height: 1.5;
}
.nm-selo span {
    display: block; color: #8FA3C9; letter-spacing: .04em;
    text-transform: none; font-weight: 400; font-size: 11.5px; margin-top: 4px;
}
.nm-regua { height: 4px; background: var(--nm-ouro); border-radius: 0 0 3px 3px; }
@media (max-width: 920px) { .nm-selo { display: none; } }
.nm-trilha { font-size: 12px; color: var(--nm-cinza); margin: 14px 0 4px; }

/* ---------- seções numeradas ---------- */
.nm-secao { margin: 26px 0 12px; border-top: 1px solid var(--nm-borda); padding-top: 18px; }
.nm-etapa {
    font-size: 10.5px; letter-spacing: .18em; text-transform: uppercase;
    color: var(--nm-ouro); font-weight: 700;
}
.nm-secao h2 { margin: 5px 0 2px; font-size: 26px; }
.nm-secao p { margin: 0; color: var(--nm-cinza); font-size: 13.5px; }

/* ---------- blocos de conteúdo ---------- */
.bloco-item {
    background: var(--nm-palha); border: 1px solid var(--nm-borda);
    border-radius: 8px; padding: 14px 18px; margin-bottom: 10px;
}
.bloco-item b {
    font-family: 'Source Serif 4', serif; font-size: 17px; color: var(--nm-tinta);
}
.rotulo {
    font-size: 10.5px; letter-spacing: .15em; text-transform: uppercase;
    color: var(--nm-ouro); font-weight: 700; margin-bottom: 5px; opacity: 1;
}
.dica { font-size: .9rem; color: var(--nm-cinza); font-style: italic; margin-top: 8px; }

/* ---------- componentes do Streamlit ---------- */
[data-testid="stSidebar"] { background: var(--nm-palha); border-right: 1px solid var(--nm-borda); }
[data-testid="stSidebar"] h2 { font-size: 19px; }
[data-testid="stMetricValue"] { font-family: 'Source Serif 4', serif; color: var(--nm-tinta); }
[data-testid="stMetricLabel"] p {
    text-transform: uppercase; letter-spacing: .1em; font-size: 11px; color: var(--nm-cinza);
}
.stTabs [data-baseweb="tab-list"] { border-bottom: 1px solid var(--nm-borda); }
.stTabs [data-baseweb="tab"] { font-size: 14px; font-weight: 500; }
.stButton > button { border-radius: 6px; font-weight: 600; }
.stDownloadButton > button { border-radius: 6px; font-weight: 500; }
.stDownloadButton > button[kind="secondary"] {
    border: 1px solid var(--nm-borda); background: #fff;
}
.stDownloadButton > button[kind="secondary"]:hover {
    border-color: var(--nm-tinta); color: var(--nm-tinta);
}
.stDownloadButton > button[kind="primary"] {
    background: var(--nm-tinta); border: 1px solid var(--nm-tinta);
    color: #fff; font-weight: 600;
}
.stDownloadButton > button[kind="primary"]:hover {
    background: var(--nm-tinta-clara); border-color: var(--nm-tinta-clara);
}

/* ---------- rodapé ---------- */
.nm-rodape {
    margin-top: 42px; padding: 18px 0 8px; border-top: 1px solid var(--nm-borda);
    font-size: 12px; color: var(--nm-cinza); line-height: 1.7;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def secao(etapa: str, titulo: str, descricao: str = "") -> None:
    """Cabeçalho de seção no padrão institucional."""
    apoio = f"<p>{descricao}</p>" if descricao else ""
    st.markdown(
        f"<div class='nm-secao'><span class='nm-etapa'>{etapa}</span>"
        f"<h2>{titulo}</h2>{apoio}</div>",
        unsafe_allow_html=True,
    )


# Brasil não adota horário de verão desde 2019, então o deslocamento fixo é
# exato — e evita depender do banco de fusos do sistema, que não existe em
# toda imagem de contêiner.
FUSO_BRASILIA = timezone(timedelta(hours=-3))

MATERIAIS_PRONTOS = sorted((RAIZ / "examples").glob("cenario-*.json"))


def _duracao_legivel(segundos: int) -> str:
    horas, resto = divmod(max(segundos, 0), 3600)
    minutos = resto // 60
    if horas and minutos:
        return f"{horas}h{minutos:02d}"
    if horas:
        return f"{horas}h"
    return f"{minutos} min"


def painel_de_cota(segundos: int | None, provedor: str = "Gemini") -> None:
    """Explica o 429 do provedor em vez de despejar o erro da API na tela.

    O tempo vem do `retry_delay` (Gemini) ou do `Retry-After` (NVIDIA) da própria
    resposta, então a mensagem continua correta em qualquer dia: não há data nem
    horário fixo no código.
    """
    if segundos:
        volta = datetime.now(FUSO_BRASILIA) + timedelta(seconds=segundos)
        quando = (
            f"O limite volta por volta das **{volta:%H:%M}** "
            f"(horário de Brasília), em cerca de {_duracao_legivel(segundos)}."
        )
    elif provedor == "NVIDIA":
        quando = "O limite da NVIDIA é por minuto: tente de novo em cerca de um minuto."
    else:
        quando = (
            "A cota volta à meia-noite no horário do Pacífico — **05:00** em "
            "Brasília."
        )

    if provedor == "NVIDIA":
        explicacao = (
            "O endpoint gratuito da NVIDIA limita as requisições por minuto, e o "
            "limite é compartilhado por todos que usam a mesma chave. "
        )
        titulo = "**O limite de requisições da NVIDIA foi atingido.**"
    else:
        explicacao = (
            "O plano gratuito permite 20 gerações por dia para o projeto inteiro, "
            "e não por pessoa. "
        )
        titulo = "**A cota diária do Gemini acabou.**"

    st.warning(
        f"{titulo}\n\n"
        f"{explicacao}"
        "Isto não é uma falha do NovaMente: o pipeline parou na primeira recusa "
        "da API, de propósito, porque toda tentativa — inclusive a que falha — "
        "consome o saldo.\n\n"
        f"{quando}"
    )

    if not MATERIAIS_PRONTOS:
        return

    st.markdown(
        "Enquanto isso, veja um material **já gerado** por este sistema, "
        "com a auditoria de fidelidade que ele recebeu na execução real:"
    )
    col_escolha, col_botao = st.columns([3, 1])
    with col_escolha:
        escolhido = st.selectbox(
            "Material pronto",
            MATERIAIS_PRONTOS,
            format_func=lambda caminho: caminho.stem.replace("-", " ").capitalize(),
            label_visibility="collapsed",
            key="material_pronto",
        )
    with col_botao:
        abrir = st.button("Abrir material", use_container_width=True)

    if abrir and escolhido is not None:
        try:
            dados = json.loads(escolhido.read_text(encoding="utf-8"))
            st.session_state["resposta"] = RespostaAdaptacao.model_validate(
                dados["resposta"]
            )
            # Sem diagnóstico: estes números vieram de uma execução anterior e
            # exibi-los como se fossem desta sessão seria enganoso.
            st.session_state["diagnostico"] = None
            st.session_state["respostas_quiz"] = {}
            st.session_state["material_e_exemplo"] = escolhido.name
            st.rerun()
        except Exception as exc:  # noqa: BLE001
            st.error(f"Não consegui abrir o material de exemplo: {exc}")


# ---------------------------------------------------------------------------
# Estado
# ---------------------------------------------------------------------------

for chave, inicial in [
    ("resposta", None),
    ("diagnostico", None),
    ("respostas_quiz", {}),
    ("quota_esgotada", None),
]:
    if chave not in st.session_state:
        st.session_state[chave] = inicial


# ---------------------------------------------------------------------------
# Cabeçalho
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="nm-banner">
      <div class="nm-brasao">NM</div>
      <div>
        <div class="nm-instituicao">NovaMente</div>
        <div class="nm-unidade">Núcleo de Adaptação de Conteúdo Educacional</div>
      </div>
      <div class="nm-selo">Hackathon ONE G10
        <span>Oracle Next Education &amp; Alura</span>
      </div>
    </div>
    <div class="nm-regua"></div>
    <div class="nm-trilha">
      Início › Núcleo de Conteúdo Educacional › Gerador de material didático
    </div>
    """,
    unsafe_allow_html=True,
)

cfg = get_settings()

# ---------------------------------------------------------------------------
# Barra lateral
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Parâmetros de adaptação")
    st.caption("Os três eixos definem como o mesmo documento é reescrito.")

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
    if cfg.llm_configurado:
        st.success(f"{cfg.nome_provedor_llm} configurado · `{cfg.modelo_llm_ativo}`")
    else:
        variavel = "NVIDIA_API_KEY" if cfg.provedor_llm == "nvidia" else "GOOGLE_API_KEY"
        st.error(f"{variavel} ausente — defina no arquivo `.env`.")
    st.caption(
        f"Persistência: `{cfg.storage_backend}` · bucket `{cfg.oci_bucket_name}`"
    )
    st.caption(f"Chunk {cfg.chunk_size} / overlap {cfg.chunk_overlap} / top-k {cfg.top_k}")


# ---------------------------------------------------------------------------
# Entrada do documento
# ---------------------------------------------------------------------------

secao(
    "Etapa 1",
    "Documento técnico de entrada",
    "A fonte de toda a geração. O material produzido é ancorado "
    "exclusivamente neste documento.",
)

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

secao(
    "Etapa 2",
    "Geração do material didático",
    "Quatro agentes em sequência: roteiro pedagógico, recuperação de contexto, "
    "redação e auditoria de fidelidade.",
)

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
    st.session_state["quota_esgotada"] = None
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
                st.session_state["material_e_exemplo"] = None
                status.update(label="Pipeline concluído", state="complete")
            except ErroPipeline as exc:
                status.update(label="Falha no pipeline", state="error")
                st.error(str(exc))
            except Exception as exc:  # noqa: BLE001
                if getattr(exc, "cota_esgotada", False):
                    # Não é erro do sistema: é o limite diário da API. O painel
                    # logo abaixo explica e oferece um material já gerado.
                    provedor = getattr(exc, "provedor", "Gemini")
                    status.update(
                        label=f"Limite da API {provedor} atingido", state="error"
                    )
                    st.session_state["quota_esgotada"] = {
                        "segundos": getattr(exc, "segundos", None),
                        "provedor": provedor,
                    }
                else:
                    status.update(label="Erro inesperado", state="error")
                    st.error(f"{type(exc).__name__}: {exc}")


cota_esgotada = st.session_state.get("quota_esgotada")
if cota_esgotada is not None:
    painel_de_cota(cota_esgotada.get("segundos"), cota_esgotada.get("provedor", "Gemini"))


# ---------------------------------------------------------------------------
# Resultado
# ---------------------------------------------------------------------------

resposta = st.session_state.get("resposta")
diag = st.session_state.get("diagnostico")

if resposta is not None:
    secao(
        "Etapa 3",
        "Material gerado",
        "Revise o conteúdo, confira a procedência e exporte no formato de uso.",
    )

    if st.session_state.get("material_e_exemplo"):
        st.info(
            "Este material veio de uma **execução real anterior**, versionada "
            "no repositório em `examples/`. Os números de qualidade abaixo são "
            "os daquela execução; o diagnóstico técnico não se aplica a esta "
            "sessão."
        )

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
        nome_base = (
            resposta.conteudo_adaptado.titulo.replace(" ", "_")[:50] or "novamente"
        )

        st.markdown("#### Apresentação de aula")
        st.caption(
            "Um slide por item, com capa, ficha do material, divisória de conteúdo "
            "e slide de procedência. Abre no PowerPoint, no Google Slides e no Keynote."
        )
        try:
            st.download_button(
                "🎓 Baixar apresentação (.pptx)",
                data=para_pptx(resposta),
                file_name=f"{nome_base}.pptx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "presentationml.presentation"
                ),
                type="primary",
                use_container_width=True,
            )
        except RuntimeError as exc:
            st.warning(f"Apresentação indisponível: {exc}")

        st.markdown("#### Outros formatos")
        coluna_a, coluna_b = st.columns(2)

        with coluna_a:
            try:
                st.download_button(
                    "📄 PDF didático",
                    data=para_pdf(resposta),
                    file_name=f"{nome_base}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except RuntimeError as exc:
                st.caption(f"PDF indisponível: {exc}")
            st.download_button(
                "📝 Markdown",
                data=para_markdown(resposta),
                file_name=f"{nome_base}.md",
                mime="text/markdown",
                use_container_width=True,
            )

        with coluna_b:
            st.download_button(
                "🗂️ CSV para Anki",
                data=para_csv_anki(resposta),
                file_name=f"{nome_base}_anki.csv",
                mime="text/csv",
                use_container_width=True,
            )
            st.download_button(
                "🧾 JSON estruturado",
                data=json.dumps(
                    resposta.model_dump(mode="json"), ensure_ascii=False, indent=2
                ),
                file_name=f"{nome_base}.json",
                mime="application/json",
                use_container_width=True,
            )

        st.divider()
        st.markdown("**Persistência na nuvem**")
        st.json(resposta.armazenamento_oci.model_dump(mode="json"))


# ---------------------------------------------------------------------------
# Rodapé institucional
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="nm-rodape">
      <b>NovaMente</b> · Núcleo de Adaptação de Conteúdo Educacional<br>
      Hackathon ONE G10 — Oracle Next Education &amp; Alura · Grupo 10<br>
      Todo material é gerado a partir do documento enviado e auditado por
      verificação de fidelidade em duas camadas. Revise antes de usar em turma.
    </div>
    """,
    unsafe_allow_html=True,
)
