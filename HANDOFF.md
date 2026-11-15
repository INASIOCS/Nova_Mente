# Project Handoff — NovaMente

**Last Updated:** 2026-11-15 (horário local do sistema, Windows)
**Status:** ACTIVE — MVP funcional, testado e publicado no GitHub; faltam deploy e anotações
**Project:** NovaMente — Sistema Inteligente de Adaptação e Geração de Conteúdo Educacional
**Contexto:** Hackathon ONE G10 — Projeto 1 — Oracle Next Education & Alura
**Project Root:** `C:\Users\inasio\OneDrive\Área de Trabalho\Projeto_Nova_Mente`
**Repositório:** https://github.com/INASIOCS/Nova_Mente (público, branch `main`)
**Prazo de entrega:** segunda-feira, 16/11/2026

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

### Evidence Summary

- **IMPLEMENTED:** pipeline completo — ingestão (PDF/MD/texto), RAG (chunking,
  embeddings Gemini, ChromaDB), orquestração LangGraph com 4 agentes,
  verificação anti-alucinação em 2 camadas, validação Pydantic estrita,
  storage abstraído (local + OCI), FastAPI, Streamlit com quiz interativo,
  exportação Markdown/PDF/CSV-Anki, Docker e configuração Railway.
- **TESTED:** 29 testes automatizados passando (`python -m pytest tests -q`);
  `compileall` sem erros; 4 cenários de demonstração executados de ponta a ponta
  contra a API real.
- **VERIFIED:** material do cenário 1 inspecionado manualmente — tecnicamente
  correto e adequado ao perfil iniciante. Chave do Gemini validada. Modelos
  disponíveis confirmados por `list_models`. `.env` confirmado fora do Git.
- **APPROVED:** as 6 decisões da seção 4 foram escolhidas explicitamente pelo
  usuário.

### O que NÃO está feito

- Deploy no Railway (bloqueado — ver Workflow correspondente).
- Anotações no No Country (bloqueado — mesmo motivo).
- Integração OCI Object Storage **nunca foi executada contra o serviço real**:
  o código existe e está completo, mas a senha do OCI ainda não foi redefinida.
- Cenário 5 de demonstração (ingestão de PDF → Tutorial) não gerado: cota diária
  da API do Gemini esgotada.

---

## 3. Active Workflows

### Workflow: Núcleo da aplicação
**Status:** COMPLETED

Todo o pipeline está implementado, testado e commitado. Nada pendente.

**Validação executada**
- `python -m pytest tests -q` → 29 passed.
- `python scripts/gerar_exemplos.py` → 4 de 5 cenários concluídos.

---

### Workflow: Integração OCI Object Storage (OBRIGATÓRIO)
**Status:** BLOCKED

**Blocker**
- O usuário recuperou o acesso ao OCI mas **ainda não redefiniu a senha**. Sem o
  console não há como criar o bucket nem gerar o par de chaves de API.

**Completed**
- `app/storage/oci_storage.py` implementado: autenticação por arquivo de
  configuração ou Resource Principal, `put_object`, criação de bucket, montagem
  da URI e tratamento de falha sem derrubar o pipeline.
- `app/storage/factory.py` seleciona o backend por `STORAGE_BACKEND` e devolve
  um aviso explícito quando degrada para o local.

**Pending**
1. Redefinir a senha do OCI e entrar no console.
2. Criar o bucket `novamente-conteudos-educativos` na camada Always Free.
3. Gerar o par de chaves de API e configurar `~/.oci/config`.
4. No `.env`, definir `STORAGE_BACKEND=oci` e ajustar `OCI_NAMESPACE`,
   `OCI_REGION` e `OCI_BUCKET_NAME`.
5. Validar com `GET /saude` e uma execução real.

**Validation / Success Criteria**
- `GET /saude` retorna `"storage_backend_ativo": "oci"` e nenhum
  `aviso_storage`.
- Uma execução grava os dois objetos (`originais/...` e `conteudos/....json`) e
  a resposta traz `"status_upload": "concluido"` — hoje retorna `"local"`.

---

### Workflow: Deploy no Railway
**Status:** BLOCKED

**Completed**
- `Dockerfile` (imagem única, `SERVICE=ui|api`, porta de `$PORT`),
  `entrypoint.sh`, `railway.json` e `.dockerignore` commitados.

**Blocker**
- O navegador interno do Claude **não está autenticado** no Railway nem no No
  Country: ele é isolado do Chrome do usuário. Ambas as URLs redirecionaram
  para a tela de login.
- Além disso, por regra de segurança o agente **não digita chaves de API em
  formulários de serviços externos**. A variável `GOOGLE_API_KEY` precisa ser
  inserida pelo próprio usuário no painel do Railway.

**Pending**
1. No painel do Railway, criar projeto a partir de `INASIOCS/Nova_Mente`.
2. Definir variáveis: `GOOGLE_API_KEY` (pelo usuário), `SERVICE=ui`,
   `GEMINI_MODEL=gemini-3.5-flash`,
   `GEMINI_EMBEDDING_MODEL=models/gemini-embedding-001`.
