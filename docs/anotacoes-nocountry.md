# Anotações para o No Country — Grupo 10

Página: https://talent.nocountry.tech/my-simulation/communication

Texto preparado para publicação, assinado como Inasio.

---

## Atualização — 15/11/2026

Pessoal, subi a primeira versão completa do **NovaMente**, nosso Projeto 1 do
Hackathon ONE G10. O repositório está público:

**https://github.com/INASIOCS/Nova_Mente**

### O que o sistema faz

Ele recebe uma documentação técnica (PDF, Markdown ou texto), ancora o conteúdo
nos trechos reais do documento usando RAG e gera material didático adaptado a um
perfil e a um formato pedagógico. O mesmo manual vira flashcards para iniciante,
resumo executivo para gestor ou quiz para desenvolvedor.

### Como está a arquitetura

- **Ingestão**: PDF (pypdf), Markdown e texto bruto.
- **RAG**: segmentação em chunks com sobreposição, embeddings com
  `gemini-embedding-001` e busca vetorial no ChromaDB.
- **Orquestração**: um grafo LangGraph com quatro agentes — Roteador,
  Pesquisador RAG, Redator Pedagógico e Crítico/Revisor. O Crítico pode devolver
  o material para uma rodada de revisão quando a ancoragem na fonte fica baixa.
- **Anti-alucinação**: além da auditoria do LLM, há uma verificação léxica
  determinística que detecta números e identificadores citados no material mas
  ausentes do documento original. Essa camada tem poder de veto sobre o score,
  porque um LLM auditando o próprio texto tende a se aprovar.
- **Saída**: JSON estruturado no contrato exato do briefing, interface Streamlit
  e API REST em FastAPI.
- **Exportação**: Markdown, PDF didático e CSV compatível com Anki.
- **Persistência**: OCI Object Storage na camada Always Free.

### Resultados das execuções reais

Rodei quatro cenários de ponta a ponta contra a API do Gemini:

| Cenário | Documento | Perfil | Formato | Ancoragem |
|---|---|---|---|---|
| 1 | VCN (Markdown) | Iniciante | Flashcards | 0.82 |
| 2 | VCN (Markdown) | Líder Técnico / Arquiteto | Resumo Executivo | 0.81 |
| 3 | VCN (Markdown) | Desenvolvedor Júnior / Pleno | Quiz | 0.82 |
| 4 | Object Storage (texto) | Gestor / Executivo | Resumo Executivo | 0.73 |

Os três primeiros usam **o mesmo documento**, o que é exatamente o requisito do
checklist: provar a adaptação para perfis e formatos diferentes. As saídas
completas estão versionadas em `examples/`, em JSON e em Markdown.

O cenário 4 ficou com 0.73 e disparou a rodada de revisão automaticamente. Faz
sentido: um resumo para público executivo traduz jargão técnico em linguagem de
negócio, então a sobreposição com a fonte cai naturalmente. O mecanismo sinalizou
em vez de mascarar.

### Status do checklist

Sete dos oito requisitos mínimos estão cumpridos e verificados. O que falta é a
**execução real contra o OCI Object Storage** — o código está pronto e testado,
mas eu ainda estou redefinindo a senha do OCI. Assim que entrar no console, crio
o bucket na camada Always Free e valido.

Os três diferenciais também estão implementados: multi-agentes com LangGraph,
quiz interativo com feedback em tempo real e exportação multiformato.

### Dois avisos importantes para a apresentação

1. **Cota do Gemini**: o free tier permite cerca de 20 gerações por dia. Cada
   execução consome 3 chamadas, ou 5 se houver revisão. Isso dá umas 6
   demonstrações ao vivo por dia. Sugiro usarmos os exemplos já salvos no
   repositório e deixarmos no máximo uma geração ao vivo.
2. **Modelo**: nem todo modelo do Gemini está disponível para a nossa chave.
   O que funciona é o `gemini-3.5-flash`. Está documentado no README.

### Como rodar

Está tudo no README, mas em resumo: criar o ambiente virtual, instalar o
`requirements.txt`, copiar o `.env.example` para `.env` com a chave do Google AI
Studio e rodar `streamlit run ui/app.py`.

Quem for mexer no código, dá uma olhada antes no `HANDOFF.md` da raiz: ele tem o
estado atual, as decisões tomadas, o que já falhou e por quê, e o próximo passo.

Qualquer dúvida é só chamar.

— Inasio
