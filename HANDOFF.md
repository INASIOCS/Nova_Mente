# Project Handoff — NovaMente

**Last Updated:** 2026-11-17 ~21:15 (horário local do sistema, Windows)
**Status:** ACTIVE — MVP funcional e testado; **integração com o OCI Object Storage executada e verificada de verdade**; falta uma execução do pipeline completo gravando no balde (bloqueada hoje pela cota diária do Gemini)
**Project:** NovaMente — Sistema Inteligente de Adaptação e Geração de Conteúdo Educacional
**Contexto:** Hackathon ONE G10 — Projeto 1 — Oracle Next Education & Alura
**Project Root:** `C:\Users\inasio\OneDrive\Área de Trabalho\Projeto_Nova_Mente`
**Repositório:** https://github.com/INASIOCS/Nova_Mente (público, branch `main`)
**Prazo real:** domingo, **22/11/2026, 23:59** — confirmado em 17/11 no próprio
painel do No Country (*Projeto · Aberto até dom., 22 de nov., 23:59*). O
"16/11" que constava aqui estava errado. Restam ~5 dias.

---

## 1. Goal

MVP que ingere documentação técnica (PDF, Markdown ou texto), ancora o conteúdo
via RAG e o transforma em material didático personalizado por **perfil**,
**formato pedagógico** e **nicho**, com saída em JSON estruturado, interface
interativa, API REST e persistência obrigatória em **OCI Object Storage
(camada Always Free)**.

O conteúdo integral do briefing (contrato JSON, checklist de 8 itens,
diferenciais) está transcrito na seção 6 — **não é necessário reler o PDF**.

---

## 2. Current State

O sistema está **implementado e funcionando de ponta a ponta**. Quatro execuções
reais com a API do Gemini produziram material didático correto e tecnicamente
fiel, versionado em `examples/`.

**Novidade desta sessão (17/11):** o OCI saiu do papel. Credencial criada, balde
criado, e o backend `oci` **gravou e leu objetos reais** no
`novamente-conteudos-educativos`. O `.env` já está com `STORAGE_BACKEND=oci`.

O que ainda falta para o item 6 ficar 100%: **uma execução do pipeline completo**
(com LLM) devolvendo `status_upload: "concluido"` dentro da resposta. Isso não é
limitação do OCI — é a cota diária do Gemini, esgotada hoje.

**Novidade da madrugada de 18/11:** a interface está **publicada e acessível**
em <https://nova-mente.streamlit.app>, na Streamlit Community Cloud, a partir do
`main` do GitHub. O link é público e já foi preparado para ser enviado ao grupo.
Nessa nuvem a persistência cai para disco local (sem a seção `[oci]` nos
segredos) e o disco é efêmero — o OCI continua sendo exercitado pela máquina do
usuário.

### Evidence Summary

- **IMPLEMENTED:** pipeline completo — ingestão (PDF/MD/texto), RAG (chunking,
  embeddings Gemini, ChromaDB), orquestração LangGraph com 4 agentes,
  verificação anti-alucinação em 2 camadas, validação Pydantic estrita,
  storage abstraído (local + OCI), FastAPI, Streamlit com quiz interativo,
  exportação em apresentação .pptx, Markdown, PDF e CSV-Anki, Docker e
  configuração Railway.
- **TESTED (17/11):** `.venv\Scripts\python.exe -m pytest tests -q` →
  **34 passed**, já com `STORAGE_BACKEND=oci` no `.env`. Nenhum teste consome
  quota da API nem exige credencial do OCI.
- **VERIFIED (17/11) — OCI Object Storage real:** `scripts/verificar_oci.py`
  percorreu a cadeia inteira com sucesso: config → credencial aceita →
  namespace `gr6m1uqnjub1` → balde `novamente-conteudos-educativos`
  (Standard, NoPublicAccess, compartimento raiz `InasioOCI`) → escrita, leitura
  idêntica e remoção de um objeto de teste. Em seguida, a camada de storage do
  projeto (`criar_storage()` + `enviar_bytes`/`enviar_json`) gravou **dois
  artefatos reais** que continuam no balde:
  `originais/oci-vcn-arquitetura-de-redes-014ee9.md` (6.246 bytes) e
  `conteudos/oci-vcn-arquitetura-de-redes-iniciante-flashcards-1c1d52.json`
  (12.746 bytes), ambos com `status_upload: "concluido"`, e o JSON foi lido de
  volta íntegro.
- **VERIFIED (17/11):** `GET /saude?profundo=true` →
  `storage_backend_ativo: "oci"`, `bucket_acessivel: true`,
  `aviso_storage: null`.
- **VERIFIED (15/11):** os 4 decks dos cenários de `examples/` foram
  renderizados em PNG pelo PowerPoint e conferidos slide a slide, junto com
  um deck de casos-limite (título de três linhas, corpo longo, comando
  extenso): sem estouro de caixa, sem sobreposição e sem texto cortado.
- **VERIFIED:** material do cenário 1 inspecionado manualmente — tecnicamente
  correto e adequado ao perfil iniciante. Chave do Gemini validada. Modelos
  disponíveis confirmados por `list_models`. `.env` confirmado fora do Git.
- **VERIFIED (17/11):** repositório limpo e sincronizado —
  `git status` sem alterações, `main` alinhada com `origin/main` em `5b8db88`.
- **APPROVED:** as 6 decisões da seção 4 foram escolhidas explicitamente pelo
  usuário.

### O que NÃO está feito

- **Execução do pipeline completo gravando no OCI.** A camada de storage está
  verificada, mas nenhuma resposta gerada pelo pipeline carregou ainda
  `status_upload: "concluido"`. Bloqueado hoje pela cota diária do Gemini
  (ver Known Issues); é um comando só quando a cota voltar.
- Deploy no Railway (pendente, e agora **opcional**: a publicação para o grupo
  e a avaliação saiu pela Streamlit Community Cloud, que é gratuita. O Railway
  segue preparado no repositório caso seja preciso expor também a API REST).
