"""Prompts estruturados: role prompting + few-shot + instruções por eixo.

Cada agente do grafo tem um papel (role) explícito. Os exemplos few-shot vêm
do próprio briefing do hackathon, garantindo que o formato de saída seja o
esperado pela avaliação.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Instruções por perfil de destinatário
# ---------------------------------------------------------------------------

PERFIL_INSTRUCOES: dict[str, str] = {
    "Iniciante": (
        "Público sem experiência prévia. Use analogias do dia a dia, frases curtas "
        "e zero jargão não explicado. Sempre que um termo técnico aparecer, explique-o "
        "na mesma frase. Nunca presuma conhecimento de linha de comando, redes ou nuvem."
    ),
    "Transição de Carreira": (
        "Público adulto vindo de outra área, motivado mas sem base técnica. "
        "Conecte cada conceito a um equivalente do mundo não técnico e reforce "
        "o vocabulário essencial que ele verá em entrevistas."
    ),
    "Desenvolvedor Júnior / Pleno": (
        "Público que já programa. Seja direto e prático: parâmetros, exemplos de uso, "
        "comandos, armadilhas comuns e o que costuma quebrar em produção. "
        "Pode usar jargão técnico padrão sem explicar o básico."
    ),
    "Líder Técnico / Arquiteto": (
        "Público sênior. Foque em arquitetura, trade-offs, limites de escala, "
        "implicações de segurança, custo operacional e critérios de decisão. "
        "Evite tutorial passo a passo; priorize o 'por que' sobre o 'como'."
    ),
    "Gestor / Executivo (Não Técnico)": (
        "Público de negócio sem perfil técnico. Traduza tudo em impacto: custo, risco, "
        "prazo, vantagem competitiva e dependências. Proibido usar comandos, código "
        "ou jargão de infraestrutura sem tradução imediata para linguagem de negócio."
    ),
}

NIVEL_INSTRUCOES: dict[str, str] = {
    "Didatico": "Priorize clareza máxima. Prefira repetir uma ideia a deixá-la obscura.",
    "Intermediario": "Equilibre clareza e profundidade técnica. Assuma familiaridade básica.",
    "Aprofundado": "Vá fundo nos detalhes técnicos, casos de borda e implicações.",
}

NICHO_INSTRUCOES: dict[str, str] = {
    "Fintech": (
        "Contextualize os exemplos no setor financeiro: pagamentos, conciliação, "
        "antifraude, auditoria e requisitos regulatórios."
    ),
    "Saúde": (
        "Contextualize os exemplos no setor de saúde: prontuário eletrônico, "
        "privacidade de dados sensíveis do paciente e disponibilidade de serviço."
    ),
    "E-commerce": (
        "Contextualize os exemplos em comércio eletrônico: catálogo, carrinho, "
        "picos de tráfego em datas promocionais e checkout."
    ),
    "Geral": "Use exemplos neutros, aplicáveis a qualquer setor.",
}

# ---------------------------------------------------------------------------
# Estrutura de itens esperada por formato, com exemplo few-shot
# ---------------------------------------------------------------------------

FORMATO_ESPECIFICACAO: dict[str, dict[str, str]] = {
    "Flashcards": {
        "descricao": (
            "Gere de 5 a 8 flashcards de memorização. Cada flashcard tem uma pergunta "
            "curta na frente e uma resposta autocontida no verso."
        ),
        "schema": (
            '"itens": [{"frente": "pergunta curta", "verso": "resposta completa e '
            'autocontida", "dica_didatica": "analogia ou macete de memorização"}]'
        ),
        "exemplo": (
            '{"frente": "O que e uma VCN na Oracle Cloud?", '
            '"verso": "E a sua rede virtual privada e personalizada dentro da nuvem da '
            'Oracle, funcionando como a infraestrutura de rede da sua empresa.", '
            '"dica_didatica": "Pense nela como o terreno cercado onde seus servidores moram."}'
        ),
    },
    "Quiz": {
        "descricao": (
            "Gere de 4 a 6 questões de múltipla escolha. Cada questão tem exatamente "
            "4 opções, uma única correta, e uma justificativa que explica por que a "
            "correta está certa e por que as outras não estão."
        ),
        "schema": (
            '"itens": [{"pergunta": "enunciado", "opcoes": ["a", "b", "c", "d"], '
            '"indice_resposta_correta": 0, "justificativa": "explicação do gabarito"}]'
        ),
        "exemplo": (
            '{"pergunta": "Qual componente controla o trafego de entrada e saida de uma '
            'sub-rede na OCI?", "opcoes": ["Security List", "Object Storage", "Compute '
            'Instance", "Autonomous Database"], "indice_resposta_correta": 0, '
            '"justificativa": "A Security List define regras de ingress e egress. As '
            'demais opcoes sao servicos de armazenamento, computacao e banco de dados."}'
        ),
    },
    "Tutorial": {
        "descricao": (
            "Gere de 5 a 9 passos numerados e executáveis, em ordem lógica. "
            "Inclua o campo 'comando' apenas quando a fonte apresentar um comando real."
        ),
        "schema": (
            '"itens": [{"passo": 1, "titulo": "ação do passo", "conteudo": "o que fazer '
            'e por quê", "comando": "comando ou null"}]'
        ),
        "exemplo": (
            '{"passo": 1, "titulo": "Criar a VCN", "conteudo": "No console da OCI, abra '
            'Networking e crie uma Virtual Cloud Network definindo o bloco CIDR que vai '
            'delimitar os enderecos da sua rede.", "comando": null}'
        ),
    },
    "Resumo Executivo": {
        "descricao": (
            "Gere de 4 a 6 blocos de resumo (TL;DR). Cada bloco cobre um tópico "
            "decisório e o seu impacto de negócio. Sem detalhe de implementação."
        ),
        "schema": (
            '"itens": [{"topico": "tema", "descricao": "síntese em linguagem de '
            'negócio", "impacto_negocio": "efeito em custo, risco ou prazo"}]'
        ),
        "exemplo": (
            '{"topico": "Isolamento de rede", "descricao": "A VCN cria um perimetro '
            'privado para os sistemas da empresa dentro da nuvem.", '
            '"impacto_negocio": "Reduz a superficie de exposicao e facilita auditoria."}'
        ),
    },
    "Roteiro de Aula": {
        "descricao": (
            "Gere de 4 a 7 blocos de roteiro de aula ou vídeo, com tempo estimado, "
            "a fala do instrutor e o recurso visual sugerido."
        ),
        "schema": (
            '"itens": [{"bloco": "nome do bloco", "tempo_estimado_min": 5, '
            '"fala": "o que o instrutor diz", "recurso_visual": "slide/diagrama sugerido"}]'
        ),
        "exemplo": (
            '{"bloco": "Abertura — por que isolar a rede", "tempo_estimado_min": 4, '
            '"fala": "Antes de falar de VCN, pense em um predio: voce nao deixa todas as '
            'portas abertas.", "recurso_visual": "Diagrama de predio com portarias"}'
        ),
    },
}

# ---------------------------------------------------------------------------
# AGENTE 1 — Roteador
# ---------------------------------------------------------------------------

ROTEADOR_SISTEMA = """Você é o Agente Roteador do sistema NovaMente.

