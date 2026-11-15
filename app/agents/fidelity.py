"""Verificação determinística de fidelidade à fonte (anti-alucinação).

Complementa o Agente Crítico (que é baseado em LLM) com checagens léxicas que
não dependem do modelo e portanto não podem ser "convencidas" por ele:

1. Cobertura de termos técnicos: quanto do vocabulário técnico do material
   gerado existe de fato no documento de origem.
2. Números órfãos: valores numéricos citados no material que não aparecem na
   fonte — a forma mais comum e mais perigosa de alucinação técnica.
3. Identificadores órfãos: comandos, nomes de serviço e siglas inexistentes
   na fonte.

O score final combina o veredito do LLM com estes sinais objetivos.
"""

from __future__ import annotations


import re
from dataclasses import dataclass, field

# Palavras muito comuns não contam como "termo técnico"
_STOPWORDS = {
    "a", "o", "as", "os", "um", "uma", "de", "do", "da", "dos", "das", "e", "ou",
    "que", "para", "com", "sem", "por", "no", "na", "nos", "nas", "em", "ao", "aos",
    "se", "ser", "sua", "seu", "suas", "seus", "como", "mais", "mas", "the", "of",
    "and", "to", "in", "is", "it", "você", "voce", "ele", "ela", "isso", "esse",
    "essa", "este", "esta", "pode", "deve", "cada", "quando", "onde", "qual",
    "quais", "sobre", "entre", "pelo", "pela", "tem", "são", "sao", "foi", "já",
    "ja", "também", "tambem", "muito", "todo", "toda", "todos", "todas", "não",
    "nao", "sim", "porque", "assim", "antes", "depois", "até", "ate", "dentro",
    "fora", "aqui", "lá", "la", "nele", "nela", "numa", "num", "pensa", "pense",
    "imagine", "exemplo", "forma", "parte", "caso", "vez", "modo", "nível", "nivel",
}

_TERMO_RE = re.compile(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9_\-]{2,}")
_NUMERO_RE = re.compile(r"\b\d+(?:[.,]\d+)?\b")
_IDENT_RE = re.compile(r"\b(?:[A-Z]{2,}|[a-z]+(?:[-_][a-z]+)+|[a-z]+\.[a-z]+)\b")


@dataclass
class RelatorioFidelidade:
    cobertura_termos: float
    numeros_orfaos: list[str] = field(default_factory=list)
    identificadores_orfaos: list[str] = field(default_factory=list)
    total_termos_avaliados: int = 0

    @property
    def score_lexico(self) -> float:
        """Score objetivo de ancoragem, de 0.0 a 1.0."""
        score = self.cobertura_termos
        # cada número inventado é uma falha grave
        score -= 0.08 * len(self.numeros_orfaos)
        # identificadores inventados são graves, mas um pouco menos
        score -= 0.04 * len(self.identificadores_orfaos)
        return round(max(0.0, min(1.0, score)), 4)

    @property
    def tem_suspeita(self) -> bool:
        return bool(self.numeros_orfaos or self.identificadores_orfaos)

    def resumo(self) -> str:
        partes = [f"cobertura léxica de {self.cobertura_termos:.0%}"]
        if self.numeros_orfaos:
            partes.append(
                f"{len(self.numeros_orfaos)} número(s) sem respaldo na fonte "
                f"({', '.join(self.numeros_orfaos[:5])})"
            )
        if self.identificadores_orfaos:
            partes.append(
                f"{len(self.identificadores_orfaos)} identificador(es) sem respaldo "
                f"({', '.join(self.identificadores_orfaos[:5])})"
            )
        return "; ".join(partes)


def _normalizar(texto: str) -> str:
    return texto.lower()


def _termos(texto: str) -> set[str]:
    return {
        t.lower()
        for t in _TERMO_RE.findall(texto)
        if t.lower() not in _STOPWORDS and len(t) > 3
    }


def _texto_de(material: object) -> str:
    """Achata o material gerado em um único texto para auditoria.

    Coleta apenas os VALORES textuais da estrutura. As chaves do JSON
    ("titulo", "frente", "verso", ...) são vocabulário do nosso próprio schema,
    não conteúdo gerado — contá-las distorceria a métrica de cobertura.
    """
    partes: list[str] = []

    def caminhar(no: object) -> None:
        if isinstance(no, dict):
            for valor in no.values():
                caminhar(valor)
        elif isinstance(no, (list, tuple)):
            for valor in no:
                caminhar(valor)
        elif isinstance(no, str):
            partes.append(no)
        elif isinstance(no, (int, float)) and not isinstance(no, bool):
            partes.append(str(no))

    caminhar(material)
    return " ".join(partes)


def verificar_fidelidade(material: dict, contexto_fonte: str) -> RelatorioFidelidade:
    """Compara o material gerado com o contexto de origem."""
    gerado = _texto_de(material)
    fonte_norm = _normalizar(contexto_fonte)
    termos_fonte = _termos(contexto_fonte)

    termos_gerados = _termos(gerado)
    if termos_gerados:
        ancorados = sum(
            1
            for t in termos_gerados
            if t in termos_fonte or t in fonte_norm
        )
        cobertura = ancorados / len(termos_gerados)
    else:
        cobertura = 0.0

    # Números citados no material que não existem na fonte.
    # Ignora números pequenos (1-12), usados como ordinais/contagem didática.
    numeros_fonte = set(_NUMERO_RE.findall(contexto_fonte))
    numeros_orfaos = []
    for n in dict.fromkeys(_NUMERO_RE.findall(gerado)):
        try:
            valor = float(n.replace(",", "."))
        except ValueError:
            continue
        if valor <= 12 and valor.is_integer():
            continue
        if n not in numeros_fonte and n not in fonte_norm:
            numeros_orfaos.append(n)

    # Identificadores técnicos (siglas, kebab-case, snake_case, a.b)
    identificadores_orfaos = [
        ident
        for ident in dict.fromkeys(_IDENT_RE.findall(gerado))
        if len(ident) > 3
        and ident.lower() not in _STOPWORDS
        and ident.lower() not in fonte_norm
    ]

    return RelatorioFidelidade(
        cobertura_termos=round(cobertura, 4),
        numeros_orfaos=numeros_orfaos[:12],
        identificadores_orfaos=identificadores_orfaos[:12],
        total_termos_avaliados=len(termos_gerados),
    )


def combinar_scores(score_llm: float, relatorio: RelatorioFidelidade) -> float:
    """Combina o veredito do Agente Crítico com o score léxico objetivo.

    Peso maior no LLM (entende semântica), mas o sinal léxico tem poder de veto
    quando encontra números ou identificadores inventados.
    """
    combinado = 0.65 * score_llm + 0.35 * relatorio.score_lexico
    if relatorio.numeros_orfaos:
        combinado = min(combinado, 0.79)
    if len(relatorio.numeros_orfaos) >= 3:
        combinado = min(combinado, 0.59)
    return round(max(0.0, min(1.0, combinado)), 2)