- Anotações no No Country (pendente — exige sessão autenticada do usuário).
- Cenário 5 de demonstração (ingestão de PDF → Tutorial) ainda não gerado:
  três tentativas em 17/11 bateram no limite por minuto e depois no diário.

---

## 3. Active Workflows

### Workflow: Núcleo da aplicação
**Status:** COMPLETED

Todo o pipeline está implementado, testado e commitado. Nada pendente.

**Validação executada (17/11)**
- `.venv\Scripts\python.exe -m pytest tests -q` → 33 passed.

---

### Workflow: Integração OCI Object Storage (OBRIGATÓRIO)
**Status:** IN PROGRESS — infraestrutura e storage VERIFICADOS; falta a execução
do pipeline completo

**Executado e verificado em 17/11**
- Balde `novamente-conteudos-educativos` criado na região `sa-saopaulo-1`
  (Brasil Leste / São Paulo), compartimento raiz `InasioOCI`, escopo Namespace,
  camada **Standard**, privado, sem auto-tiering, sem versionamento, chave de
  criptografia gerenciada pela Oracle — tudo dentro da Always Free.
- Namespace do tenancy: `gr6m1uqnjub1` (fixado em `OCI_NAMESPACE` no `.env`
  para poupar uma chamada por execução).
- Chave de API registrada no usuário; privada instalada em
  `C:\Users\inasio\.oci\oci_api_key.pem`, **fora** da pasta sincronizada do
  projeto. `~/.oci/config`, perfil `DEFAULT`, aponta para ela.
- `.env`: `STORAGE_BACKEND=oci`.
- Dois objetos reais gravados e conferidos no balde (ver Evidence Summary).

**Completed (código, de sessões anteriores)**
- `app/storage/oci_storage.py` implementado: autenticação por arquivo de
  configuração (`~/.oci/config`) com fallback para Resource Principal,
  `enviar_bytes` (`put_object`), `garantir_bucket`, montagem da URI pública
  (`https://objectstorage.<regiao>.oraclecloud.com/n/<ns>/b/<bucket>/o/<obj>`)
  e tratamento de falha sem derrubar o pipeline.
- `app/storage/factory.py` seleciona o backend por `STORAGE_BACKEND` e devolve
  um aviso explícito quando degrada para o local.
- `.env` **já traz os valores certos** de `OCI_BUCKET_NAME`
  (`novamente-conteudos-educativos`), `OCI_REGION` (`sa-saopaulo-1` — a mesma
  região do console aberto), `OCI_CONFIG_FILE` (`~/.oci/config`) e
  `OCI_PROFILE` (`DEFAULT`). `OCI_NAMESPACE` está **vazio de propósito** — o
  código o descobre por `get_namespace()`.
- SDK `oci 2.191.0` instalado no `.venv` (**confirmado em 17/11**).

**Pending**
1. Com a cota do Gemini renovada, rodar o pipeline completo uma vez:
   `.venv\Scripts\python.exe scripts/gerar_exemplos.py 5` (gera também o cenário
   5, que falta). Conferir `armazenamento_oci.status_upload == "concluido"` no
   JSON gerado.
2. Atualizar o item 6 do checklist (seção 6) com essa evidência.

**Dependencies / Blockers**
- Cota diária do Gemini (ver Known Issues). Nada a ver com o OCI.

**Validation / Success Criteria**
- `python scripts/verificar_oci.py` termina com exit 0 — **já atendido**.
- `GET /saude?profundo=true` → `storage_backend_ativo: "oci"`,
  `bucket_acessivel: true`, sem aviso — **já atendido**.
- Uma execução do pipeline grava os dois objetos e a resposta traz
  `"status_upload": "concluido"` — **pendente**.

---

### Workflow: Deploy na Streamlit Community Cloud
**Status:** DONE — no ar em <https://nova-mente.streamlit.app> (18/11, 00h)

**Completed**
- App criado em share.streamlit.io a partir de `INASIOCS/Nova_Mente`, branch
  `main`, arquivo `ui/app.py`, Python 3.12.
- `GOOGLE_API_KEY` e o modo econômico (`AGENTE_ROTEADOR_ATIVO=false`,
  `MAX_REVISOES=0`) colados em *Advanced settings -> Secrets* pelo usuário.
- `app/core/segredos_nuvem.py` faz a ponte `st.secrets` -> variáveis de
  ambiente, porque na nuvem não existe `.env`. Fora da nuvem não faz nada.
- `.streamlit/secrets.toml.example` é o modelo versionado (sem valores).
- Verificado no ar: a interface carrega e o aviso de cota aparece corretamente.

**Regra operacional — não esquecer**
- Todo commit que mexa em arquivo **fora** de `ui/app.py` exige **Reboot app**
  no painel. Ver o Finding sobre o cache de módulos, na seção 6.

**Pending / opcional**
- Seção `[oci]` nos segredos, para exercitar o Object Storage também pela
  nuvem. Exige colar a chave privada no painel de um terceiro — decisão do
  usuário, hoje deliberadamente não feita.

---

### Workflow: Deploy no Railway
**Status:** PENDING

**Completed**
- `Dockerfile` (imagem única, `SERVICE=ui|api`, porta de `$PORT`),
  `entrypoint.sh`, `railway.json` e `.dockerignore` commitados.

**Pending**
1. No painel do Railway, criar projeto a partir de `INASIOCS/Nova_Mente`.
2. Definir variáveis: `GOOGLE_API_KEY` (**pelo usuário**), `SERVICE=ui`,
   `GEMINI_MODEL=gemini-3.5-flash`,
   `GEMINI_EMBEDDING_MODEL=models/gemini-embedding-001`.
3. Opcional: segundo serviço no mesmo repositório com `SERVICE=api` e
   `healthcheckPath=/saude`.

