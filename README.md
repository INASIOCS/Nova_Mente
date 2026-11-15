# 🧠 NovaMente

**Sistema Inteligente de Adaptação e Geração de Conteúdo Educacional**

Transforma documentação técnica densa em material didático personalizado —
flashcards, quizzes, tutoriais, resumos executivos e roteiros de aula — ancorado
nas fontes originais via RAG e orquestrado por agentes, com auditoria automática
contra alucinação.

> **Hackathon ONE G10 · Projeto 1** — Oracle Next Education & Alura
> Setor: EdTech / Treinamento Corporativo / Plataformas de Ensino Técnico

---

## O problema

Criar material didático a partir de documentação técnica complexa consome
semanas de especialistas e designers instrucionais. E um mesmo manual de
infraestrutura em nuvem precisa ser ensinado de formas muito diferentes para
quem está dando os primeiros passos em programação e para quem vai tomar
decisões executivas de investimento.

O NovaMente reduz esse ciclo de **semanas para menos de um minuto**, mantendo
fidelidade técnica ao documento de origem.

## O que ele faz

1. **Ingere** documentação técnica em PDF, Markdown ou texto bruto.
2. **Ancora** o conteúdo com um pipeline de RAG: segmentação em chunks,
   embeddings vetoriais e busca por similaridade em Vector Store.
3. **Orquestra quatro agentes** (Roteador → Pesquisador RAG → Redator Pedagógico
   → Crítico/Revisor) em um grafo de decisão com rodada de revisão.
4. **Audita a fidelidade** em duas camadas independentes, incluindo detecção
   determinística de números e identificadores inventados.
5. **Entrega** JSON estruturado, interface interativa e exportação em Markdown,
   PDF didático e CSV compatível com Anki.
6. **Persiste** o documento original e o pacote gerado no **OCI Object Storage**
   (camada Always Free).

### Eixos de parametrização

| Eixo | Valores aceitos |
|---|---|
| **Perfil do destinatário** | Iniciante · Transição de Carreira · Desenvolvedor Júnior / Pleno · Líder Técnico / Arquiteto · Gestor / Executivo (Não Técnico) |
| **Formato pedagógico** | Flashcards · Quiz · Tutorial · Resumo Executivo · Roteiro de Aula |
| **Nicho / contexto** | Fintech · Saúde · E-commerce · Geral |
| **Nível de detalhe** | Didatico · Intermediario · Aprofundado |

---

## Arquitetura

```mermaid
flowchart LR
    A["PDF · Markdown · Texto"] --> B["Ingestão"]
    B --> C["Roteador<br/>plano didático"]
    C --> D["Pesquisador RAG<br/>chunking + embeddings<br/>+ busca vetorial"]
    D --> E["Redator Pedagógico<br/>adapta ao perfil"]
    E --> F["Crítico/Revisor<br/>audita fidelidade"]
    F -->|"score < 0.80"| E
    F -->|aprovado| G["Validação Pydantic"]
    G --> H["JSON estruturado"]
    H --> I["Streamlit · FastAPI"]
    H --> J["Markdown · PDF · Anki"]
    H --> K["OCI Object Storage"]
```

O diagrama completo, o grafo de estados dos agentes e as decisões de projeto
estão em **[docs/arquitetura.md](docs/arquitetura.md)**.

### Mecanismo anti-alucinação

A fidelidade é verificada por dois mecanismos **independentes**, porque um LLM
auditando o próprio texto tende a aprová-lo:

- **Auditoria semântica (LLM):** o Agente Crítico compara cada afirmação com o
  contexto recuperado, sob critérios explícitos de pontuação.
- **Verificação léxica determinística:** mede a cobertura do vocabulário técnico
  na fonte e detecta **números órfãos** e **identificadores órfãos** — valores,
  siglas e comandos citados no material que não existem no documento original.

O score final é `0.65 × score_LLM + 0.35 × score_léxico`, e a camada léxica tem
**poder de veto**: números inventados limitam o resultado a 0.79, e três ou mais
limitam a 0.59, independentemente do que o LLM afirme.

---

## Stack

