# NovaMente

## Sistema Inteligente de Adaptação e Geração de Conteúdo Educacional

Hackathon ONE G10 — Projeto 1
Oracle Next Education & Alura — Grupo 10

Repositório: https://github.com/INASIOCS/Nova_Mente

## 1. O problema que atacamos

Empresas e escolas de tecnologia produzem documentação técnica rica, mas
frequentemente inacessível para quem não domina o jargão. Um mesmo manual de
infraestrutura em nuvem precisa ser ensinado de formas muito diferentes para
quem está dando os primeiros passos em programação e para quem vai tomar
decisões executivas de investimento.

Hoje essa adaptação é manual. Um designer instrucional lê a documentação,
entende o domínio, decide o recorte para cada público e reescreve tudo. O ciclo
leva semanas e depende de especialistas caros. Pior: quando o software é
atualizado, o material envelhece e o ciclo recomeça.

O NovaMente reduz esse ciclo de semanas para menos de um minuto, sem abrir mão
da fidelidade técnica ao documento original.

## 2. O que construímos

Uma aplicação que recebe documentação técnica em PDF, Markdown ou texto bruto e
devolve material didático pronto, parametrizado em três eixos:

Perfil do destinatário: Iniciante, Transição de Carreira, Desenvolvedor Júnior
ou Pleno, Líder Técnico ou Arquiteto, e Gestor ou Executivo não técnico.

Formato pedagógico: Flashcards, Quiz com justificativas, Guia prático passo a
passo, Resumo executivo e Roteiro de aula ou vídeo.

Nicho de aplicação: Fintech, Saúde, E-commerce e Geral.

A saída é um JSON estruturado contendo o conteúdo adaptado, metadados de
aprendizado (conceitos-chave, pré-requisitos e tempo estimado de estudo) e uma
avaliação de qualidade com score de ancoragem na fonte.

## 3. Como funciona

### 3.1 Ingestão

O documento é lido e normalizado. PDFs são processados com pypdf, com junção de
palavras quebradas por hifenização de fim de linha. Markdown tem a sintaxe de
ênfase removida, mas os blocos de código são preservados porque são conteúdo
técnico valioso. Documentos sem texto extraível, como PDFs digitalizados, são
rejeitados com mensagem clara em vez de gerar material vazio.

### 3.2 Pipeline de RAG

O texto é segmentado em chunks por um divisor recursivo que respeita a maior
fronteira semântica que couber: primeiro parágrafos, depois linhas, depois
frases. Cada chunk recebe a cauda do anterior como sobreposição, de modo que uma
definição técnica cortada na fronteira continue recuperável.

Os chunks são convertidos em embeddings com o modelo gemini-embedding-001, de
3072 dimensões, e indexados no ChromaDB com métrica de cosseno.

Uma decisão importante aqui: a consulta enviada ao Vector Store não é o título
do documento. Ela é montada a partir do formato e do perfil pedidos. Um quiz
precisa de fatos verificáveis, regras e exceções. Um resumo executivo precisa de
custo, risco e impacto. Um tutorial precisa de passos e comandos. Buscar o mesmo
contexto para todos os formatos desperdiçaria a etapa de recuperação.

### 3.3 Orquestração de agentes

A geração é um grafo de decisão construído com LangGraph, com quatro agentes:

O Agente Roteador lê uma amostra do documento e produz um plano didático:
assunto central, conceitos candidatos, pré-requisitos, estratégia de ensino para
aquele perfil e riscos de adaptação.

O Agente Pesquisador RAG executa o pipeline descrito acima e devolve os trechos
mais relevantes, com seus scores de similaridade.

O Agente Redator Pedagógico escreve o material. Ele opera sob uma restrição
explícita: usar exclusivamente informação presente no contexto recuperado. Se o
contexto não cobre algo, o assunto é omitido em vez de preenchido com
conhecimento externo.