**Dependencies / Blockers**
- Sessão autenticada do usuário (o navegador interno do Claude não está logado).
- Por regra de segurança o agente **não digita chaves de API em formulários de
  serviços externos** — a `GOOGLE_API_KEY` é inserida pelo usuário.

**Validation / Success Criteria**
- A URL pública abre a interface Streamlit e gera um material com sucesso.

---

### Workflow: Entrega no No Country
**Status:** IN PROGRESS — 3 de 4 entregáveis enviados

**Corrigido em 17/11, olhando o painel logado**
- A página `/my-simulation/communication` **não tem campo de publicação**. Ela é
  informativa e trata do **Discord** como espaço de comunicação da equipe
  (convite: `discord.gg/wbJTXGmTba`; canais `general`, `notificaciones`,
  `sprint-meet-obligatorio` e por papel). A premissa anterior deste handoff —
  "a página onde vamos colocando todas as anotações" — estava errada. O texto de
  `docs/anotacoes-nocountry.md` serve para o Discord, não para aquela página.
- A entrega de verdade fica em `/my-simulation/deliverables`
  (menu **Projeto**). Qualquer integrante envia ou edita enquanto estiver
  aberto, e **cada envio substitui a versão anterior para toda a equipe**.

**Estado dos 4 entregáveis (17/11)**
| # | Entregável | Situação |
|---|---|---|
| 1 | Documentação (PDF) | ✅ `NovaMente_Documentacao.pdf` (13 kB) — confere com o arquivo local |
| 2 | Vídeo demo (link do YouTube) | ❌ **não enviado** — é a única lacuna |
| 3 | Ferramentas | ✅ 10 itens, inclusive Claude Code e Docker |
| 4 | Links | ✅ Repositório GitHub — NovaMente |

**Contexto da equipe**
- Equipe `G10-BRASIL-equipo 9`, projeto registrado na plataforma como
  **"NuevaMente"** (o repositório usa *NovaMente* — divergência cosmética).
- Papel do usuário no painel: **UX/UI Designer**.
- 9 integrantes: Inasio, TIAGO, Carlos, Enoque, Aguinaldo, Thiago, Davi,
  Vanessa e Luis Felipe (primeiros nomes como o painel exibe).
- Avaliação 360 do usuário: concluída em 17/11.

**Next Step**
- Gravar e publicar o vídeo demo, seguindo `docs/ROTEIRO_VIDEO_DEMO.md`, e
  enviar o link do YouTube no entregável 2.
- Opcional: publicar o texto de `docs/anotacoes-nocountry.md` no canal
  `general` do Discord da equipe.

---

### Workflow: Cenário 5 de demonstração
**Status:** PENDING

- Falhou com `429` em 15/11 — cota diária do free tier esgotada
  (~20 gerações/dia). A cota já deve ter renovado.
- Comando: `.venv\Scripts\python.exe scripts/gerar_exemplos.py 5`.
- **Não é bloqueante**: o checklist exige 3 exemplos e há 4 versionados.

---

## 4. Approved / Must Preserve [P0]

- **[APPROVED] LLM: Google Gemini.** Modelo em uso: `gemini-3.5-flash`.
- **[APPROVED] Interface: Streamlit + FastAPI (ambos).** Não reduzir a um só.
- **[APPROVED] Deploy: Railway como principal**, mantendo o repositório pronto
  para OCI Compute. Palavras do usuário: *"Railway, mais já deixa tudo no git
  para quando eu tiver recuperado a minha senha do OCI eu cumprir essa parte de
  fazer o deploy completo também na nuvem do OCI"*.
  - **Regression boundary:** o deploy no Railway **não substitui** o OCI Object
    Storage obrigatório. Não acoplar o código a particularidades do Railway.
- **[APPROVED] Repositório `Nova_Mente`, público.** Já criado e publicado.
- **[APPROVED] Documentos da demo: documentação da OCI.** Três documentos
  próprios em `docs/fontes/`, um por formato de ingestão.
- **[APPROVED] Escopo completo:** obrigatório + multi-agentes LangGraph + quiz
  interativo + exportação multiformato. Todos os três diferenciais estão
  implementados.
- **[MUST PRESERVE] Camada Always Free da OCI.** Citação do edital: *"deve-se
  utilizar estritamente a camada Always Free da OCI, evitando configurações que
  possam gerar custos monetários."*
- **[MUST PRESERVE] Contrato JSON do briefing.** Os nomes de campo da seção 6
  são conferidos na avaliação. Não renomear.
- **[MUST PRESERVE] Degradação visível.** Quando um backend cai para o fallback,
  isso aparece no diagnóstico e na interface. O fallback de storage retorna
  `status_upload: "local"`, nunca `"concluido"`.
- **[MUST PRESERVE] `_texto_da_resposta()` em `app/agents/llm.py`.** Ver seção 6.

---

## 5. User Instructions [P0]

### Requirements
- *"é um projeto que tem um PDF que você precisa ler, cria ele na pasta e depois
  subir para o GIT"* — **FEITO**.
- *"https://talent.nocountry.tech/my-simulation/communication que é a pagina onde
  devemos ir colocando lá todas as anotações"* — **SUPERADO pelos fatos**: em
  17/11, com a sessão aberta, confirmou-se que essa página não tem campo de
  publicação; ela aponta para o Discord da equipe. A intenção (registrar o
  andamento para o grupo) continua válida — muda o destino.
- Prazo: *"Até Segunda-feira 16/11/2026"* — **incorreto**. O painel mostra
  22/11/2026, 23:59.
- *"Sim, acredito que sim"* — outros integrantes do Grupo 10 também devem
  commitar; manter o histórico legível e por camada.

### Approvals
- *"Você pode publicar direto, faça os comentários como eu Inasio."*
- Repositório `Nova_Mente`, público.

### Preferences
- Comunicação em português do Brasil.

