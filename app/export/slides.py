"""Geração do material didático em PowerPoint (.pptx).

O deck é montado inteiramente por código, sem template externo, com um layout
acadêmico consistente: capa escura, divisórias de seção, um slide por item de
conteúdo e slides de abertura e encerramento.

Regras de composição adotadas:

* Um item pedagógico por slide. Isso elimina listas longas e, com elas, a
  principal causa de texto estourando a caixa.
* O corpo tem o tamanho de fonte calculado a partir da área disponível, com
  piso de 14 pt. Se nem no piso couber, o texto é dividido em um slide de
  continuação em vez de ser cortado.
* O motivo visual repetido é o selo circular numerado, presente em todo slide
  de conteúdo.
"""

from __future__ import annotations

import io
import math
from typing import Any

from app.schemas.content import RespostaAdaptacao

try:  # a dependência é opcional, como a do reportlab
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
    from pptx.dml.color import RGBColor
    from pptx.util import Inches, Pt

    PPTX_DISPONIVEL = True
except ImportError:  # pragma: no cover - ambiente sem python-pptx
    PPTX_DISPONIVEL = False


# ---------------------------------------------------------------------------
# Identidade visual
# ---------------------------------------------------------------------------

TINTA = "16254C"        # azul institucional, cor dominante
TINTA_CLARA = "2E4A86"
OURO = "C08A2E"         # acento
GRAFITE = "1F2733"      # texto corrido
CINZA = "5D6B7E"        # texto secundário
PALHA = "F2F5FA"        # fundo de cartão
BORDA = "DCE3EE"
BRANCO = "FFFFFF"
GELO = "C9D4E8"         # texto sobre fundo escuro
VERDE = "1B6B46"        # resposta correta
VERDE_FUNDO = "E9F3ED"

FONTE_TITULO = "Cambria"
FONTE_CORPO = "Calibri"
FONTE_MONO = "Consolas"

LARGURA = 13.333
ALTURA = 7.5
MARGEM = 0.75
UTIL = LARGURA - 2 * MARGEM

TOPO_TITULO = 1.18
TOPO_CORPO = 2.22
BASE_CORPO = 6.75


# ---------------------------------------------------------------------------
# Utilidades de medida
# ---------------------------------------------------------------------------


def _cor(hexa: str) -> "RGBColor":
    return RGBColor.from_string(hexa)


def _capacidade(largura_in: float, altura_in: float, tamanho: int) -> int:
    """Quantos caracteres cabem, aproximadamente, numa caixa de texto.

    Estimativa deliberadamente conservadora: largura média de caractere de
    0,52 em e entrelinha de 1,26. Serve para escolher o corpo da fonte sem
    precisar renderizar o slide.
    """
    por_linha = max(12, int(largura_in * 72 / (tamanho * 0.52)))
    linhas = max(1, int(altura_in * 72 / (tamanho * 1.26)))
    return por_linha * linhas


def _tamanho_que_cabe(
    texto: str, largura_in: float, altura_in: float, maximo: int, minimo: int
) -> int:
    """Maior corpo de fonte, entre máximo e mínimo, que acomoda o texto."""
    comprimento = len(texto)
    for tamanho in range(maximo, minimo - 1, -1):
        if comprimento <= _capacidade(largura_in, altura_in, tamanho) * 0.90:
            return tamanho
    return minimo


def _altura_texto(
    texto: str, largura_in: float, tamanho: int, entrelinha: float = 1.24
) -> float:
    """Altura aproximada, em polegadas, que o texto ocupa na largura dada."""
    por_linha = max(12, int(largura_in * 72 / (tamanho * 0.52)))
    linhas = 0
    for bloco in [b for b in str(texto).split("\n") if b.strip()] or [""]:
        linhas += max(1, math.ceil(len(bloco) / por_linha))
    return linhas * tamanho * entrelinha * 1.2 / 72


def _dividir(texto: str, largura_in: float, altura_in: float, minimo: int) -> list[str]:
    """Divide o texto em pedaços que caibam na caixa, cortando em frases."""
    limite = int(_capacidade(largura_in, altura_in, minimo) * 0.90)
    if len(texto) <= limite:
        return [texto]

    palavras = texto.split()
    partes: list[str] = []
    atual: list[str] = []
    tamanho_atual = 0
    for palavra in palavras:
        if tamanho_atual + len(palavra) + 1 > limite and atual:
            partes.append(" ".join(atual))
            atual, tamanho_atual = [], 0
        atual.append(palavra)
        tamanho_atual += len(palavra) + 1
    if atual:
        partes.append(" ".join(atual))
    return partes


