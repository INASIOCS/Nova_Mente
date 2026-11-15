# Roteiro do Vídeo Demo — NovaMente

Entregável 2 de 4 do No Country: *"Um link do YouTube com a demo do projeto."*

**Duração alvo:** 4 a 5 minutos
**Formato:** gravação de tela com narração
**Idioma:** português do Brasil

---

## Antes de gravar — checklist

**1. Deixe tudo aberto em abas separadas**, para não perder tempo navegando:

- Aba 1 — Streamlit rodando: `python -m streamlit run ui/app.py` (http://localhost:8501)
- Aba 2 — o repositório no GitHub: https://github.com/INASIOCS/Nova_Mente
- Aba 3 — `docs/arquitetura.md` aberto no diagrama Mermaid
- Aba 4 — um arquivo de `examples/` aberto (o JSON do cenário 1)

**2. Cuidado com a cota do Gemini.** O free tier dá ~20 gerações por dia e cada
execução consome 3 chamadas. **Faça no máximo UMA geração ao vivo no vídeo.**
Para o resto, mostre os resultados já salvos em `examples/`. Se quiser testar o
roteiro antes, ative o modo econômico no `.env`:

```ini
AGENTE_ROTEADOR_ATIVO=false
MAX_REVISOES=0
```

**3. Antes de começar, gere UMA vez** o cenário Iniciante + Flashcards na
interface, para que o resultado já esteja na tela quando você começar a gravar.
Assim você evita 45 segundos de silêncio esperando o pipeline.

**4. Esconda a chave de API.** Não abra o arquivo `.env` em nenhum momento da
gravação.

---

## Roteiro

### [0:00 – 0:30] Abertura: o problema

> **Tela:** seu rosto ou um slide simples com o nome do projeto.

**Fala:**

"Oi, eu sou o Inasio, do Grupo 10. Vou apresentar o NovaMente.

Pensa numa empresa de tecnologia que tem uma documentação técnica enorme. Essa
mesma documentação precisa ser ensinada de um jeito para quem está começando a
programar, e de um jeito completamente diferente para um gestor que vai decidir
um investimento.

Hoje essa adaptação é manual. Um especialista lê tudo, entende o domínio e
reescreve para cada público. Leva semanas. E quando o software é atualizado, o
material envelhece e o ciclo recomeça.

O NovaMente faz isso em menos de um minuto."

---

### [0:30 – 1:00] O que o sistema faz

> **Tela:** a interface do Streamlit, mostrando a barra lateral com os seletores.

**Fala:**

"O sistema recebe uma documentação técnica em PDF, Markdown ou texto puro, e
devolve material didático pronto.

Aqui na lateral eu escolho três coisas: o perfil de quem vai estudar, o formato
pedagógico que eu quero, e o nicho de aplicação.

Para esta demonstração eu estou usando a documentação de redes da Oracle Cloud,
sobre Virtual Cloud Network."

> **Ação:** abra o seletor de Perfil e passe o mouse pelas opções, depois o de
> Formato. Mostre que existem 5 perfis e 5 formatos.

---

### [1:00 – 1:45] Demo 1 — Iniciante, Flashcards

> **Tela:** o resultado já gerado antes da gravação, na aba "Conteúdo".

**Fala:**

"Primeiro, o mesmo documento para um público iniciante, em flashcards.

Olha a linguagem que ele escolheu." — *leia em voz alta um flashcard, por
exemplo o da VCN* — "'É a sua rede virtual privada dentro da nuvem da Oracle.'
E a dica didática: 'pense nela como o terreno cercado onde seus servidores
moram.'

Repara que ele não só traduziu o texto: ele criou uma analogia do cotidiano, que
é exatamente o que um iniciante precisa."

> **Ação:** clique em "Mostrar resposta" em um ou dois flashcards.

---

### [1:45 – 2:30] Demo 2 — o mesmo documento, outro público

> **Tela:** abra `examples/cenario-2-vcn-arquiteto-resumo-executivo.md`, ou gere
> ao vivo se preferir (lembre: só uma geração ao vivo no vídeo todo).

**Fala:**

"Agora o ponto principal. Este é **o mesmo documento**, sem alterar uma vírgula
na fonte. Só mudei o perfil para Líder Técnico e o formato para Resumo
Executivo.

Olha como o conteúdo muda completamente." — *leia um trecho que fale de
trade-off, risco ou decisão de arquitetura* — "Sumiram as analogias. Agora ele
fala de superfície de exposição, de auditoria, de decisão.

É o mesmo documento de origem gerando dois materiais que ensinam públicos
diferentes."

---

### [2:30 – 3:00] Demo 3 — Quiz interativo

> **Tela:** aba "Quiz interativo" com o cenário 3 carregado.

**Fala:**

"E este é um dos diferenciais que implementamos: o quiz com avaliação em tempo
real.

O aluno responde aqui, e recebe na hora a justificativa do gabarito."

> **Ação:** responda uma questão **errada** de propósito, mostre o feedback
> explicativo, depois responda outra certa e mostre o placar de desempenho.

**Fala:**

"Ele não diz só 'errou': ele explica por que a resposta certa é a certa."

---

### [3:00 – 3:45] Como funciona por dentro

> **Tela:** a aba "Pipeline" do Streamlit, e depois o diagrama em
> `docs/arquitetura.md`.

**Fala:**

"Por dentro, não é uma chamada única a um modelo.

Primeiro tem um pipeline de RAG: o documento é quebrado em pedaços com
sobreposição, cada pedaço vira um vetor de embedding, e isso vai para um banco
vetorial. Aqui na tela dá para ver: sete chunks indexados no ChromaDB,
similaridade média de 0.79.

Depois entram quatro agentes orquestrados num grafo com LangGraph: um Roteador
que monta o plano didático, um Pesquisador que busca o contexto, um Redator que
escreve, e um Crítico que audita o resultado.

E o Crítico pode devolver o material para revisão. Aqui no rastro dá para ver
cada decisão que o sistema tomou."

---

### [3:45 – 4:20] O diferencial técnico: anti-alucinação

> **Tela:** continue na aba "Pipeline", mostrando o score de ancoragem.

**Fala:**

"Essa é a parte de que eu mais gosto.

Quando a gente pediu para o próprio modelo auditar o texto que ele mesmo
escreveu, ele se deu nota máxima, 1.0. Sempre.

Um modelo auditando a si mesmo se aprova. Então a gente criou uma segunda
camada, que não depende do modelo: ela mede quanto do vocabulário técnico do
material realmente existe no documento de origem, e caça números e nomes de
serviço que foram inventados — que é a alucinação mais perigosa, porque parece
plausível.

Essa camada tem poder de veto. Se aparece um número que não está na fonte, o
score é limitado, não importa o que o modelo diga. O resultado final aqui foi
0.82, e não 1.0. É um número honesto."

---

### [4:20 – 4:50] Saída estruturada, nuvem e exportação

> **Tela:** aba "JSON", depois aba "Exportar".

**Fala:**

"A saída é um JSON estruturado, no contrato exato que o desafio pediu, com os
metadados de aprendizado e a avaliação de qualidade. Isso permite integrar com
qualquer sistema externo.

O documento original e o pacote gerado são persistidos no Object Storage da
Oracle Cloud, na camada Always Free.

E o material pode ser exportado em Markdown, em PDF didático formatado, ou em
CSV para importar direto no Anki."

> **Ação:** clique em "PDF didático" para mostrar o download acontecendo.

---

### [4:50 – 5:00] Fechamento

> **Tela:** o repositório no GitHub.

**Fala:**

"O código está todo aberto no GitHub, com README, diagrama de arquitetura,
testes e os exemplos de execução versionados.

Obrigado!"

---

## ⚠️ Atenção no trecho da Oracle Cloud

No momento da gravação, verifique em que estado está a integração com o OCI:

**Se o bucket já estiver configurado e funcionando**, mostre na tela a aba
"Exportar" com o bloco `armazenamento_oci` trazendo `"status_upload":
"concluido"`, e narre como está no roteiro.

**Se ainda não estiver**, não afirme que está rodando na nuvem. Troque a fala
por algo honesto como:

> "A camada de persistência está implementada para o Object Storage da Oracle na
> camada Always Free, com a integração pronta no código, e estamos finalizando a
> configuração do bucket."

Um avaliador técnico vai conferir. É melhor ser preciso do que prometer.

---

## Dicas de gravação

- **OBS Studio** ou a própria gravação do Windows (`Win + G`) resolvem bem.
- Grave em **1920x1080** e aumente o zoom do navegador para **125%**: texto
  pequeno some na compressão do YouTube.
- Feche abas, notificações e qualquer coisa com dado pessoal na tela.
- Não precisa ser uma tomada única. Grave por blocos e junte depois.
- Fale um pouco mais devagar do que parece natural. Na gravação sempre soa mais
  rápido.
- Ao subir no YouTube, pode deixar como **"Não listado"** — o link funciona para
  os avaliadores sem ficar público na busca.