### Prohibitions
- Não usar recursos da OCI fora da camada Always Free.
- O agente não digita chaves de API, senhas ou tokens em formulários de serviços
  externos. Essas inserções ficam com o usuário.

---

## 6. Shared Understanding [P0]

### Finding: Contrato de dados exato exigido pelo briefing
- **Confidence:** CONFIRMED (transcrito do PDF, páginas 4–5)
- **Impact:** implementado em `app/schemas/content.py` e coberto por testes que
  validam estes exemplos literais.

**Entrada:**
```json
{
  "documento_titulo": "Introducao a Arquitetura de Redes VCN na OCI",
  "documento_conteudo": "A Virtual Cloud Network (VCN) e uma rede privada...",
  "perfil_destinatario": "Iniciante",
  "formato_saida": "Flashcards",
  "nicho_setor": "Geral",
  "nivel_detalhe": "Didatico"
}
```

**Saída:** `status`, `metadados` (`perfil_aplicado`, `formato_gerado`,
`tempo_estimado_estudo_minutos`, `conceitos_chave`), `conteudo_adaptado`
(`titulo`, `introducao_contextualizada`, `itens`), `avaliacao_qualidade`
(`ancoragem_fonte_score`, `clareza_pedagogica`, `observacoes`) e
`armazenamento_oci` (`bucket`, `objeto_id`, `status_upload`).

### Finding: Checklist de avaliação (8 requisitos mínimos)
- **Confidence:** CONFIRMED

| # | Requisito | Situação |
|---|---|---|
| 1 | Ingestão (PDF, Markdown ou texto) | ✅ os 3 formatos, exercitados nos cenários |
| 2 | RAG com chunking, embeddings e busca vetorial | ✅ ChromaDB + `gemini-embedding-001` |
| 3 | Orquestração com LLM | ✅ LangGraph, 4 agentes |
| 4 | Mesmo conteúdo para ≥2 perfis e ≥2 formatos | ✅ cenários 1, 2 e 3 (mesmo doc de VCN) |
| 5 | JSON estruturado + interface ou API REST | ✅ Pydantic + Streamlit **e** FastAPI |
| 6 | OCI Object Storage (Always Free) | 🟡 balde criado e objetos reais gravados/lidos em 17/11; falta uma resposta do pipeline com `status_upload: "concluido"` |
| 7 | ≥3 exemplos de execução | ✅ 4 versionados em `examples/` |
| 8 | Documentação com diagrama de arquitetura | ✅ README + `docs/arquitetura.md` (Mermaid) |

**O item 6 deixou de ser risco de infraestrutura e virou só uma questão de cota:
o balde responde, a credencial funciona e os objetos estão lá.**

### Finding: A aplicação nunca cria o bucket sozinha — por decisão
- **Finding:** `OCIObjectStorage.garantir_bucket(compartment_id)` não é chamado
  por nenhum caminho da aplicação. Desde 17/11 existe **um** chamador:
  `scripts/verificar_oci.py --criar-bucket`, explícito e fora do pipeline.
- **Impact:** se o bucket sumir, o upload falha com `status_upload: "falhou"`;
  recrie pelo console ou pelo script. Não acople criação de recurso ao pipeline.
- **Confidence:** CONFIRMED (17/11)

### Finding: Estado local do OCI (17/11, após o setup)
- `~/.oci/config` existe, perfil `DEFAULT`, apontando para
  `C:/Users/inasio/.oci/oci_api_key.pem`.
- O **OCI CLI não está instalado** e não é necessário — o `config` foi escrito à
  mão a partir do *Configuration file preview* do console.
- SDK Python `oci 2.191.0` no `.venv`.
- `STORAGE_BACKEND=oci` e `OCI_NAMESPACE=gr6m1uqnjub1` no `.env`.
- **Confidence:** CONFIRMED

### Finding: A chave privada da API só existe no instante da criação
- **Finding:** no fluxo *Gerar par de chaves de API*, o console oferece o
  download da privada **uma única vez**. Fechou a janela, a chave registrada
  fica inútil: só resta excluí-la e criar outra. Isso custou duas tentativas
  em 17/11.
- **Impact:** prefira *Colar chave pública* com um par gerado localmente — não
  há download para perder, e o fingerprint é conhecido de antemão.
- **Confidence:** CONFIRMED (observado duas vezes)

### Finding: O free tier do Gemini tem DOIS limites, não um
- **Finding:** além do limite diário (`GenerateRequestsPerDayPerProjectPerModel`,
  **20/dia por modelo**), existe um limite por minuto
  (`GenerateRequestsPerMinutePerProjectPerModel`, **5/min**). Uma execução
  completa dispara 3 chamadas em sequência (Roteador, Redator, Crítico) e 5 se
  houver revisão — ou seja, **uma única execução pode estourar o limite por
  minuto sozinha**.
- **Evidence:** em 17/11, três tentativas do cenário 5: as duas primeiras caíram
  em `quota_value: 5` com `retry_delay` de 23s e 30s; a terceira, já com a janela
  aberta, caiu em `quota_value: 20` (diário) com `retry_delay: 28429s` (~7h54m).
- **Impact crítico:** **tentativas que falham também consomem o saldo diário.**
  Repetir um comando que deu 429 por minuto queima quota diária à toa. Espere
  pelo menos 60s entre tentativas, e prefira o modo econômico
  (`AGENTE_ROTEADOR_ATIVO=false`, `MAX_REVISOES=0` → 2 chamadas).
- **Na apresentação:** use os exemplos versionados em `examples/`. Gerar ao vivo
  é arriscado por causa do limite por minuto.
- **Confidence:** CONFIRMED (17/11)

### Finding: A Streamlit Cloud recarrega o script, mas não os módulos
- **Finding:** quando chega um commit novo, a Streamlit Community Cloud baixa os
  arquivos e **re-executa apenas o script principal** (`ui/app.py`). Os módulos
  Python já importados (`app/agents/llm.py`, `app/pipeline.py`, ...) continuam
  **em memória, na versão antiga**. O app passa a rodar metade do código novo e
  metade do antigo.
