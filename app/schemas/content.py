"""Contrato de dados do NovaMente.

Os nomes de campo seguem **exatamente** o briefing do Hackathon ONE G10
(exemplo de requisição e de resposta estruturada). Não renomeie campos:
a avaliação do hackathon confere o formato.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ---------------------------------------------------------------------------
# Enumerações dos eixos de parametrização
# ---------------------------------------------------------------------------


class PerfilDestinatario(str, Enum):
    INICIANTE = "Iniciante"
    TRANSICAO_CARREIRA = "Transição de Carreira"
    DEV_JUNIOR_PLENO = "Desenvolvedor Júnior / Pleno"
    LIDER_TECNICO = "Líder Técnico / Arquiteto"
    GESTOR_EXECUTIVO = "Gestor / Executivo (Não Técnico)"


class FormatoSaida(str, Enum):
    TUTORIAL = "Tutorial"
    FLASHCARDS = "Flashcards"
    QUIZ = "Quiz"
    RESUMO_EXECUTIVO = "Resumo Executivo"
    ROTEIRO_AULA = "Roteiro de Aula"


class NichoSetor(str, Enum):
    FINTECH = "Fintech"
    SAUDE = "Saúde"
    ECOMMERCE = "E-commerce"
    GERAL = "Geral"


class NivelDetalhe(str, Enum):
    DIDATICO = "Didatico"
    INTERMEDIARIO = "Intermediario"
    APROFUNDADO = "Aprofundado"


# ---------------------------------------------------------------------------
# Entrada
# ---------------------------------------------------------------------------


class RequisicaoAdaptacao(BaseModel):
    """Payload de entrada do endpoint principal de adaptação."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    documento_titulo: str = Field(min_length=3, max_length=300)
    documento_conteudo: str = Field(
        min_length=50,
        description="Texto técnico bruto. Para upload de arquivo, use /adaptar/upload.",
    )
    perfil_destinatario: PerfilDestinatario
    formato_saida: FormatoSaida
    nicho_setor: NichoSetor = NichoSetor.GERAL
    nivel_detalhe: NivelDetalhe = NivelDetalhe.DIDATICO

    @field_validator("documento_conteudo")
    @classmethod
    def _sem_conteudo_vazio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("documento_conteudo não pode ser apenas espaços em branco.")
        return v


# ---------------------------------------------------------------------------
# Itens de conteúdo — um modelo por formato pedagógico
# ---------------------------------------------------------------------------


class ItemFlashcard(BaseModel):
    """Flashcard de memorização."""

    model_config = ConfigDict(extra="ignore")
    frente: str
    verso: str
    dica_didatica: str = ""


class ItemQuiz(BaseModel):
    """Questão de múltipla escolha com justificativa."""

    model_config = ConfigDict(extra="ignore")
    pergunta: str
    opcoes: list[str] = Field(min_length=2, max_length=6)
    indice_resposta_correta: int = Field(ge=0)
    justificativa: str

    @field_validator("indice_resposta_correta")
    @classmethod
    def _indice_valido(cls, v: int, info) -> int:
        opcoes = info.data.get("opcoes") or []
        if opcoes and v >= len(opcoes):
            raise ValueError(
                f"indice_resposta_correta={v} fora do intervalo de {len(opcoes)} opções."
            )
        return v


class ItemTutorial(BaseModel):
    """Passo de um guia prático."""

    model_config = ConfigDict(extra="ignore")
    passo: int = Field(ge=1)
    titulo: str
    conteudo: str
    comando: str | None = None


class ItemResumo(BaseModel):
    """Bloco de um resumo executivo (TL;DR)."""

    model_config = ConfigDict(extra="ignore")
    topico: str
    descricao: str
    impacto_negocio: str = ""


class ItemRoteiro(BaseModel):
    """Bloco de um roteiro de aula / vídeo."""

    model_config = ConfigDict(extra="ignore")
    bloco: str
    tempo_estimado_min: int = Field(ge=0)
    fala: str
    recurso_visual: str = ""


ItemConteudo = Annotated[
    ItemFlashcard | ItemQuiz | ItemTutorial | ItemResumo | ItemRoteiro,
    Field(union_mode="smart"),
]

MODELO_POR_FORMATO: dict[str, type[BaseModel]] = {
    FormatoSaida.FLASHCARDS.value: ItemFlashcard,
    FormatoSaida.QUIZ.value: ItemQuiz,
    FormatoSaida.TUTORIAL.value: ItemTutorial,
    FormatoSaida.RESUMO_EXECUTIVO.value: ItemResumo,
    FormatoSaida.ROTEIRO_AULA.value: ItemRoteiro,
}


# ---------------------------------------------------------------------------
# Saída
# ---------------------------------------------------------------------------


class MetadadosAprendizado(BaseModel):
    """Metadados pedagógicos gerados pelo sistema."""

    model_config = ConfigDict(extra="ignore")

    perfil_aplicado: str
    formato_gerado: str
    tempo_estimado_estudo_minutos: int = Field(ge=1, le=600)
    conceitos_chave: list[str] = Field(default_factory=list)
    pre_requisitos: list[str] = Field(default_factory=list)


class ConteudoAdaptado(BaseModel):
    """Pacote didático propriamente dito."""

    model_config = ConfigDict(extra="ignore")

    titulo: str
    introducao_contextualizada: str
    itens: list[ItemConteudo] = Field(min_length=1)


class AvaliacaoQualidade(BaseModel):
    """Resultado do agente crítico / verificação de fidelidade."""

    model_config = ConfigDict(extra="ignore")

    ancoragem_fonte_score: float = Field(ge=0.0, le=1.0)
    clareza_pedagogica: Literal["Alta", "Média", "Baixa"]
    observacoes: str = ""


class ArmazenamentoOCI(BaseModel):
    """Rastro da persistência no OCI Object Storage (ou no fallback local)."""

    model_config = ConfigDict(extra="ignore")

    bucket: str
    objeto_id: str
    status_upload: Literal["concluido", "falhou", "pendente", "local"]
    backend: str = "oci"
    uri: str | None = None


class RespostaAdaptacao(BaseModel):
    """Resposta completa do endpoint principal."""

    model_config = ConfigDict(extra="ignore")

    status: Literal["sucesso", "erro"] = "sucesso"
    metadados: MetadadosAprendizado
    conteudo_adaptado: ConteudoAdaptado
    avaliacao_qualidade: AvaliacaoQualidade
    armazenamento_oci: ArmazenamentoOCI


class RespostaErro(BaseModel):
    """Resposta de erro amigável."""

    status: Literal["erro"] = "erro"
    mensagem: str
    detalhe: str | None = None


# ---------------------------------------------------------------------------
# Validação auxiliar
# ---------------------------------------------------------------------------


def validar_itens_do_formato(formato: str, itens: list[Any]) -> list[BaseModel]:
    """Revalida os itens contra o modelo estrito do formato pedido.

    A união 'smart' do Pydantic já escolhe o modelo certo na maioria dos casos;
    esta função garante tipagem estrita quando o formato é conhecido.
    """
    modelo = MODELO_POR_FORMATO.get(formato)
    if modelo is None:
        return itens
    validados: list[BaseModel] = []
    for item in itens:
        dados = item if isinstance(item, dict) else item.model_dump()
        validados.append(modelo.model_validate(dados))
    return validados
