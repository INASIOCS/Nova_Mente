# Flashcards Didáticos: Arquitetura de Redes (VCN) na Oracle Cloud

> Seja bem-vindo ao estudo da VCN, a rede privada virtual da Oracle Cloud Infrastructure. Estes flashcards foram criados de forma simples e direta para ajudar você a memorizar os principais componentes de rede sem complicações.

## Ficha do material

- **Perfil:** Iniciante
- **Formato:** Flashcards
- **Tempo estimado de estudo:** 8 min
- **Conceitos-chave:** Virtual Cloud Network (VCN), Sub-redes Públicas e Privadas, Gateways de Rede, Security Lists e NSGs
- **Pré-requisitos:** Noções básicas de computação em nuvem, Conceito básico de endereço IP
- **Ancoragem na fonte:** 0.82
- **Clareza pedagógica:** Alta

## Conteúdo — Flashcards

### 1. O que é uma Virtual Cloud Network (VCN) na Oracle Cloud?

É uma rede privada e personalizável configurada em uma região da Oracle Cloud. Ela funciona como a rede de um data center tradicional, oferecendo controle total sobre o tráfego, endereços de IP e regras de acesso.

*Dica:* Pense na VCN como um terreno cercado e seguro onde você coloca os seus servidores na nuvem.

### 2. Qual a diferença entre uma Sub-rede Pública e uma Sub-rede Privada?

Na sub-rede pública, os recursos podem ter IP público e ser acessados direto da internet. Na sub-rede privada, os recursos não recebem IP público e ficam isolados da internet (ideal para bancos de dados).

*Dica:* A sub-rede pública é a recepção aberta do prédio; a sub-rede privada é o cofre trancado no fundo.

### 3. Para que serve o Internet Gateway?

É o componente de rede que permite a comunicação nos dois sentidos (entrada e saída) entre uma sub-rede pública e a internet.

*Dica:* Ele é a porta de entrada e saída principal que liga sua rede aberta à rua (internet).

### 4. Qual é a função do NAT Gateway em uma sub-rede privada?

Ele permite que os computadores da sub-rede privada iniciem conexões para fora (como baixar atualizações na internet), sem permitir que pessoas de fora iniciem conexões para dentro dela.

*Dica:* Funciona como uma porta de saída de emergência: quem está dentro sai, mas ninguém da rua consegue entrar por ela.

### 5. O que faz o Service Gateway?

Dá acesso privado e seguro a serviços da própria Oracle (como o Object Storage) sem que o tráfego precise passar pela internet pública, evitando custos extras de saída de dados.

*Dica:* É como um corredor interno privado que liga sua sala direto ao depósito da empresa sem precisar sair no meio da rua.

### 6. Qual a diferença entre uma regra de segurança com estado (stateful) e sem estado (stateless)?

Nas regras com estado (stateful), o sistema lembra da conexão e libera a resposta automaticamente. Nas regras sem estado (stateless), você precisa criar manualmente uma regra para o tráfego ir e outra para ele voltar.

*Dica:* Regra com estado é como um ticket de retorno automático; sem estado exige autorização para ir e nova autorização para voltar.

### 7. O que é um Network Security Group (NSG) e como ele se difere da Security List?

A Security List vale para a sub-rede inteira. O NSG permite aplicar regras de segurança diretamente a placas de rede específicas, permitindo que servidores na mesma sub-rede tenham regras diferentes.

*Dica:* A Security List é o crachá para entrar no andar (sub-rede); o NSG é a chave individual para abrir uma mesa específica.

---

*Observações da auditoria:* O material é totalmente ancorado no contexto de origem e utiliza ótimas analogias pedagógicas para o perfil iniciante sem introduzir fatos inventados. Verificação léxica: cobertura léxica de 52%; 1 identificador(es) sem respaldo (bem-vindo).

*Gerado por NovaMente — Hackathon ONE G10 (Oracle Next Education & Alura).*