| Camada | Tecnologia |
|---|---|
| LLM | Google Gemini (`gemini-3.5-flash`) |
| Embeddings | `gemini-embedding-001` (3072 dimensões) |
| Orquestração | LangGraph + LangChain |
| Vector Store | ChromaDB (cosseno) |
| Ingestão de PDF | pypdf |
| Tipagem / validação | Pydantic v2 + pydantic-settings |
| API | FastAPI + Uvicorn |
| Interface | Streamlit |
| Exportação | reportlab (PDF), csv (Anki) |
| Nuvem | OCI Object Storage — camada Always Free |
| Deploy | Railway (Docker) · OCI Compute Always Free |

---

## Instalação

Requer **Python 3.12 ou superior**.

```bash
git clone https://github.com/INASIOCS/Nova_Mente.git
cd Nova_Mente
```

```bash
python -m venv .venv
```

No Windows, ative com `.venv\Scripts\activate`; no Linux ou macOS, com
`source .venv/bin/activate`. Depois:

```bash
pip install -r requirements.txt
```

### Configuração

```bash
cp .env.example .env
```

Edite o `.env` e preencha a `GOOGLE_API_KEY` com uma chave do
[Google AI Studio](https://aistudio.google.com/apikey).

```ini
GOOGLE_API_KEY=sua_chave_aqui
GEMINI_MODEL=gemini-3.5-flash
GEMINI_EMBEDDING_MODEL=models/gemini-embedding-001

CHUNK_SIZE=1200
CHUNK_OVERLAP=150
TOP_K=5

STORAGE_BACKEND=local          # "local" ou "oci"
OCI_BUCKET_NAME=novamente-conteudos-educativos
```

> O arquivo `.env` está no `.gitignore` e **nunca** deve ser commitado.

---

## Como executar

### Interface Streamlit

```bash
python -m streamlit run ui/app.py
```

Abre em `http://localhost:8501`. A interface permite upload de arquivo, colar
texto ou usar um dos documentos de exemplo em `docs/fontes/`, e mostra o rastro
completo do pipeline (chunks indexados, similaridade média, decisões de cada
agente).

### API REST

```bash
python -m uvicorn app.api.main:app --reload
```

Documentação interativa em `http://localhost:8000/docs`.

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/saude` | Diagnóstico de configuração (LLM, storage, bucket) |
| `GET` | `/opcoes` | Valores aceitos em cada eixo de parametrização |
| `POST` | `/adaptar` | **Endpoint principal** — adaptação de conteúdo |
| `POST` | `/adaptar/upload` | Adaptação a partir de upload de arquivo |
| `POST` | `/exportar/markdown` | Converte a resposta em Markdown |
| `POST` | `/exportar/pdf` | Converte a resposta em PDF didático |
| `POST` | `/exportar/csv-anki` | Converte a resposta em CSV para Anki |

### Exemplo de requisição

```bash
curl -X POST http://localhost:8000/adaptar \
  -H "Content-Type: application/json" \
  -d '{
    "documento_titulo": "Introducao a Arquitetura de Redes VCN na OCI",
    "documento_conteudo": "A Virtual Cloud Network (VCN) e uma rede privada e personalizavel configurada na Oracle Cloud Infrastructure. Semelhante a uma rede de data center tradicional, a VCN oferece controle total sobre seu ambiente de rede, incluindo sub-redes publicas e privadas, tabelas de roteamento, Internet Gateways, NAT Gateways e Security Lists para controle de trafego via regras de entrada (ingress) e saida (egress).",
    "perfil_destinatario": "Iniciante",
    "formato_saida": "Flashcards",
    "nicho_setor": "Geral",
    "nivel_detalhe": "Didatico"
  }'