def _topo_para(titulo: str) -> float:
    """Onde o conteúdo começa, dado o número de linhas que o título ocupa."""
    largura = UTIL - 0.75
    tamanho = _tamanho_que_cabe(titulo, largura, 1.3, 28, 18)
    altura = _altura_texto(titulo, largura, tamanho, 1.12)
    return max(TOPO_CORPO, TOPO_TITULO - 0.26 + altura + 0.46)


def _altura_cartao(texto: str, largura_in: float, tam: int = 13) -> float:
    """Altura de um cartão com rótulo em caixa alta mais um parágrafo."""
    return 0.32 + _altura_texto(texto, largura_in - 0.6, tam, 1.18) + 0.32


def _encurtar(texto: str, limite: int) -> str:
    texto = " ".join(str(texto).split())
    if len(texto) <= limite:
        return texto
    return texto[: limite - 1].rstrip() + "…"


# ---------------------------------------------------------------------------
# Primitivas de desenho
# ---------------------------------------------------------------------------


def _texto(
    slide: Any,
    conteudo: str,
    x: float,
    y: float,
    cx: float,
    cy: float,
    *,
    tam: int,
    cor: str,
    fonte: str = FONTE_CORPO,
    negrito: bool = False,
    italico: bool = False,
    align: Any = None,
    entrelinha: float = 1.24,
    espaco: int = 8,
    caixa_alta: bool = False,
    espaco_letras: int | None = None,
    ancora: Any = None,
) -> Any:
    forma = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(cx), Inches(cy))
    quadro = forma.text_frame
    quadro.word_wrap = True
    quadro.auto_size = MSO_AUTO_SIZE.NONE
    quadro.margin_left = quadro.margin_right = 0
    quadro.margin_top = quadro.margin_bottom = 0
    if ancora is not None:
        quadro.vertical_anchor = ancora

    blocos = [b for b in str(conteudo).split("\n") if b.strip()] or [""]
    for indice, bloco in enumerate(blocos):
        paragrafo = quadro.paragraphs[0] if indice == 0 else quadro.add_paragraph()
        paragrafo.alignment = align or PP_ALIGN.LEFT
        paragrafo.line_spacing = entrelinha
        paragrafo.space_after = Pt(espaco)
        trecho = paragrafo.add_run()
        trecho.text = bloco.upper() if caixa_alta else bloco
        fonte_run = trecho.font
        fonte_run.name = fonte
        fonte_run.size = Pt(tam)
        fonte_run.bold = negrito
        fonte_run.italic = italico
        fonte_run.color.rgb = _cor(cor)
        if espaco_letras:
            # charSpacing não é exposto pela API; gravamos direto no rPr.
            trecho.font._rPr.set("spc", str(espaco_letras))
    return forma


def _cartao(
    slide: Any,
    x: float,
    y: float,
    cx: float,
    cy: float,
    *,
    fundo: str = PALHA,
    borda: str | None = BORDA,
    raio: float = 0.035,
) -> Any:
    forma = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(cx), Inches(cy)
    )
    forma.adjustments[0] = raio
    forma.fill.solid()
    forma.fill.fore_color.rgb = _cor(fundo)
    if borda:
        forma.line.color.rgb = _cor(borda)
        forma.line.width = Pt(0.75)
    else:
        forma.line.fill.background()
    forma.shadow.inherit = False
    forma.text_frame.text = ""
    return forma


def _selo(
    slide: Any,
    rotulo: str,
    x: float,
    y: float,
    diametro: float = 0.52,
    *,
    fundo: str = TINTA,
    tinta: str = BRANCO,
    tam: int = 15,
) -> Any:
    """Selo circular numerado — o motivo visual do deck."""
    forma = slide.shapes.add_shape(
        MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(diametro), Inches(diametro)
    )
    forma.fill.solid()
    forma.fill.fore_color.rgb = _cor(fundo)
    forma.line.fill.background()
    forma.shadow.inherit = False

    quadro = forma.text_frame
    quadro.word_wrap = False
    quadro.margin_left = quadro.margin_right = 0
    quadro.margin_top = quadro.margin_bottom = 0
    quadro.vertical_anchor = MSO_ANCHOR.MIDDLE
    paragrafo = quadro.paragraphs[0]
    paragrafo.alignment = PP_ALIGN.CENTER
    trecho = paragrafo.add_run()
    trecho.text = str(rotulo)
    trecho.font.name = FONTE_TITULO
    trecho.font.size = Pt(tam)
    trecho.font.bold = True
    trecho.font.color.rgb = _cor(tinta)
    return forma


