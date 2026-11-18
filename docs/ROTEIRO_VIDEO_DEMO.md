# Roteiro do Vídeo Demo — NovaMente

Entregável 2 de 4 do No Country: *"Um link do YouTube com a demo do projeto."*

**Duração alvo:** cerca de 5 minutos e 40
**Formato:** gravação de tela com narração
**Idioma:** português do Brasil

> Atualizado em 17/11/2026, depois que a integração com o OCI entrou em
> operação. Se precisar encurtar para 4:30, o corte menos custoso é o bloco da
> apresentação `.pptx` — não o da Oracle Cloud, que é requisito obrigatório do
> desafio.

---

## Antes de gravar — checklist

**1. Deixe tudo aberto em abas separadas**, para não perder tempo navegando:

- Aba 1 — Streamlit rodando: `python -m streamlit run ui/app.py` (http://localhost:8501)
- Aba 2 — o repositório no GitHub: https://github.com/INASIOCS/Nova_Mente
- Aba 3 — `docs/arquitetura.md` aberto no diagrama Mermaid
- Aba 4 — um arquivo de `examples/` aberto (o JSON do cenário 1)
- Aba 5 — o console da OCI no balde `novamente-conteudos-educativos`, já na
  lista de **Objetos**
- Um terminal, com o diretório do projeto aberto, para o `verificar_oci.py`

**2. A cota do Gemini tem DOIS limites, e o segundo é o que estraga gravação.**
São 20 gerações por dia **e 5 por minuto**. Uma execução completa dispara 3
chamadas em sequência, 5 se houver revisão — ou seja, **uma única geração pode
estourar o limite por minuto sozinha**, e o erro aparece na tela no meio do
vídeo. Pior: **tentativa que falha também consome o saldo diário**, então
repetir o comando na hora do nervosismo queima a cota do dia inteiro.

Regras práticas:

- **No máximo UMA geração ao vivo** no vídeo inteiro.
- Se der erro 429, **não repita na hora**. Espere um minuto, respire, e corte
  esse trecho na edição.
- Teste o roteiro antes com o modo econômico, que reduz para 2 chamadas:

```ini
AGENTE_ROTEADOR_ATIVO=false
MAX_REVISOES=0
```

**3. Gere o material de apoio com antecedência, não em cima da hora.** Antes de
gravar, rode UMA vez o cenário Iniciante + Flashcards na interface, para que o
resultado já esteja na tela quando a gravação começar — evita 45 segundos de
silêncio. Faça isso com folga: se falhar, você precisa de um minuto de espera.

**4. Esconda credenciais e dados pessoais.** Não abra o `.env`, o
`~/.oci/config` nem o arquivo `.pem` em momento algum. No console da OCI, o
canto superior direito mostra seu e-mail — vale esconder ou recortar na edição.

**5. Se for mostrar persistência na nuvem, gere o material no dia da gravação.**
Os exemplos salvos em `examples/` foram gerados antes da integração com o OCI
entrar no ar e trazem `"status_upload": "local"`. Narrar "está salvo na Oracle
Cloud" apontando para um desses arquivos seria impreciso, e um avaliador técnico
percebe. Veja o bloco da Oracle Cloud mais abaixo.

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

### [4:20 – 4:40] Saída estruturada

> **Tela:** aba "JSON".

**Fala:**

"A saída é um JSON estruturado, no contrato exato que o desafio pediu, com os
metadados de aprendizado e a avaliação de qualidade. Isso permite integrar com
qualquer sistema externo."

> **Ação:** role até o bloco `armazenamento_oci` e deixe visível o
> `"status_upload": "concluido"`.

---

### [4:40 – 5:05] Persistência real na Oracle Cloud

> **Tela:** o terminal, depois o console da OCI.

**Fala:**

"E isso não fica só na minha máquina. Cada execução grava dois objetos no Object
Storage da Oracle, na camada Always Free: o documento técnico original, para
rastreabilidade, e o pacote educacional gerado."

> **Ação 1:** no terminal, rode `python scripts/verificar_oci.py`. Ele leva
> poucos segundos e imprime a cadeia inteira em `[ok]`: configuração,
> credencial, namespace, balde, escrita e leitura.

**Fala:**

"Deixamos um diagnóstico no repositório que confere a cadeia inteira — a
credencial, o balde, e uma escrita e leitura de verdade. Qualquer pessoa da
equipe reproduz a configuração com um comando."

> **Ação 2:** passe para o console da OCI, na lista de objetos do balde, e mostre
> as pastas `originais/` e `conteudos/` com os arquivos lá dentro.

**Fala:**

"E aqui está, no console da Oracle: o documento de origem e o material gerado.

Um detalhe de projeto que vale citar: se a credencial da nuvem falhar, o sistema
não quebra e também não mente. Ele cai para a persistência local e devolve o
status 'local' em vez de 'concluido', com um aviso na interface. A degradação
fica visível."

---

### [5:05 – 5:25] Exportação

> **Tela:** aba "Exportar".

**Fala:**

"E o material pode ser exportado como uma apresentação de aula pronta em
PowerPoint, em PDF didático, em Markdown, ou em CSV para importar direto no
Anki."

> **Ação:** clique em "Baixar apresentação (.pptx)" e abra o arquivo. Mostre a
> capa, um slide de conteúdo e o slide de procedência com o score de ancoragem.

**Fala:**

"Repara que não é um despejo de texto em slides: tem capa, ficha do material,
um slide por conceito, e no fim um slide de procedência com o score de
ancoragem na fonte. É material que o professor leva direto para a sala."


---

### [5:25 – 5:40] Fechamento

> **Tela:** o repositório no GitHub.

**Fala:**

"O código está todo aberto no GitHub, com README, diagrama de arquitetura,
testes e os exemplos de execução versionados.

Obrigado!"

---

## ⚠️ Atenção no trecho da Oracle Cloud

**Situação em 17/11/2026:** a integração está no ar. O balde
`novamente-conteudos-educativos` existe na região de São Paulo, a credencial
funciona e já há objetos reais gravados e lidos de volta. O `.env` está com
`STORAGE_BACKEND=oci`, então qualquer execução nova grava na nuvem.

**O cuidado que resta é com o material antigo.** Os arquivos de `examples/`
foram gerados em 15/11, quando o backend ainda era local, e trazem
`"status_upload": "local"`. Se você mostrar um desses na tela enquanto narra a
persistência na nuvem, a imagem contradiz a fala — e é exatamente o tipo de
detalhe que um avaliador técnico nota.

Então, para o bloco da Oracle Cloud, use **uma destas duas fontes**:

1. O JSON da geração feita no dia da gravação, que já virá com
   `"status_upload": "concluido"`; ou
2. O console da OCI, mostrando os objetos no balde — que vale por si só,
   independentemente de qual execução os criou.

Antes de gravar, confirme com um comando que não gasta cota nenhuma:

```bash
python scripts/verificar_oci.py
```

Se ele terminar com `[ok]` em todas as etapas, pode narrar o trecho com
segurança. Se falhar, não afirme que está na nuvem — descreva a arquitetura e
siga em frente.

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