- **Evidence (18/11, três ciclos seguidos):**
  1. Push com `from app.agents.llm import ErroQuota` no topo da UI →
     `ImportError` na nuvem, porque o `llm.py` em memória ainda era o anterior.
     O mesmo arquivo subia sem erro no local, onde o processo nasce limpo.
  2. Push seguinte trocando o import por `getattr(exc, "cota_esgotada", False)`
     → a tela mostrou "Erro inesperado" com o texto `ErroQuota: Cota da API do
     Gemini esgotada.` dentro: UI nova lendo exceção de um `llm.py` velho, que
     ainda não tinha o atributo.
  3. Depois do **Reboot app**, tudo alinhado e o painel de cota correto no ar.
- **Impact:** todo commit que mexa em arquivo **fora** do `ui/app.py` exige
  Reboot no painel (*Manage app -> menu ... -> Reboot app*). Mudança só no
  script principal pega sozinha.
- **Correção de registro:** a mensagem do commit `4f5a28d` atribui esse
  `ImportError` ao conflito de nome entre `ui/app.py` e o pacote `app`. **Essa
  explicação está errada** — a causa é o cache de módulos descrito aqui. A
  mudança daquele commit continua válida por outro motivo: um import a menos no
  topo deixa a interface menos acoplada ao pacote.
- **Confidence:** CONFIRMED (18/11, observado no ar nos três ciclos)

### Finding: Nem todo modelo Gemini está disponível para esta chave
- **Finding:** `gemini-2.5-flash` responde *"no longer available to new users"*;
  `gemini-3.8-flash` e `gemini-flash-latest` devolvem `504 DeadlineExceeded`.
  **`gemini-3.5-flash` funciona** e é o modelo em uso. O embedding
  `text-embedding-004` não existe mais; **`gemini-embedding-001`** funciona
  (3072 dimensões).
- **Impact:** não troque o modelo sem testar.
- **Confidence:** CONFIRMED

### Finding: No LangChain 1.x, `AIMessage.content` pode ser uma LISTA
- **Finding:** `response.content` vem como `[{"type": "text", "text": "..."}]`.
  Aplicar `str()` devolve o repr do Python, não o texto — causa silenciosa de
  "JSON inválido".
- **Impact:** resolvido por `_texto_da_resposta()` em `app/agents/llm.py`, que
  trata string e lista de blocos. **Não reverter.**
- **Confidence:** CONFIRMED (foi a causa da primeira falha do pipeline)

### Finding: Os modelos atuais gastam a maior parte dos tokens em raciocínio
- **Finding:** em um teste, 116 de 127 tokens de saída foram de raciocínio, o
  que truncou a resposta com `max_output_tokens=64`.
- **Impact:** `max_output_tokens` está em 16384. Não reduzir.
- **Confidence:** CONFIRMED (via `usage_metadata`)

### Finding: O navegador interno do Claude é isolado do navegador do usuário
- Railway e No Country redirecionaram para login no navegador interno, embora o
  usuário esteja logado no próprio navegador.
- **Impact:** console da OCI, Railway e No Country exigem o navegador do usuário
  (que é o **Edge**) ou login/importação de cookies no painel interno.
- **Confidence:** CONFIRMED

### Finding: Ferramentas locais
- Python 3.13.17; `python`, `py` e `python3` funcionam; venv em `.venv`.
- `gh` 2.104.0 em `C:\Program Files\GitHub CLI\gh.exe`, autenticado como
  **INASIOCS** — **fora do PATH do Bash**, invoque pelo caminho completo.
- **Confidence:** CONFIRMED

---

## 7. Key Decisions

### Decision: Camada de storage abstraída com fallback local
- **Chosen:** `StorageBackend` com `LocalStorage` e `OCIObjectStorage`.
- **Why:** permitiu construir e demonstrar todo o MVP enquanto o acesso ao OCI
  estava indisponível.
- **Consequence:** o fallback **não** cumpre o item 6 do checklist; por isso
  retorna `status_upload: "local"` e emite aviso, em vez de simular sucesso.

### Decision: Verificação anti-alucinação em duas camadas
- **Chosen:** auditoria semântica por LLM **+** verificação léxica determinística
  com poder de veto (`0.65 × LLM + 0.35 × léxico`).
- **Why:** um LLM auditando o próprio texto tende a aprová-lo. Nos cenários
  reais o LLM deu 1.0 enquanto o léxico deu 0.49–0.55 — a combinação produziu
  0.73–0.82, bem mais honesto.
- **Ruled Out:** confiar apenas no Agente Crítico.

### Decision: Consulta de recuperação derivada dos parâmetros
- **Chosen:** a consulta ao Vector Store é montada a partir de formato + perfil +
  nicho, não do título.
- **Why:** um quiz precisa de fatos verificáveis; um resumo executivo precisa de
  custo e risco. Buscar o mesmo contexto para todos desperdiçaria o RAG.

### Decision: Imagem Docker única com `SERVICE=ui|api`
- **Why:** a mesma imagem serve Railway e, depois, OCI Compute Always Free, sem
  acoplamento à plataforma.

### Decision: Modo econômico de quota configurável
- **Chosen:** `AGENTE_ROTEADOR_ATIVO` e `MAX_REVISOES` em variáveis de ambiente.
- **Why:** o limite de ~20 gerações/dia inviabiliza demonstrações repetidas na
  configuração completa.

---

## 8. What Worked

### Pipeline completo contra a API real
- **Result:** 4 cenários, ancoragem 0.73–0.82, clareza Alta, 38–145s.
- **Evidence:** VERIFIED — saídas em `examples/`, material do cenário 1
  inspecionado manualmente.

### Rodada de revisão do Agente Crítico
- **Result:** no cenário 4 (ancoragem 0.73 < 0.80) a revisão disparou
  automaticamente, elevando o tempo para 144,9s (5 chamadas em vez de 3).