```

### Exemplo de resposta

```json
{
  "status": "sucesso",
  "metadados": {
    "perfil_aplicado": "Iniciante",
    "formato_gerado": "Flashcards",
    "tempo_estimado_estudo_minutos": 5,
    "conceitos_chave": ["VCN", "Sub-redes", "Internet Gateway", "Security Lists"],
    "pre_requisitos": []
  },
  "conteudo_adaptado": {
    "titulo": "Dominando Redes na Nuvem (VCN) do Zero",
    "introducao_contextualizada": "Imagine a VCN como o seu proprio bairro particular e seguro dentro da nuvem da Oracle, onde voce decide quem entra e quem sai.",
    "itens": [
      {
        "frente": "O que e uma VCN na Oracle Cloud?",
        "verso": "E a sua rede virtual privada e personalizada dentro da nuvem da Oracle, funcionando como a infraestrutura de rede da sua empresa.",
        "dica_didatica": "Pense nela como o terreno cercado onde seus servidores moram."
      }
    ]
  },
  "avaliacao_qualidade": {
    "ancoragem_fonte_score": 0.98,
    "clareza_pedagogica": "Alta",
    "observacoes": "Linguagem ajustada com analogias para publico iniciante, sem jargoes excessivos."
  },
  "armazenamento_oci": {
    "bucket": "novamente-conteudos-educativos",
    "objeto_id": "conteudos/vcn-iniciante-flashcards-a1b2c3.json",
    "status_upload": "concluido",
    "backend": "oci",
    "uri": "https://objectstorage.sa-saopaulo-1.oraclecloud.com/n/.../b/novamente-conteudos-educativos/o/..."
  }
}
```

---

## Demonstração

Os cenários de demonstração são gerados por um script e ficam versionados em
[`examples/`](examples/), em JSON (saída estruturada completa, com o rastro do
pipeline) e em Markdown (material pronto para leitura).

```bash
python scripts/gerar_exemplos.py          # todos os cenários
python scripts/gerar_exemplos.py 1 3      # apenas os cenários 1 e 3
```

Os cenários **1, 2 e 3 usam o mesmo documento** (a documentação de VCN da OCI),
adaptado para perfis e formatos diferentes — é a prova direta da capacidade de
adaptação exigida pelo checklist. Os cenários 4 e 5 exercitam os outros dois
formatos de ingestão (texto bruto e PDF).

<!-- RESULTADOS_DEMO -->

### Documentos técnicos de origem

| Arquivo | Formato | Tema |
|---|---|---|
| `docs/fontes/oci_vcn_arquitetura_de_redes.md` | Markdown | VCN, sub-redes, gateways, Security Lists e NSGs |
| `docs/fontes/oci_object_storage_conceitos.txt` | Texto bruto | Buckets, namespace, camadas, PARs e SDK |
| `docs/fontes/oci_iam_identidade_e_politicas.pdf` | PDF | Tenancy, compartimentos, políticas e principais |

---

## Oracle Cloud Infrastructure

### Object Storage (requisito obrigatório)

A persistência fica atrás de uma interface abstrata (`app/storage/base.py`) com
duas implementações selecionadas pela variável `STORAGE_BACKEND`:

- `oci` → **OCI Object Storage**, camada Always Free (produção).
- `local` → disco local, para desenvolvimento sem credenciais.

Para ativar o OCI:

1. No console da OCI, crie um bucket na camada Always Free (nome sugerido:
   `novamente-conteudos-educativos`).
2. Gere um par de chaves de API em *Identity → Users → API Keys* e baixe a
   chave privada.
3. Configure o arquivo `~/.oci/config` com `user`, `tenancy`, `fingerprint`,
   `key_file` e `region`.
4. No `.env`, defina `STORAGE_BACKEND=oci` e ajuste `OCI_BUCKET_NAME` e
   `OCI_REGION`.
5. Confirme com `GET /saude`, que reporta o backend ativo.

Quando a aplicação roda **dentro** da OCI, o código tenta automaticamente
autenticação por **Resource Principal**, dispensando chaves estáticas.

> ⚠️ **Aviso ONE:** o programa é uma iniciativa social 100% gratuita. Use
> **estritamente a camada Always Free** da OCI e evite qualquer configuração que
> possa gerar custo.

### Compute (diferencial)

O `Dockerfile` e o `entrypoint.sh` são agnósticos de plataforma: a mesma imagem
roda no Railway e em uma instância VM Linux Always Free da OCI. A variável
`SERVICE` escolhe o processo:

```bash
docker build -t novamente .
docker run -p 8080:8080 --env-file .env -e SERVICE=ui novamente    # interface
docker run -p 8080:8080 --env-file .env -e SERVICE=api novamente   # API REST
```

---

## Deploy

### Railway

O repositório já contém `Dockerfile` e `railway.json`. No painel do Railway:

1. Crie um projeto a partir deste repositório do GitHub.
2. Defina as variáveis de ambiente: `GOOGLE_API_KEY`, `SERVICE=ui` e, quando o
   OCI estiver configurado, `STORAGE_BACKEND=oci` e as variáveis `OCI_*`.
3. Para expor também a API REST, crie um segundo serviço no mesmo repositório
   com `SERVICE=api` e `healthcheckPath=/saude`.

A porta é lida de `$PORT`, como o Railway exige.

---

## Testes

```bash
pip install -r requirements-dev.txt
```

```bash
python -m pytest tests -v
```

A suíte cobre o contrato de dados (validando o exemplo oficial do briefing), a
segmentação do RAG, a verificação anti-alucinação e os exportadores. **Não
consome quota da API** — exercita apenas a lógica determinística.

---

## Estrutura do projeto

```text
app/
├── core/config.py          Configuração via .env
├── schemas/content.py      Contrato de entrada e saída
├── ingestion/loader.py     PDF, Markdown e texto
├── rag/                    chunking · embeddings · vector_store · retriever
├── agents/                 llm · prompts · fidelity · graph
├── storage/                base · local · oci_storage · factory
├── export/exporters.py     Markdown · PDF · CSV Anki
├── pipeline.py             Orquestração de ponta a ponta
└── api/main.py             FastAPI

