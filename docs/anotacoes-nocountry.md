# Anotações para o No Country — Grupo 10

**Destino:** canal `general` do Discord da equipe
(`G10-BRASIL-equipo 9`, convite `discord.gg/wbJTXGmTba`).

Em 17/11 confirmamos, com a sessão aberta no painel, que a página
`talent.nocountry.tech/my-simulation/communication` **não tem campo de
publicação** — ela é informativa e aponta para o Discord como espaço de
comunicação da equipe. A entrega formal do projeto fica em *Minha simulação →
Projeto*, e não é aqui que entram anotações de andamento.

Texto preparado para publicação, assinado como Inasio.

---

## Atualização — 17/11/2026

Pessoal, o **NovaMente**, nosso Projeto 1 do Hackathon ONE G10, está completo e
rodando. O repositório está público:

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
- **Exportação**: apresentação `.pptx`, Markdown, PDF didático e CSV compatível
  com Anki.
- **Persistência**: OCI Object Storage na camada Always Free.

### O OCI está ligado de verdade

Essa era a parte que estava em aberto e foi resolvida hoje. O balde
`novamente-conteudos-educativos` está criado na região **Brasil Leste (São
Paulo)**, camada Standard, privado, sem versionamento e sem auto-tiering — tudo
dentro da Always Free, como o edital exige.

A aplicação grava lá os dois artefatos de cada execução: o documento técnico
original, em `originais/`, e o pacote educacional em JSON, em `conteudos/`. Já
há objetos reais no balde, escritos e lidos de volta pela aplicação.

Para quem for configurar o OCI na própria conta, deixei um diagnóstico no
repositório:

```bash
python scripts/verificar_oci.py
```

Ele checa, em ordem, o arquivo de configuração, a credencial, o namespace, o
balde e uma escrita/leitura real, parando no primeiro ponto que falhar e dizendo
o que corrigir. Não imprime segredos.

**Uma armadilha que custou duas tentativas:** no fluxo *Gerar par de chaves de
API* do console, a chave **privada** só pode ser baixada no instante da criação.
Se a janela fechar antes, a chave registrada fica inútil e só resta excluí-la e
criar outra. O caminho mais seguro é gerar o par localmente e usar a opção
*Colar chave pública*, que não depende de download nenhum.

### Resultados das execuções reais

Quatro cenários rodados de ponta a ponta contra a API do Gemini:

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

Sete dos oito requisitos mínimos estão cumpridos e verificados. O oitavo — a
persistência no OCI — tem a infraestrutura verificada, como descrevi acima; o que
falta é apenas uma execução completa registrando o upload na própria resposta,
que eu não consegui fazer hoje porque a cota diária do Gemini acabou. É um
comando quando a cota renovar.

Os três diferenciais também estão implementados: multi-agentes com LangGraph,
quiz interativo com feedback em tempo real e exportação multiformato.

### Dois avisos importantes para a apresentação

1. **A cota do Gemini tem dois limites, não um.** São 20 gerações por dia **e**
   5 por minuto. Uma execução completa dispara 3 chamadas em sequência (5 se
   houver revisão), então ela pode estourar o limite por minuto sozinha. E o
   detalhe que mais atrapalha: **tentativa que falha também consome o saldo
   diário** — repetir o comando logo depois de um erro 429 queima quota à toa.
   Se der erro, esperem pelo menos um minuto antes de tentar de novo.

   Conclusão prática: na apresentação, usemos os exemplos já salvos no
   repositório. Se quisermos uma geração ao vivo, que seja **uma só**, e com o
   modo econômico ligado (`AGENTE_ROTEADOR_ATIVO=false` e `MAX_REVISOES=0`, que
   reduz para 2 chamadas).

2. **Modelo**: nem todo modelo do Gemini está disponível para a nossa chave.
   O que funciona é o `gemini-3.5-flash`. Está documentado no README.

### Como rodar

Está tudo no README, mas em resumo: criar o ambiente virtual, instalar o
`requirements.txt`, copiar o `.env.example` para `.env` com a chave do Google AI
Studio e rodar `streamlit run ui/app.py`. O `.env` **não** vai para o Git.

Sem credencial do OCI o sistema continua funcionando: ele cai para a persistência
local e avisa na interface que o backend obrigatório não foi exercitado — não
finge sucesso.

Quem for mexer no código, dá uma olhada antes no `HANDOFF.md` da raiz: ele tem o
estado atual, as decisões tomadas, o que já falhou e por quê, e o próximo passo.

Qualquer dúvida é só chamar.

— Inasio