# ---------------------------------------------------------------------------
# Montagem do deck
# ---------------------------------------------------------------------------


class _Deck:
    """Acumula os slides e cuida de numeração e rodapé."""

    def __init__(self, rodape: str) -> None:
        self.prs = Presentation()
        self.prs.slide_width = Inches(LARGURA)
        self.prs.slide_height = Inches(ALTURA)
        self.rodape = _encurtar(rodape, 68)
        self.numero = 0

    # -- infraestrutura ---------------------------------------------------

    def _novo(self, escuro: bool = False) -> Any:
        slide = self.prs.slides.add_slide(self.prs.slide_layouts[6])
        fundo = slide.background.fill
        fundo.solid()
        fundo.fore_color.rgb = _cor(TINTA if escuro else BRANCO)
        return slide

    def _rodape(self, slide: Any) -> None:
        self.numero += 1
        _texto(
            slide,
            self.rodape,
            MARGEM,
            6.98,
            UTIL - 1.0,
            0.3,
            tam=9,
            cor=CINZA,
            espaco=0,
        )
        _texto(
            slide,
            str(self.numero),
            LARGURA - MARGEM - 0.6,
            6.98,
            0.6,
            0.3,
            tam=9,
            cor=CINZA,
            align=PP_ALIGN.RIGHT,
            espaco=0,
        )

    def _cabecalho(self, slide: Any, etiqueta: str, titulo: str, selo: str) -> float:
        """Selo + etiqueta + título. Devolve o y em que o conteúdo pode começar."""
        largura = UTIL - 0.75
        _selo(slide, selo, MARGEM, 0.52)
        _texto(
            slide,
            etiqueta,
            MARGEM + 0.75,
            0.58,
            largura,
            0.3,
            tam=10,
            cor=OURO,
            negrito=True,
            caixa_alta=True,
            espaco_letras=140,
            espaco=0,
        )
        tamanho = _tamanho_que_cabe(titulo, largura, 1.3, 28, 18)
        altura = _altura_texto(titulo, largura, tamanho, 1.12)
        _texto(
            slide,
            titulo,
            MARGEM + 0.75,
            TOPO_TITULO - 0.26,
            largura,
            max(0.5, altura),
            tam=tamanho,
            cor=TINTA,
            fonte=FONTE_TITULO,
            negrito=True,
            entrelinha=1.12,
            espaco=0,
        )
        return _topo_para(titulo)

    def _notas(self, slide: Any, texto: str) -> None:
        if texto.strip():
            slide.notes_slide.notes_text_frame.text = texto.strip()

    # -- slides de conteúdo ----------------------------------------------

    def capa(self, titulo: str, subtitulo: str, rodape: str) -> None:
        slide = self._novo(escuro=True)
        _selo(slide, "NM", MARGEM, 0.85, 1.0, fundo=OURO, tinta=TINTA, tam=26)
        _texto(
            slide,
            "NovaMente · Material didático adaptado",
            MARGEM,
            2.45,
            UTIL,
            0.32,
            tam=12,
            cor=OURO,
            negrito=True,
            caixa_alta=True,
            espaco_letras=180,
            espaco=0,
        )
        tamanho = _tamanho_que_cabe(titulo, UTIL - 1.2, 2.1, 42, 26)
        _texto(
            slide,
            titulo,
            MARGEM,
            2.95,
            UTIL - 1.2,
            2.2,
            tam=tamanho,
            cor=BRANCO,
            fonte=FONTE_TITULO,
            negrito=True,
            entrelinha=1.1,
            espaco=0,
        )
        _texto(
            slide, subtitulo, MARGEM, 5.42, UTIL - 1.2, 0.5, tam=15, cor=GELO, espaco=0
        )
        _texto(
            slide, rodape, MARGEM, 6.62, UTIL, 0.35, tam=11, cor=GELO, espaco=0
        )
        self.numero += 1

    def divisoria(self, etiqueta: str, titulo: str, apoio: str) -> None:
        slide = self._novo(escuro=True)
        _texto(
            slide,
            etiqueta,
            MARGEM,
            2.85,
            UTIL,
            0.32,
            tam=11,
            cor=OURO,
            negrito=True,
            caixa_alta=True,
            espaco_letras=180,
            espaco=0,
        )
        _texto(
            slide,
            titulo,
            MARGEM,
            3.3,
            UTIL - 1.5,
            1.3,
            tam=36,
            cor=BRANCO,
            fonte=FONTE_TITULO,
            negrito=True,
            entrelinha=1.1,
            espaco=0,
        )
        _texto(slide, apoio, MARGEM, 4.62, UTIL - 1.5, 0.5, tam=14, cor=GELO, espaco=0)
        self.numero += 1

    def ficha(self, introducao: str, estatisticas: list[tuple[str, str]]) -> None:
        slide = self._novo()
        topo = self._cabecalho(slide, "Abertura", "Sobre este material", "i")

        largura_texto = 7.0
        altura_bloco = len(estatisticas) * 1.45 - 0.19
        tamanho = _tamanho_que_cabe(introducao, largura_texto, altura_bloco, 17, 14)
        _texto(
            slide,
            introducao,
            MARGEM,
            topo,
            largura_texto,
            altura_bloco,
            tam=tamanho,
            cor=GRAFITE,
            ancora=MSO_ANCHOR.MIDDLE,
        )

        x_cartao = MARGEM + largura_texto + 0.6
        largura_cartao = LARGURA - MARGEM - x_cartao
        y = topo
        for valor, rotulo in estatisticas:
            _cartao(slide, x_cartao, y, largura_cartao, 1.26)
            _texto(
                slide,
                valor,
                x_cartao + 0.3,
                y + 0.16,
                largura_cartao - 0.6,
                0.68,
                tam=30,
                cor=TINTA,
                fonte=FONTE_TITULO,
                negrito=True,
                espaco=0,
            )
            _texto(
                slide,
                rotulo,
                x_cartao + 0.3,
                y + 0.86,
                largura_cartao - 0.6,
                0.3,
                tam=10,
                cor=CINZA,
                caixa_alta=True,
                espaco_letras=100,
                espaco=0,
            )
            y += 1.45
        self._rodape(slide)

    def listas(self, conceitos: list[str], pre_requisitos: list[str]) -> None:
        """Conceitos-chave e pré-requisitos lado a lado."""
        slide = self._novo()
        topo = self._cabecalho(slide, "Antes de começar", "Mapa do conteúdo", "ii")

        colunas = [
            ("Conceitos-chave", conceitos, TINTA),
            ("Pré-requisitos", pre_requisitos, OURO),
        ]
        largura_coluna = (UTIL - 0.8) / 2
        for indice, (rotulo, itens, cor_selo) in enumerate(colunas):
            if not itens:
                continue
            x = MARGEM + indice * (largura_coluna + 0.8)
            _texto(
                slide,
                rotulo,
                x,
                topo,
                largura_coluna,
                0.34,
                tam=11,
                cor=CINZA,
                negrito=True,
                caixa_alta=True,
                espaco_letras=120,
                espaco=0,
            )
            y = topo + 0.52
            for posicao, item in enumerate(itens[:6], start=1):
                altura = 0.72
                _cartao(slide, x, y, largura_coluna, altura)
                _selo(
                    slide,
                    str(posicao),
                    x + 0.22,
                    y + 0.16,
                    0.4,
                    fundo=cor_selo,
                    tam=12,
                )
                _texto(
                    slide,
                    _encurtar(item, 110),
                    x + 0.78,
                    y + 0.17,
                    largura_coluna - 1.0,
                    0.44,
                    tam=13,
                    cor=GRAFITE,
                    entrelinha=1.12,
                    espaco=0,
                    ancora=MSO_ANCHOR.MIDDLE,
                )
                y += altura + 0.16
        self._rodape(slide)

    def item(
        self,
        etiqueta: str,
        titulo: str,
        corpo: str,
        selo: str,
        *,
        rotulo_corpo: str | None = None,
        destaque: tuple[str, str] | None = None,
        bloco_codigo: str | None = None,
        notas: str = "",
    ) -> None:
        """Slide padrão de um item pedagógico, com continuação se necessário."""
        topo = _topo_para(titulo)
        altura_rotulo = 0.42 if rotulo_corpo else 0.0
        altura_codigo = 1.32 if bloco_codigo else 0.0
        altura_destaque = (
            _altura_cartao(destaque[1], UTIL) + 0.3 if destaque else 0.0
        )

        disponivel = max(
            1.0, BASE_CORPO - topo - altura_rotulo - altura_codigo - altura_destaque
        )
        partes = _dividir(corpo, UTIL, disponivel, 14)

        for indice, parte in enumerate(partes):
            slide = self._novo()
            sufixo = "" if indice == 0 else " (continuação)"
            self._cabecalho(slide, etiqueta + sufixo, titulo, selo)

            y = topo
            if rotulo_corpo:
                _texto(
                    slide, rotulo_corpo, MARGEM, y, UTIL, 0.3,
                    tam=10, cor=CINZA, negrito=True, caixa_alta=True,
                    espaco_letras=120, espaco=0,
                )
                y += altura_rotulo

            tamanho = _tamanho_que_cabe(parte, UTIL, disponivel, 18, 14)
            altura_real = min(disponivel, _altura_texto(parte, UTIL, tamanho))
            _texto(
                slide, parte, MARGEM, y, UTIL, altura_real, tam=tamanho, cor=GRAFITE
            )
            y += altura_real + 0.42

            ultimo = indice == len(partes) - 1
            if ultimo:
                # os blocos auxiliares nunca ultrapassam a área útil
                y = min(y, BASE_CORPO - altura_codigo - altura_destaque)

                if bloco_codigo:
                    _cartao(slide, MARGEM, y, UTIL, 1.02, fundo=TINTA, borda=None)
                    _texto(
                        slide, "Comando", MARGEM + 0.3, y + 0.16, UTIL - 0.6, 0.26,
                        tam=9, cor=OURO, negrito=True, caixa_alta=True,
                        espaco_letras=120, espaco=0,
                    )
                    _texto(
                        slide, _encurtar(bloco_codigo, 190), MARGEM + 0.3, y + 0.48,
                        UTIL - 0.6, 0.44, tam=13, cor=BRANCO, fonte=FONTE_MONO,
                        espaco=0,
                    )
                    y += altura_codigo

                if destaque:
                    rotulo, conteudo = destaque
                    altura = _altura_cartao(conteudo, UTIL)
                    _cartao(slide, MARGEM, y, UTIL, altura)
                    _texto(
                        slide, rotulo, MARGEM + 0.3, y + 0.18, UTIL - 0.6, 0.26,
                        tam=9, cor=OURO, negrito=True, caixa_alta=True,
                        espaco_letras=120, espaco=0,
                    )
                    _texto(
                        slide, conteudo, MARGEM + 0.3, y + 0.5, UTIL - 0.6,
                        altura - 0.68, tam=13, cor=GRAFITE, entrelinha=1.18, espaco=0,
                    )

                self._notas(slide, notas)
            self._rodape(slide)

    def questao(
        self, numero: int, total: int, pergunta: str, opcoes: list[str], correta: int
    ) -> None:
        slide = self._novo()
        topo = self._cabecalho(
            slide, f"Questão {numero} de {total}", pergunta, str(numero)
        )

        y = topo
        altura_linha = min(0.74, (BASE_CORPO - y - 0.2) / max(1, len(opcoes)))
        for indice, opcao in enumerate(opcoes):
            _cartao(slide, MARGEM, y, UTIL, altura_linha)
            _selo(
                slide,
                chr(65 + indice),
                MARGEM + 0.22,
                y + (altura_linha - 0.4) / 2,
                0.4,
                fundo=TINTA_CLARA,
                tam=12,
            )
            _texto(
                slide,
                _encurtar(opcao, 150),
                MARGEM + 0.8,
                y + 0.1,
                UTIL - 1.1,
                altura_linha - 0.2,
                tam=14,
                cor=GRAFITE,
                entrelinha=1.14,
                espaco=0,
                ancora=MSO_ANCHOR.MIDDLE,
            )
            y += altura_linha + 0.12

        self._notas(
            slide,
            f"Resposta correta: {chr(65 + correta)}) {opcoes[correta]}",
        )
        self._rodape(slide)

    def resposta(
        self, numero: int, correta: str, letra: str, justificativa: str
    ) -> None:
        slide = self._novo()
        topo = self._cabecalho(
            slide, f"Questão {numero} · gabarito", "Resposta comentada", "✓"
        )

        _cartao(slide, MARGEM, topo, UTIL, 1.2, fundo=VERDE_FUNDO, borda=None)
        _selo(slide, letra, MARGEM + 0.28, topo + 0.34, 0.5, fundo=VERDE, tam=14)
        _texto(
            slide,
            _encurtar(correta, 180),
            MARGEM + 0.95,
            topo + 0.26,
            UTIL - 1.3,
            0.7,
            tam=16,
            cor=VERDE,
            negrito=True,
            entrelinha=1.16,
            espaco=0,
            ancora=MSO_ANCHOR.MIDDLE,
        )

        y = topo + 1.5
        _texto(
            slide,
            "Por que esta é a resposta",
            MARGEM,
            y,
            UTIL,
            0.3,
            tam=10,
            cor=CINZA,
            negrito=True,
            caixa_alta=True,
            espaco_letras=120,
            espaco=0,
        )
        altura = BASE_CORPO - y - 0.5
        tamanho = _tamanho_que_cabe(justificativa, UTIL, altura, 17, 14)
        _texto(
            slide,
            justificativa,
            MARGEM,
            y + 0.42,
            UTIL,
            altura,
            tam=tamanho,
            cor=GRAFITE,
        )
        self._rodape(slide)

    def qualidade(
        self, estatisticas: list[tuple[str, str]], observacoes: str, fonte: str
    ) -> None:
        slide = self._novo()
        topo = self._cabecalho(
            slide, "Procedência", "Qualidade e rastreabilidade", "✓"
        )

        largura_cartao = (UTIL - 2 * 0.4) / 3
        for indice, (valor, rotulo) in enumerate(estatisticas[:3]):
            x = MARGEM + indice * (largura_cartao + 0.4)
            _cartao(slide, x, topo, largura_cartao, 1.5)
            _texto(
                slide, valor, x + 0.34, topo + 0.26, largura_cartao - 0.68, 0.8,
                tam=34, cor=TINTA, fonte=FONTE_TITULO, negrito=True, espaco=0,
            )
            _texto(
                slide, rotulo, x + 0.34, topo + 1.06, largura_cartao - 0.68, 0.3,
                tam=10, cor=CINZA, caixa_alta=True, espaco_letras=100, espaco=0,
            )

        y = topo + 1.85
        _texto(
            slide, "Auditoria de fidelidade", MARGEM, y, UTIL, 0.3,
            tam=10, cor=CINZA, negrito=True, caixa_alta=True,
            espaco_letras=120, espaco=0,
        )
        altura = BASE_CORPO - y - 1.0
        corpo = observacoes.strip() or "Sem observações registradas pelo agente crítico."
        tamanho = _tamanho_que_cabe(corpo, UTIL, altura, 16, 13)
        corpo = _encurtar(corpo, int(_capacidade(UTIL, altura, tamanho) * 0.9))
        _texto(slide, corpo, MARGEM, y + 0.4, UTIL, altura, tam=tamanho, cor=GRAFITE)

        _texto(
            slide,
            f"Documento-fonte: {_encurtar(fonte, 90)}",
            MARGEM,
            BASE_CORPO - 0.42,
            UTIL,
            0.32,
            tam=11,
            cor=CINZA,
            italico=True,
            espaco=0,
        )
        self._rodape(slide)

    def encerramento(self, titulo: str, linhas: list[str]) -> None:
        slide = self._novo(escuro=True)
        _texto(
            slide,
            titulo,
            MARGEM,
            2.9,
            UTIL - 1.5,
            1.1,
            tam=34,
            cor=BRANCO,
            fonte=FONTE_TITULO,
            negrito=True,
            entrelinha=1.12,
            espaco=0,
        )
        _texto(
            slide,
            "\n".join(linhas),
            MARGEM,
            4.15,
            UTIL - 1.5,
            1.8,
            tam=14,
            cor=GELO,
            espaco=10,
        )
        self.numero += 1

    def bytes(self) -> bytes:
        buffer = io.BytesIO()
        self.prs.save(buffer)
        return buffer.getvalue()


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------