ui/app.py                   Interface Streamlit (com quiz interativo)
docs/                       Arquitetura, briefing e documentos de origem
examples/                   Saídas das execuções de demonstração
scripts/                    Geração de exemplos e de PDFs de origem
tests/                      Suíte de testes
```

---

## Checklist de avaliação

| # | Requisito mínimo | Onde está |
|---|---|---|
| 1 | Ingestão de documentos técnicos (PDF, Markdown ou texto) | `app/ingestion/loader.py` · 3 formatos exercitados nos cenários |
| 2 | RAG com chunking, embeddings e busca vetorial | `app/rag/` · ChromaDB + `gemini-embedding-001` |
| 3 | Orquestração com LLM | `app/agents/graph.py` · LangGraph com 4 agentes |
| 4 | Mesmo conteúdo para ≥ 2 perfis e ≥ 2 formatos | Cenários 1, 2 e 3 — mesmo documento de VCN |
| 5 | JSON estruturado + interface interativa ou API REST | `app/schemas/content.py` · Streamlit **e** FastAPI |
| 6 | Integração com OCI Object Storage (Always Free) | `app/storage/oci_storage.py` |
| 7 | ≥ 3 exemplos de execução | `examples/` · 5 cenários |
| 8 | Documentação com diagrama de arquitetura | Este README · [docs/arquitetura.md](docs/arquitetura.md) |

### Diferenciais implementados

- ✅ **Sistema multi-agentes com LangGraph** — Roteador, Pesquisador RAG, Redator
  Pedagógico e Crítico/Revisor, com aresta condicional de revisão.
- ✅ **Quiz com avaliação em tempo real** — aba dedicada no Streamlit, com
  feedback explicativo imediato e placar de desempenho.
- ✅ **Exportação multiformato** — Markdown, PDF didático formatado e CSV
  compatível com Anki.
- ⏳ **Deploy completo em nuvem OCI** — imagem Docker e instruções prontas;
  pendente de execução na instância Compute Always Free.

---

## Equipe

**Grupo 10 — Programa ONE (Oracle Next Education & Alura)**

Formações mapeadas: *Inteligência de Dados e RAG Avançado*, *Oracle Cloud
Infrastructure (OCI)*, *Engenharia de Agentes e Automação* e *Desarrollo y
Orquestación con IA Generativa*.

---

## Licença

Projeto acadêmico desenvolvido para o Hackathon ONE G10.
