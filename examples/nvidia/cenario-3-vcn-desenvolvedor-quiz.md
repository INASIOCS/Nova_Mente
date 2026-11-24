# Arquitetura de Redes OCI: VCN, Sub-redes e Segurança

> A Oracle Cloud Infrastructure (OCI) oferece a Virtual Cloud Network (VCN), uma rede privada e personalizável que funciona como um data center virtual. Para desenvolvedores júnior e pleno, entender como segmentar o tráfego com sub-redes e controlar o acesso com listas de segurança é essencial para projetos cloud seguros e escaláveis.

## Ficha do material

- **Perfil:** Desenvolvedor Júnior / Pleno
- **Formato:** Quiz
- **Tempo estimado de estudo:** 5 min
- **Conceitos-chave:** Virtual Cloud Network (VCN), Sub-rede Pública, Sub-rede Privada, Security List
- **Pré-requisitos:** Noções básicas de TCP/IP e endereçamento CIDR
- **Ancoragem na fonte:** 0.84
- **Clareza pedagógica:** Alta

## Conteúdo — Quiz

### 1. Em que componente da OCI as Security List são associadas e aplicam controle de tráfego?

- [ ] a) Na instância de compute individual
- [x] b) Na sub-rede
- [ ] c) No compartment
- [ ] d) No Object Storage

*Justificativa:* As Security List são listas de regras associadas à sub-rede; toda instância dentro dessa sub-rede herda as mesmas regras de ingress e egress, conforme definido na arquitetura de redes da OCI.

### 2. Qual a principal diferença entre uma regra de Security List com estado e uma sem estado?

- [ ] a) A regra com estado bloqueia todo tráfego UDP
- [x] b) A regra com estado rastreia a conexão e libera automaticamente o tráfego de resposta
- [ ] c) A regra sem estado só funciona com IPv6
- [ ] d) Não existe diferença prática entre as duas

*Justificativa:* Em uma regra com estado, a OCI rastreia a conexão e libera o tráfego de resposta automaticamente. Já em uma regra sem estado, é necessário declarar explicitamente as duas direções (entrada e saída).

### 3. No padrão de arquitetura de referência para aplicação web na OCI, qual a função da sub-rede pública?

- [ ] a) Hospedar o banco de dados
- [x] b) Contener o balanceador de carga exposto à internet
- [ ] c) Armazenar backups de objeto
- [ ] d) Isolar as instâncias de aplicação

*Justificativa:* A sub-rede pública regional contém o balanceador de carga, protegido por regras que liberam apenas as portas 80 e 443. As instâncias de aplicação e o banco de dados ficam na sub-rede privada, sem endereço IP público.

### 4. Para acessar serviços da Oracle (como o Object Storage) sem rotear tráfego pela internet, qual recurso da OCI deve ser utilizado?

- [ ] a) Internet Gateway
- [ ] b) NAT Gateway
- [x] c) Service Gateway
- [ ] d) Dynamic Gateway

*Justificativa:* O Service Gateway permite acessar serviços da Oracle diretamente da VCN, reduzindo a superfície de exposição em vez de rotear o tráfego pela internet. O NAT Gateway serve para saída de instâncias privadas para a internet.

### 5. Qual boas prática recomendada para o planejamento inicial de uma VCN?

- [ ] a) Criar a VCN primeiro e ajustar o CIDR depois
- [x] b) Planejar o bloco CIDR antes de criar a VCN, pois alterar depois é trabalhoso
- [ ] c) Usar blocos CIDR /0 para máxima flexibilidade
- [ ] d) Evitar sub-redes privadas para simplificar o roteamento

*Justificativa:* As boas práticas da OCI recomendam planejar o bloco CIDR antes de criar a VCN, pois alterar o endereçamento depois, com recursos em produção, é trabalhoso e arriscado.

---

*Observações da auditoria:* Material tecnicamente fiel ao contexto OCI. Todas as afirmações (Security List por sub-rede, regras stateful/stateless, padrão de 2 sub-redes, Service Gateway) são rastreáveis nas fontes. O quiz está alinhado ao perfil de desenvolvedor júnior/pleno, com linguagem direta e sem simplificações excessivas. Verificação léxica: cobertura léxica de 64%.

*Gerado por NovaMente — Hackathon ONE G10 (Oracle Next Education & Alura).*