3. Opcional: segundo serviço no mesmo repositório com `SERVICE=api` e
   `healthcheckPath=/saude`.

**Validation / Success Criteria**
- A URL pública abre a interface Streamlit e gera um material com sucesso.

---

### Workflow: Anotações no No Country
**Status:** BLOCKED

- Página: https://talent.nocountry.tech/my-simulation/communication
- O usuário autorizou publicar diretamente, assinando como ele: *"Você pode
  publicar direto, faça os comentários como eu Inasio."*
- Bloqueado pelo mesmo motivo do Railway: sessão não disponível no navegador
  interno.

---

### Workflow: Cenário 5 de demonstração
**Status:** PENDING

- Falhou com `429` — cota diária do free tier esgotada (~20 gerações/dia).
- Com a cota renovada: `python scripts/gerar_exemplos.py 5`.
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

---

## 5. User Instructions [P0]

### Requirements
- *"é um projeto que tem um PDF que você precisa ler, cria ele na pasta e depois
  subir para o GIT"* — **FEITO**.
- *"https://talent.nocountry.tech/my-simulation/communication que é a pagina onde
  devemos ir colocando lá todas as anotações"* — **PENDENTE**.
- Prazo: *"Até Segunda-feira 16/11/2026"*.
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
| 6 | OCI Object Storage (Always Free) | ⚠️ implementado, **nunca executado de verdade** |
| 7 | ≥3 exemplos de execução | ✅ 4 versionados em `examples/` |
| 8 | Documentação com diagrama de arquitetura | ✅ README + `docs/arquitetura.md` (Mermaid) |

**O item 6 é o único risco real da entrega.**

### Finding: Cota do free tier do Gemini é o gargalo operacional
- **Finding:** o free tier permite ~**20 requisições de geração por dia, por
  modelo**. Cada execução consome 3 chamadas (Roteador, Redator, Crítico) e 5 se
  houver rodada de revisão.
- **Evidence:** erro `429` no cenário 5, com `quota_value: 20` e
  `retry_delay: 14999s` (~4h10m a partir de ~00:50 de 15/11/2026).
- **Impact:** cerca de **6 demonstrações ao vivo por dia**. Na apresentação,
  prefira os exemplos já versionados; para gerar ao vivo, use o modo econômico
  (`AGENTE_ROTEADOR_ATIVO=false`, `MAX_REVISOES=0` → 2 chamadas).
- **Confidence:** CONFIRMED

### Finding: Nem todo modelo Gemini está disponível para esta chave
- **Finding:** `gemini-2.5-flash` responde *"no longer available to new users"*;
  `gemini-3.8-flash` e `gemini-flash-latest` devolvem `504 DeadlineExceeded`.
  **`gemini-3.5-flash` funciona** e é o modelo em uso. O embedding
  `text-embedding-004` não existe mais; **`gemini-embedding-001`** funciona
  (3072 dimensões).
- **Impact:** não troque o modelo sem testar. O erro de cota reporta
  `gemini-3.6-flash`, sugerindo que `gemini-3.5-flash` é roteado internamente.
- **Confidence:** CONFIRMED (testado nesta sessão)

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

### Finding: `python` funciona agora nesta máquina
- Python 3.13.17; `python`, `py` e `python3` todos funcionam. O venv do projeto
  está em `.venv`.
- **Confidence:** CONFIRMED

### Finding: `gh` existe mas não está no PATH do Bash
- `gh` 2.104.0 em `C:\Program Files\GitHub CLI\gh.exe`, autenticado como
  **INASIOCS** com escopos `gist, read:org, repo, workflow`. Invoque pelo
  caminho completo no Bash.
- **Confidence:** CONFIRMED

### Finding: O navegador interno do Claude é isolado do Chrome do usuário
- Railway e No Country redirecionaram para login no navegador interno, embora o
  usuário esteja logado no próprio Chrome.
- **Impact:** esses dois passos exigem o Chrome do usuário (Claude in Chrome) ou
  login/importação de cookies no painel interno.
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

### Teste que revelou defeito real na métrica de fidelidade
- **Result:** as chaves do JSON eram contadas como vocabulário técnico,
  deprimindo a cobertura. Corrigido para percorrer apenas os valores.
- **Evidence:** TESTED — `test_material_ancorado_tem_score_alto`.

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

### Leitura do PDF pela ferramenta Read
- **Result / Error:** `pdftoppm is not installed`.
- **Replacement:** texto extraído por script Node; conteúdo preservado aqui.
  Hoje há `pypdf` no venv, então `app/ingestion/loader.py` resolve.