def para_pptx(resposta: RespostaAdaptacao) -> bytes:
    """Apresentação .pptx do material didático. Requer python-pptx."""
    if not PPTX_DISPONIVEL:  # pragma: no cover - ambiente sem a dependência
        raise RuntimeError(
            "python-pptx não instalado. Rode: pip install -r requirements.txt"
        )

    conteudo = resposta.conteudo_adaptado
    meta = resposta.metadados
    avaliacao = resposta.avaliacao_qualidade

    deck = _Deck(conteudo.titulo)

    deck.capa(
        conteudo.titulo,
        f"{meta.formato_gerado} · {meta.perfil_aplicado} · "
        f"{meta.tempo_estimado_estudo_minutos} min de estudo",
        "NovaMente — Hackathon ONE G10 · Oracle Next Education & Alura",
    )

    deck.ficha(
        conteudo.introducao_contextualizada,
        [
            (f"{meta.tempo_estimado_estudo_minutos} min", "Tempo de estudo"),
            (str(len(conteudo.itens)), "Itens no material"),
            (f"{avaliacao.ancoragem_fonte_score:.2f}", "Ancoragem na fonte"),
        ],
    )

    if meta.conceitos_chave or meta.pre_requisitos:
        deck.listas(meta.conceitos_chave, meta.pre_requisitos)

    deck.divisoria(
        "Conteúdo",
        meta.formato_gerado,
        f"{len(conteudo.itens)} itens adaptados para o perfil {meta.perfil_aplicado}",
    )

    total = len(conteudo.itens)
    numero_questao = 0

    for posicao, item in enumerate(conteudo.itens, start=1):
        dados: dict[str, Any] = item.model_dump()

        if "frente" in dados:
            destaque = (
                ("Dica didática", dados["dica_didatica"])
                if dados.get("dica_didatica")
                else None
            )
            deck.item(
                f"Flashcard {posicao} de {total}",
                dados["frente"],
                dados["verso"],
                str(posicao),
                rotulo_corpo="Resposta",
                destaque=destaque,
                notas=f"Frente: {dados['frente']}",
            )

        elif "pergunta" in dados:
            numero_questao += 1
            correta = int(dados["indice_resposta_correta"])
            deck.questao(
                numero_questao,
                total,
                dados["pergunta"],
                list(dados["opcoes"]),
                correta,
            )
            deck.resposta(
                numero_questao,
                dados["opcoes"][correta],
                chr(65 + correta),
                dados["justificativa"],
            )

        elif "passo" in dados:
            deck.item(
                f"Passo {dados['passo']} de {total}",
                dados["titulo"],
                dados["conteudo"],
                str(dados["passo"]),
                bloco_codigo=dados.get("comando") or None,
            )

        elif "topico" in dados:
            destaque = (
                ("Impacto no negócio", dados["impacto_negocio"])
                if dados.get("impacto_negocio")
                else None
            )
            deck.item(
                f"Tópico {posicao} de {total}",
                dados["topico"],
                dados["descricao"],
                str(posicao),
                destaque=destaque,
            )

        elif "bloco" in dados:
            destaque = (
                ("Recurso visual", dados["recurso_visual"])
                if dados.get("recurso_visual")
                else None
            )
            deck.item(
                f"Bloco {posicao} · {dados['tempo_estimado_min']} min",
                dados["bloco"],
                dados["fala"],
                str(posicao),
                rotulo_corpo="Fala do apresentador",
                destaque=destaque,
                notas=f"Tempo previsto: {dados['tempo_estimado_min']} minutos.",
            )

    deck.qualidade(
        [
            (f"{avaliacao.ancoragem_fonte_score:.2f}", "Ancoragem na fonte"),
            (avaliacao.clareza_pedagogica, "Clareza pedagógica"),
            (str(len(conteudo.itens)), "Itens auditados"),
        ],
        avaliacao.observacoes,
        conteudo.titulo,
    )

    deck.encerramento(
        "Material gerado pelo NovaMente",
        [
            "Pipeline RAG com verificação de fidelidade em duas camadas: "
            "auditoria do modelo e checagem léxica determinística.",
            "Todo o conteúdo é ancorado no documento-fonte. "
            "Revise antes de publicar para turmas.",
            "github.com/INASIOCS/Nova_Mente — Hackathon ONE G10",
        ],
    )

    return deck.bytes()