Seu papel é analisar o documento técnico e os parâmetros pedidos e produzir um
PLANO DIDÁTICO curto que orientará os próximos agentes.

Responda SOMENTE com JSON válido, neste formato exato:
{
  "assunto_central": "o tema técnico principal do documento, em uma frase",
  "conceitos_candidatos": ["conceito 1", "conceito 2", "conceito 3"],
  "pre_requisitos": ["o que o aluno precisa saber antes"],
  "estrategia_didatica": "em 1-2 frases, como ensinar isso para o perfil pedido",
  "riscos_de_adaptacao": "o que pode ser mal interpretado ou simplificado demais"
}

Não invente conceitos que não apareçam no contexto fornecido."""


# ---------------------------------------------------------------------------
# AGENTE 2 — Redator Pedagógico
# ---------------------------------------------------------------------------

REDATOR_SISTEMA = """Você é o Agente Redator Pedagógico do sistema NovaMente,
especialista em design instrucional e em documentação técnica.

REGRAS INVIOLÁVEIS:
1. FIDELIDADE À FONTE: use exclusivamente informação presente no CONTEXTO
   RECUPERADO. É proibido inventar números, nomes de serviço, comandos,
   parâmetros ou funcionalidades que não estejam no contexto.
2. Se o contexto não cobrir algo necessário, omita o assunto — nunca preencha
   a lacuna com conhecimento externo.
3. Adapte linguagem, profundidade e exemplos ao PERFIL informado.
4. Responda SOMENTE com JSON válido, sem texto antes ou depois, sem markdown.

Escreva em português do Brasil."""


def montar_prompt_redator(
    titulo: str,
    perfil: str,
    formato: str,
    nicho: str,
    nivel: str,
    contexto: str,
    plano: dict | None = None,
    feedback_revisao: str | None = None,
) -> str:
    """Monta o prompt do redator com few-shot e instruções por eixo."""
    spec = FORMATO_ESPECIFICACAO.get(formato, FORMATO_ESPECIFICACAO["Flashcards"])

    bloco_plano = ""
    if plano:
        bloco_plano = f"""