- **Evidence:** VERIFIED no rastro do pipeline.
- **Why it matters:** prova que a aresta condicional do LangGraph funciona.

### Correção: `gerar_exemplos.py` apagava o RESUMO ao rodar um subconjunto
- **Result:** rodar `gerar_exemplos.py 5` sobrescrevia `examples/RESUMO.json`
  com apenas aquele cenário — em 17/11 isso apagou o registro dos 4 cenários
  bons (restaurado com `git checkout`).
- **Evidence:** TESTED — agora o script mescla por `id`; um `ok` novo substitui
  o anterior, e um `erro` só ocupa vaga vazia, para o resumo não contradizer os
  arquivos presentes. Verificado com `gerar_exemplos.py 99` (nenhuma chamada à
  LLM): os 5 registros permanecem intactos.
- **Why it matters:** o próximo passo do projeto é exatamente rodar o cenário 5
  sozinho.

### Teste que revelou defeito real na métrica de fidelidade
- **Result:** as chaves do JSON eram contadas como vocabulário técnico,
  deprimindo a cobertura. Corrigido para percorrer apenas os valores.
- **Evidence:** TESTED — `test_material_ancorado_tem_score_alto`.

### Verificação visual dos decks por renderização em PNG
- **Result:** os 4 decks + um deck de casos-limite conferidos slide a slide.
- **Evidence:** VERIFIED (15/11).
- **Why it matters:** `app/export/slides.py` monta o layout por código; só a
  renderização revela estouro de caixa.

---

## 9. What Didn't Work

### `str(resposta.content)` no caminho LangChain
- **Result / Error:** `ErroLLM: O modelo não devolveu JSON válido`.
- **Why:** `content` é lista de blocos no LangChain 1.x.
- **Replacement:** `_texto_da_resposta()`. **Não reverter.**

### `gemini-2.5-flash`, `gemini-3.8-flash`, `gemini-flash-latest`
- **Result / Error:** `404 no longer available to new users` e
  `504 DeadlineExceeded`.
- **Replacement:** `gemini-3.5-flash`.

### `models/text-embedding-004`
- **Result / Error:** `404 not found for API version v1beta`.
- **Replacement:** `models/gemini-embedding-001` (3072 dimensões).

### Abrir Railway / No Country pelo navegador interno do Claude
- **Result / Error:** redirecionamento para a tela de login.
- **Why:** o navegador interno é isolado da sessão do usuário.
- **Replacement:** o usuário conduz no próprio navegador (Edge), ou
  login/importação de cookies no painel interno.
- **Do not repeat unless:** a sessão tiver sido estabelecida no painel interno.

### Primeiro diagnóstico do `ImportError` na Streamlit Cloud
- **Result / Error:** atribuí a falha ao conflito de nome entre `ui/app.py` e o
  pacote `app`, e registrei isso na mensagem do commit `4f5a28d`.
- **Why:** o conflito existe de fato e já tinha mordido antes (`c093108`), então
  pareceu a explicação óbvia. A causa real era o cache de módulos da nuvem.
- **Replacement:** conferir qual versão de cada arquivo está realmente rodando
  antes de concluir — a mistura aparece no texto do erro, não no log de deploy.
- **Do not repeat unless:** o erro ocorrer num processo recém-iniciado.

### Leitura do PDF pela ferramenta Read
- **Result / Error:** `pdftoppm is not installed`.
- **Replacement:** texto extraído por script Node; conteúdo preservado aqui.
  Hoje há `pypdf` no venv, então `app/ingestion/loader.py` resolve.

### Heredoc `<<'EOF'` no Bash para escrever arquivos com barras invertidas
- **Result / Error:** barras invertidas duplas reduzidas a simples.
- **Replacement:** escrever arquivos com a ferramenta `Write`.

### Caractere `→` em `print()` no console Windows
- **Result / Error:** `UnicodeEncodeError` com o codec cp1252.
- **Replacement:** `->` em saídas de terminal. `·` é seguro (existe em cp1252).

---

## 10. Relevant Files

| File | Status | Purpose / Important State |
|---|---|---|
| `app/schemas/content.py` | created | Contrato do briefing. **Não renomear campos.** |
| `app/agents/llm.py` | created | Cliente Gemini. Contém `_texto_da_resposta()` — crítico. |
| `app/agents/graph.py` | created | Grafo LangGraph dos 4 agentes + aresta de revisão. |
| `app/agents/fidelity.py` | created | Verificação léxica anti-alucinação com veto. |
| `app/agents/prompts.py` | created | Role prompting + few-shot por formato. |
| `app/rag/` | created | chunking · embeddings · vector_store · retriever. |
| `app/storage/oci_storage.py` | verified | Exercitado contra o OCI real em 17/11: escrita, leitura e URI corretas. |
| `scripts/verificar_oci.py` | created | Diagnóstico da cadeia OCI; para no primeiro elo quebrado. `--criar-bucket` opcional. |
| `app/storage/factory.py` | created | Escolhe o backend por `STORAGE_BACKEND`; avisa ao degradar. |
| `app/pipeline.py` | created | Orquestração de ponta a ponta + diagnóstico. |
| `app/api/main.py` | modified | FastAPI. `GET /saude` mostra os backends; `?profundo=true` também checa o bucket. |
| `ui/app.py` | created | Streamlit com identidade institucional; aba de quiz interativo. |
| `app/export/slides.py` | created | Deck .pptx montado por código, sem template externo. |
| `.streamlit/config.toml` | created | Tema (navy/ouro) alinhado ao deck. |
| `app/core/segredos_nuvem.py` | created | Ponte `st.secrets` -> ambiente na Streamlit Cloud; materializa a credencial OCI se houver seção `[oci]`. Silenciosa fora da nuvem. |
| `.streamlit/secrets.toml.example` | created | Modelo dos segredos da nuvem. **Nunca preencher com valores reais** — o arquivo é versionado. |
| `tests/test_quota.py` | created | Reconhecimento do 429 de cota, com a resposta real de 17/11. |
| `.claude/launch.json` | created | Sobe a interface (8501) e a API (8000) localmente. |
| `scripts/gerar_exemplos.py` | created | Gera os cenários de demonstração (consome quota). |
| `scripts/gerar_pdf_documentacao.py` | created | Refaz `docs/NovaMente_Documentacao.pdf`. |
| `examples/` | created | 4 cenários reais (JSON + Markdown) + `RESUMO.json`. |
| `docs/fontes/` | created | 3 documentos da OCI: `.md`, `.txt` e `.pdf`. |
| `docs/arquitetura.md` | created | Diagramas Mermaid e decisões de projeto. |
| `docs/anotacoes-nocountry.md` | created | Rascunho das anotações a publicar no No Country. |
| `docs/ROTEIRO_VIDEO_DEMO.md` | created | Roteiro do vídeo de demonstração. |
| `docs/exemplos/NovaMente_Apresentacao_Exemplo.pptx` | created | Deck de exemplo gerado pelo sistema. |
| `README.md` | created | Setup do OCI documentado a partir da linha ~335. |
| `.env` | modified pending | **Não versionado.** `STORAGE_BACKEND=local` → virar `oci`. |
| `Dockerfile`, `entrypoint.sh`, `railway.json` | created | Deploy; `SERVICE=ui\|api`. |
| `tests/` | created | 40 testes, sem consumo de quota. |