O Agente Crítico/Revisor audita o resultado procurando alucinação e avaliando a
adequação ao perfil. Quando reprova, o grafo devolve o material ao Redator com
instruções concretas de correção, por uma única rodada.

### 3.4 Por que a verificação de fidelidade tem duas camadas

Este é o ponto de que mais nos orgulhamos tecnicamente.

Um LLM auditando o próprio texto tende a aprová-lo. Nas nossas execuções reais,
o Agente Crítico atribuiu nota máxima, 1.0, a materiais cuja verificação
objetiva mostrou sobreposição léxica de apenas 0.49 a 0.55 com o documento de
origem. Confiar apenas no LLM teria produzido um score de qualidade inflado e
inútil.

Por isso implementamos uma segunda camada, determinística, que não depende do
modelo e portanto não pode ser convencida por ele. Ela mede três coisas:

A cobertura de termos, isto é, que fração do vocabulário técnico do material
gerado existe de fato no documento de origem.

Os números órfãos: valores numéricos citados no material que não aparecem na
fonte. Essa é a forma mais comum e mais perigosa de alucinação técnica, porque
um limite de cota ou um número de porta inventado parece plausível e é falso.
Números pequenos, até 12, são ignorados porque funcionam como ordinais e
contagens didáticas.

Os identificadores órfãos: siglas, comandos e nomes de serviço inexistentes na
fonte.

O score final combina as duas camadas, com peso 0.65 para o LLM e 0.35 para a
verificação léxica. A camada léxica tem poder de veto: a presença de números
órfãos limita o resultado a 0.79, e três ou mais limitam a 0.59,
independentemente do que o LLM tenha afirmado.

### 3.5 Validação de tipos

Cada formato pedagógico tem um modelo Pydantic próprio. O quiz, por exemplo,
valida que o índice da resposta correta aponta para uma opção que realmente
existe. É um erro que o LLM comete e que passaria despercebido em um dicionário
solto, chegando quebrado na interface.

### 3.6 Persistência na Oracle Cloud

Cada execução grava dois artefatos no OCI Object Storage, na camada Always Free:
o documento técnico original enviado, para rastreabilidade, e o pacote
educacional gerado em JSON, acompanhado da requisição, dos metadados, da
avaliação de qualidade e do rastro completo do pipeline.

A camada de persistência fica atrás de uma interface abstrata com duas
implementações, selecionadas por variável de ambiente. Isso nos permitiu
construir e demonstrar o sistema inteiro enquanto o acesso ao console da OCI
estava pendente. Quando o backend local entra em ação, o campo de status retorna
"local" em vez de "concluido" e a interface exibe um aviso: a degradação fica
visível em vez de ser mascarada.

## 4. Decisões de projeto e por quê

Degradação explícita em todas as camadas. Cada componente tem um caminho de
contingência — LangChain cai para o SDK direto, os embeddings do Gemini caem
para um embedding léxico determinístico, o ChromaDB cai para um índice em
memória, o LangGraph cai para uma cadeia sequencial equivalente, e o OCI cai
para o disco local. Em todos os casos o backend em uso é reportado no
diagnóstico e na interface. Preferimos um sistema que degrada visivelmente a um
que falha por completo ou, pior, que finge sucesso.

Imagem Docker única com seleção de serviço. A mesma imagem serve a interface
Streamlit ou a API REST conforme uma variável de ambiente, lendo a porta do
ambiente. Isso evita acoplamento à plataforma de deploy e permite usar a mesma
construção no Railway e, depois, em uma instância OCI Compute Always Free.

Modo econômico de quota. O free tier da API do Gemini permite cerca de 20
requisições de geração por dia. Cada execução completa consome três chamadas, ou
cinco quando há rodada de revisão. Tornamos o Agente Roteador e a rodada de
revisão configuráveis, reduzindo o consumo para duas chamadas quando necessário.

## 5. Resultados

Executamos quatro cenários completos contra a API real:

Cenário 1 — documentação de VCN em Markdown, perfil Iniciante, formato
Flashcards: 7 itens, ancoragem 0.82, clareza Alta, 45,3 segundos.

Cenário 2 — o mesmo documento, perfil Líder Técnico ou Arquiteto, formato Resumo
Executivo, nicho Fintech: 5 itens, ancoragem 0.81, clareza Alta, 53,5 segundos.

Cenário 3 — o mesmo documento, perfil Desenvolvedor Júnior ou Pleno, formato
Quiz: 5 itens, ancoragem 0.82, clareza Alta, 38,3 segundos.

Cenário 4 — documentação de Object Storage em texto bruto, perfil Gestor ou
Executivo não técnico, nicho Saúde, formato Resumo Executivo: 5 itens, ancoragem
0.73, clareza Alta, 144,9 segundos.

Os três primeiros cenários usam o mesmo documento, o que demonstra diretamente a
capacidade de adaptação: de analogias do cotidiano para iniciantes a trade-offs
de arquitetura para perfis sêniores.

O cenário 4 é o mais instrutivo. Sua ancoragem de 0.73 ficou abaixo do limite de
0.80 e disparou automaticamente a rodada de revisão, o que explica os 144,9
segundos: foram cinco chamadas ao modelo em vez de três. O score permaneceu
baixo porque um resumo para público executivo necessariamente traduz termos
técnicos em linguagem de negócio, reduzindo a sobreposição léxica com a fonte.
O mecanismo funcionou como projetado: sinalizou o afastamento em vez de
mascará-lo.

As saídas completas estão versionadas no repositório, em JSON com o rastro do
pipeline e em Markdown pronto para leitura.

## 6. Stack técnica

Modelo de linguagem: Google Gemini, modelo gemini-3.5-flash.
Embeddings: gemini-embedding-001, 3072 dimensões.
Orquestração: LangGraph e LangChain.
Vector Store: ChromaDB com métrica de cosseno.
Ingestão de PDF: pypdf.
Tipagem e validação: Pydantic v2 e pydantic-settings.
API: FastAPI com Uvicorn.
Interface: Streamlit.
Exportação: reportlab para PDF e o módulo csv para o formato do Anki.
Nuvem: OCI Object Storage na camada Always Free.
Deploy: Docker, com Railway e OCI Compute como destinos.

## 7. Diferenciais implementados

Sistema multi-agentes com LangGraph, com Roteador, Pesquisador RAG, Redator
Pedagógico e Crítico/Revisor, incluindo aresta condicional de revisão.

Quiz com avaliação em tempo real: o aluno responde na interface e recebe
imediatamente a justificativa do gabarito, com placar de desempenho.

Exportação multiformato: Markdown, PDF didático formatado e CSV compatível com
o Anki.

## 8. Qualidade e testes

O projeto tem 29 testes automatizados que não consomem quota da API. Eles
validam o contrato de dados contra os exemplos literais do briefing, a
segmentação com sobreposição, a detecção de números órfãos e os exportadores.

Um desses testes revelou um defeito real durante o desenvolvimento: as chaves do
JSON estavam sendo contadas como vocabulário técnico na métrica de cobertura,
deprimindo artificialmente o score de fidelidade. A auditoria passou a percorrer
apenas os valores da estrutura.

## 9. Limitações conhecidas e próximos passos

A cota diária do free tier do Gemini limita o sistema a cerca de seis execuções
completas por dia, o que é suficiente para demonstração mas não para uso
contínuo. Uma conta paga ou um modelo local removeria essa restrição.

O score de ancoragem é naturalmente mais baixo para perfis não técnicos, pela
razão explicada no cenário 4. Um refinamento natural seria calibrar o limite de
revisão por perfil, em vez de usar um limite único.

O suporte multimodal, isto é, a interpretação de diagramas técnicos contidos no
documento original, não foi implementado e é o próximo diferencial natural.

O deploy completo em instância OCI Compute está preparado — a imagem Docker é
agnóstica de plataforma — mas ainda não executado.