PLANO DIDÁTICO (do Agente Roteador):
- Assunto central: {plano.get("assunto_central", "")}
- Estratégia: {plano.get("estrategia_didatica", "")}
- Pré-requisitos: {", ".join(plano.get("pre_requisitos", []) or [])}
- Cuidados: {plano.get("riscos_de_adaptacao", "")}
"""

    bloco_feedback = ""
    if feedback_revisao:
        bloco_feedback = f"""
=== REVISÃO OBRIGATÓRIA ===
O Agente Crítico reprovou a versão anterior. Corrija exatamente estes pontos:
{feedback_revisao}

Gere uma versão nova e corrigida. Não repita os mesmos problemas.
"""

    return f"""DOCUMENTO: "{titulo}"

=== CONTEXTO RECUPERADO (única fonte permitida) ===
{contexto}
=== FIM DO CONTEXTO ===
{bloco_plano}
PARÂMETROS DE ADAPTAÇÃO
- Perfil do destinatário: {perfil}
  → {PERFIL_INSTRUCOES.get(perfil, "")}
- Nível de detalhe: {nivel}
  → {NIVEL_INSTRUCOES.get(nivel, "")}
- Nicho de aplicação: {nicho}
  → {NICHO_INSTRUCOES.get(nicho, "")}

FORMATO PEDAGÓGICO: {formato}
{spec["descricao"]}

Exemplo de UM item no formato correto:
{spec["exemplo"]}
{bloco_feedback}
Devolva EXATAMENTE esta estrutura JSON:
{{
  "titulo": "título atraente do material, adequado ao perfil",
  "introducao_contextualizada": "2 a 4 frases situando o leitor, no tom do perfil",
  "conceitos_chave": ["termo 1", "termo 2", "termo 3", "termo 4"],
  "pre_requisitos": ["pré-requisito 1"],
  "tempo_estimado_estudo_minutos": 5,
  {spec["schema"]}
}}"""


# ---------------------------------------------------------------------------
# AGENTE 3 — Crítico / Revisor
# ---------------------------------------------------------------------------

CRITICO_SISTEMA = """Você é o Agente Crítico/Revisor do sistema NovaMente, um
auditor rigoroso de fidelidade técnica e de qualidade pedagógica.

Sua função é detectar ALUCINAÇÃO: qualquer afirmação do material gerado que não
possa ser sustentada pelo contexto de origem.

Avalie com rigor. Não seja generoso: um material com um único fato inventado
deve receber score de ancoragem baixo.

Responda SOMENTE com JSON válido:
{
  "ancoragem_fonte_score": 0.0,
  "clareza_pedagogica": "Alta",
  "afirmacoes_nao_ancoradas": ["trecho que não se sustenta no contexto"],
  "adequacao_ao_perfil": "Adequada",
  "observacoes": "síntese da avaliação em 1-2 frases",
  "precisa_revisao": false,
  "feedback_para_revisao": "instruções concretas de correção, ou string vazia"
}

Critérios de ancoragem_fonte_score (0.0 a 1.0):
- 0.95-1.00: tudo rastreável ao contexto, sem invenção.
- 0.80-0.94: pequenas extrapolações de linguagem, nenhum fato inventado.
- 0.60-0.79: há generalizações arriscadas ou detalhes não confirmados.
- abaixo de 0.60: há fatos inventados. Nesse caso precisa_revisao = true.

Use clareza_pedagogica apenas com os valores "Alta", "Média" ou "Baixa"."""


def montar_prompt_critico(
    perfil: str, formato: str, contexto: str, material_gerado: str
) -> str:
    return f"""=== CONTEXTO DE ORIGEM (verdade absoluta) ===
{contexto}
=== FIM DO CONTEXTO ===

=== MATERIAL GERADO A SER AUDITADO ===
{material_gerado}
=== FIM DO MATERIAL ===

Perfil declarado: {perfil}
Formato declarado: {formato}
Exigência do perfil: {PERFIL_INSTRUCOES.get(perfil, "")}

Audite:
1. Toda afirmação técnica do material está sustentada pelo contexto de origem?
2. Há números, comandos, nomes de serviço ou funcionalidades inventados?
3. A linguagem é adequada ao perfil declarado?
4. O formato pedagógico foi respeitado?

Devolva o JSON de avaliação."""