---

## 11. Technical Context [P1]

### Environment
- **OS:** Windows 11 Pro 10.0.26200 · PowerShell + Bash
- **Python:** 3.13.17 · venv do projeto em `.venv`
- **Navegador do usuário:** **Microsoft Edge** (console da OCI aberto nele)
- **Git:** 2.46.0 · GCM · `main` sincronizada com `origin/main` em `5b8db88`
- **gh:** 2.104.0 em `C:\Program Files\GitHub CLI\gh.exe` (fora do PATH do Bash)
- **OCI CLI:** não instalado · **SDK `oci` 2.191.0 instalado no `.venv`**
- **Docker:** não instalado localmente (a imagem é construída pelo Railway)
- **Pasta dentro do OneDrive:** `.venv/`, `chroma_db/` e `storage_local/` estão
  no `.gitignore` para não sincronizar. **Guarde a chave privada `.pem` do OCI
  fora da pasta do projeto** (ex.: `%USERPROFILE%\.oci\`).

### Versões relevantes instaladas
`fastapi 0.163.0` · `streamlit 1.67.0` · `pydantic 2.14.3` · `langchain 1.5.0` ·
`langgraph 1.2.22` · `langchain-google-genai 4.5.0` · `chromadb 1.5.9` ·
`google-generativeai 0.8.6` · `pypdf 7.1.0` · `oci 2.191.0` · `reportlab 5.1.0`

### Variáveis de ambiente (apenas nomes — nunca valores)
```text
GOOGLE_API_KEY · GEMINI_MODEL · GEMINI_EMBEDDING_MODEL
CHUNK_SIZE · CHUNK_OVERLAP · TOP_K
AGENTE_ROTEADOR_ATIVO · MAX_REVISOES · LIMITE_REVISAO
STORAGE_BACKEND · LOCAL_STORAGE_DIR
OCI_CONFIG_FILE · OCI_PROFILE · OCI_NAMESPACE · OCI_BUCKET_NAME · OCI_REGION
```

### Comandos
```text
.venv\Scripts\python.exe -m pytest tests -q
.venv\Scripts\python.exe -m streamlit run ui/app.py
.venv\Scripts\python.exe -m uvicorn app.api.main:app --reload
.venv\Scripts\python.exe scripts/gerar_exemplos.py 5
"/c/Program Files/GitHub CLI/gh.exe" repo view INASIOCS/Nova_Mente
```

Teste rápido de autenticação do OCI, sem subir a aplicação:
```text
.venv\Scripts\python.exe -c "import oci; c=oci.config.from_file(); oci.config.validate_config(c); print(oci.object_storage.ObjectStorageClient(c).get_namespace().data)"
```

---

## 12. Known Issues / Pitfalls

### Issue: Item 6 — falta a prova pelo pipeline
- **Symptoms:** nenhuma resposta gerada carrega ainda
  `armazenamento_oci.status_upload: "concluido"`. Os exemplos em `examples/`
  são de 15/11 e trazem `"local"`, o que é historicamente correto.
- **Cause:** cota diária do Gemini esgotada em 17/11. CONFIRMED. **Não é
  problema do OCI** — a camada de storage já está verificada.
- **Action:** rodar `scripts/gerar_exemplos.py 5` quando a cota voltar.

### Issue: Cota do Gemini — 5/min e 20/dia
- **Confidence:** CONFIRMED
- **Avoid:** repetir imediatamente um comando que deu 429; a tentativa falha
  consome saldo diário.
- **Action:** esperar ≥60s entre tentativas; modo econômico para gerar ao vivo.
- **Na interface (desde 18/11):** o 429 de cota não vaza mais para a tela. A UI
  reconhece a recusa, explica o limite, calcula o horário de volta a partir do
  `retry_delay` da resposta e oferece um dos materiais de `examples/`. O
  pipeline aborta na primeira recusa, em vez de queimar o resto do saldo.
- **Atenção com o link público:** a cota é do projeto, não por pessoa. Todo
  mundo que abrir <https://nova-mente.streamlit.app> consome o mesmo saldo de
  20/dia.

### Issue: Segredos expostos no chat
- **Confidence:** CONFIRMED
- **Quais:** a `GOOGLE_API_KEY` (em texto, sessões anteriores) e a **chave
  privada da API do OCI** (em captura de tela, 17/11).
- **Current State:** ambas em uso e funcionando; nenhuma está versionada.
- **Action após a entrega:** gerar nova chave no Google AI Studio e revogar a
  antiga; no OCI, *Meu perfil → Tokens e chaves*, excluir a chave de impressão
  digital atual e adicionar outra. Trocar a chave do OCI é barato — basta
  substituir o `.pem` e o `fingerprint` em `~/.oci/config`.

### Issue: `google-generativeai` está descontinuado
- **Symptoms:** `FutureWarning` a cada import (silenciado em `app/__init__.py`).
- **Cause:** o pacote foi substituído por `google-genai`. CONFIRMED.
- **Action:** dívida técnica. Não migrar antes da entrega — o caminho primário é
  o LangChain; este SDK é apenas fallback e para embeddings.

### Issue: Ancoragem naturalmente menor em perfis não técnicos
- **Symptoms:** cenário 4 com 0.73.
- **Cause:** traduzir jargão em linguagem de negócio reduz a sobreposição léxica
  com a fonte. STRONG EVIDENCE.
- **Avoid:** "consertar" baixando o peso do score léxico — isso removeria o sinal
  que protege contra alucinação. Se for ajustar, ajuste o limite por perfil.

---

## 13. Unresolved Questions

- **RESOLVIDO (17/11):** o prazo é **22/11/2026, 23:59**, lido no painel. Não
  houve perda de entrega; restam ~5 dias.
- **RESOLVIDO (17/11):** quem conduz o console web é o **usuário**, no Edge,
  enviando capturas e colando os dados; o agente faz a parte local. Funcionou
  bem para o OCI e é o modelo para o Railway e o No Country.
- **RESOLVIDO (17/11):** os 9 integrantes aparecem no painel (lista no workflow
  da entrega). Falta só decidir **se** e **como** creditá-los no README —
  sobrenomes e papéis não estão todos visíveis, e a escolha é do usuário.

---

## 14. Next Session — Start Here [P0]

### Immediate Objective
Fechar o item 6 com a prova que falta: uma execução do **pipeline completo**
gravando no OCI, com `status_upload: "concluido"` na resposta.

### First Action
Confirme primeiro que o ambiente continua de pé (não consome quota):

```bash
.venv/Scripts/python.exe scripts/verificar_oci.py
```

Deve terminar com exit 0. Então rode o cenário que falta, que também exercita a
ingestão de PDF:

```bash
.venv/Scripts/python.exe scripts/gerar_exemplos.py 5
```

**Antes de rodar, leia o Finding sobre as duas cotas do Gemini.** Se vier 429
com `quota_value: 5`, é o limite por minuto: espere ≥60s. Se vier
`quota_value: 20`, é o diário: só no dia seguinte — **não insista**, cada
tentativa falha consome saldo.

Depois confira, no JSON gerado em `examples/`, que
`resposta.armazenamento_oci.status_upload == "concluido"` e que os objetos
apareceram no balde.

### Em seguida, por ordem de impacto na nota
1. **Vídeo demo** — é o único entregável do No Country que falta (2 de 4), e o
   prazo é 22/11. Roteiro pronto em `docs/ROTEIRO_VIDEO_DEMO.md`. Gravar,
   subir no YouTube e enviar o link no painel, em *Projeto*.
2. Atualizar o item 6 do checklist (seção 6) com a evidência do pipeline.
3. Acrescentar a URL pública <https://nova-mente.streamlit.app> ao entregável
   4 (*Links*) do No Country. O deploy já está no ar; o Railway virou opcional.
4. Opcional: publicar `docs/anotacoes-nocountry.md` no canal `general` do
   Discord da equipe.
5. Após a entrega: rotacionar as duas credenciais expostas (seção 12).

### Constraints
- Preservar as decisões aprovadas da seção 4.
- Não renomear campos do contrato JSON.
- Não trocar o modelo Gemini sem testar — ver seção 6.
- Não reverter `_texto_da_resposta()` em `app/agents/llm.py`.
- Não criar recursos OCI fora da camada **Always Free**.
- Não commitar `.env`, o `~/.oci/config` nem a chave privada `.pem`; guardá-los
  fora da pasta sincronizada do projeto.
- Não "simular" sucesso de upload: o fallback local deve continuar devolvendo
  `status_upload: "local"`.

### Definition of Done
- `scripts/verificar_oci.py` termina com exit 0 — **já atendido em 17/11**.
- `GET /saude?profundo=true` reporta `oci` ativo e bucket acessível, sem aviso —
  **já atendido em 17/11**.
- Uma execução do pipeline grava os dois objetos e retorna
  `"status_upload": "concluido"` — **pendente, só falta cota**.
- `.venv\Scripts\python.exe -m pytest tests -q` continua em 34 passed.
- Os 8 itens do checklist passam a estar verificados.

---

## 15. Handoff Integrity Check

- [x] Estado atual reconciliado: a integração OCI saiu de "implementada, nunca
      executada" para **verificada contra o serviço real**; o que resta do item 6
      é a prova pelo pipeline, bloqueada por cota do Gemini, não pelo OCI.
      Railway e No Country seguem PENDING, dependendo de sessão do usuário.
- [x] Requisitos P0 ativos preservados, com citações literais do usuário.
- [x] Aprovações explícitas registradas; nenhuma inventada.
- [x] Abordagens que falharam retidas com a substituição adotada.
- [x] Arquivos e status conferidos contra o repositório em 17/11.
- [x] Rótulos de evidência usados com precisão — o item 6 do checklist continua
      marcado como **não verificado**; os 33 testes foram reexecutados hoje.
- [x] Próximos passos obsoletos removidos (o passo "redefinir a senha do OCI"
      saiu).
- [x] Nenhum segredo neste documento.
- [x] Próxima ação executável, com critério de sucesso objetivo.
- [x] Contradição de prazo marcada como `[NEEDS CONFIRMATION]`.