### Heredoc `<<'EOF'` no Bash para escrever JavaScript
- **Result / Error:** barras invertidas duplas reduzidas a simples.
- **Replacement:** escrever arquivos de código com a ferramenta `Write`.

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
| `app/storage/oci_storage.py` | created | **Nunca executado contra o OCI real.** |
| `app/pipeline.py` | created | Orquestração de ponta a ponta + diagnóstico. |
| `app/api/main.py` | created | FastAPI. `GET /saude` mostra os backends ativos. |
| `ui/app.py` | created | Streamlit, inclui a aba de quiz interativo. |
| `examples/` | created | 4 cenários reais (JSON + Markdown) + `RESUMO.json`. |
| `docs/fontes/` | created | 3 documentos da OCI: `.md`, `.txt` e `.pdf`. |
| `docs/arquitetura.md` | created | Diagramas Mermaid e decisões de projeto. |
| `.env` | created | **Não versionado.** Contém a `GOOGLE_API_KEY`. |
| `Dockerfile`, `entrypoint.sh`, `railway.json` | created | Deploy; `SERVICE=ui\|api`. |
| `tests/` | created | 29 testes, sem consumo de quota. |

---

## 11. Technical Context [P1]

### Environment
- **OS:** Windows 11 Pro 10.0.26200 · PowerShell + Bash
- **Python:** 3.13.17 · venv do projeto em `.venv`
- **Node:** v22.20.0 (usado só para extrair o PDF do briefing)
- **Git:** 2.46.0 · GCM · remoto `origin` configurado
- **gh:** 2.104.0 em `C:\Program Files\GitHub CLI\gh.exe` (fora do PATH do Bash)
- **Docker:** não instalado localmente (a imagem é construída pelo Railway)
- **Pasta dentro do OneDrive:** `.venv/`, `chroma_db/` e `storage_local/` estão
  no `.gitignore` para não sincronizar.

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

---

## 12. Known Issues / Pitfalls

### Issue: Cota diária do Gemini (~20 gerações/dia)
- **Confidence:** CONFIRMED
- **Avoid:** gerar vários cenários ao vivo em sequência.
- **Action:** usar `examples/` na apresentação; modo econômico se precisar gerar.

### Issue: Item 6 do checklist não exercitado
- **Symptoms:** `armazenamento_oci.status_upload` retorna `"local"`.
- **Cause:** sem credenciais OCI. CONFIRMED.
- **Action:** é a prioridade número um antes da entrega.

### Issue: A chave do Gemini foi exposta em texto aberto no chat
- **Confidence:** CONFIRMED
- **Action:** revogar e gerar nova chave no Google AI Studio após a
  apresentação. Ela está só no `.env` local, que não é versionado.

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

- **[NEEDS CONFIRMATION]** Como executar os passos que exigem sessão
  autenticada (Railway e No Country): usar o Chrome do usuário via Claude in
  Chrome, fazer login no navegador interno, ou o próprio usuário executa?
- **[NEEDS CONFIRMATION]** Nomes dos demais integrantes do Grupo 10, para
  creditar no README.

---

## 14. Next Session — Start Here [P0]

### Immediate Objective
Fechar o item 6 do checklist: executar a integração real com o OCI Object
Storage. É o único requisito obrigatório ainda não exercitado.

### First Action
1. Redefinir a senha do OCI e entrar no console.
2. Criar o bucket `novamente-conteudos-educativos` na camada **Always Free**.
3. Gerar o par de chaves de API e montar `~/.oci/config`.
4. No `.env`: `STORAGE_BACKEND=oci`, `OCI_NAMESPACE`, `OCI_REGION`.
5. Validar:

```bash
.venv\Scripts\python.exe -m uvicorn app.api.main:app --reload
```

Confirme que `GET /saude` retorna `"storage_backend_ativo": "oci"` sem aviso.
Depois rode um cenário e verifique `"status_upload": "concluido"`.

### Em seguida
- Deploy no Railway (a `GOOGLE_API_KEY` deve ser inserida pelo usuário).
- Publicar as anotações no No Country, assinando como Inasio.
- Com a cota renovada: `python scripts/gerar_exemplos.py 5`.

### Constraints
- Preservar as decisões aprovadas da seção 4.
- Não renomear campos do contrato JSON.
- Não trocar o modelo Gemini sem testar — ver seção 6.
- Não reverter `_texto_da_resposta()` em `app/agents/llm.py`.
- Não criar recursos OCI fora da camada Always Free.
- Não commitar `.env`.

### Definition of Done
- `GET /saude` reporta o backend `oci` ativo.
- Uma execução grava os dois objetos no bucket e retorna
  `"status_upload": "concluido"`.
- Os 8 itens do checklist passam a estar verificados.

---

## 15. Handoff Integrity Check

- [x] Estado atual reconciliado com o handoff anterior (bloqueios do OCI, do
      `gh` e da chave do Gemini resolvidos ou atualizados).
- [x] Requisitos P0 ativos preservados, com citações literais do usuário.
- [x] Aprovações explícitas registradas; nenhuma inventada.
- [x] Abordagens que falharam retidas com a substituição adotada.
- [x] Arquivos e status conferidos contra o repositório.
- [x] Rótulos de evidência usados com precisão — o item 6 do checklist continua
      marcado como **não verificado**.
- [x] Próximos passos obsoletos do handoff anterior removidos.
- [x] Nenhum segredo neste documento.
- [x] Próxima ação executável, com critério de sucesso objetivo.
