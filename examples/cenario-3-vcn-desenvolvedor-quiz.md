# Quiz Técnico: Arquitetura de Redes e VCN na OCI

> Avalie seus conhecimentos práticos sobre o desenho de Virtual Cloud Networks (VCN) na Oracle Cloud Infrastructure. Este quiz valida decisões de arquitetura envolvendo segregação de sub-redes, escolha de gateways de conectividade e políticas de segurança com Security Lists e NSGs.

## Ficha do material

- **Perfil:** Desenvolvedor Júnior / Pleno
- **Formato:** Quiz
- **Tempo estimado de estudo:** 8 min
- **Conceitos-chave:** Virtual Cloud Network (VCN), NAT Gateway vs Service Gateway, Security Lists vs NSGs, Roteamento Implícito em VCN
- **Pré-requisitos:** Conceitos básicos de redes (endereçamento IP, portas e CIDR), Noções gerais de arquitetura de aplicações web
- **Ancoragem na fonte:** 0.82
- **Clareza pedagógica:** Alta

## Conteúdo — Quiz

### 1. Em uma arquitetura de sub-rede privada na OCI, qual componente deve ser configurado para permitir que os servidores baixem atualizações na internet sem expor as instâncias a conexões de entrada não solicitadas?

- [ ] Internet Gateway
- [x] NAT Gateway
- [ ] Service Gateway
- [ ] Local Peering Gateway

*Justificativa:* O NAT Gateway permite que recursos em sub-redes privadas iniciem conexões de saída para a internet (como para atualização de pacotes) mantendo o tráfego de entrada não solicitado bloqueado. O Internet Gateway é bidirecional para sub-redes públicas, o Service Gateway é restrito a serviços Oracle e o Local Peering Gateway conecta VCNs na mesma região.

### 2. Qual é a principal diferença prática de escopo e aplicação entre Security Lists e Network Security Groups (NSGs)?

- [ ] Security Lists aplicam-se às placas de rede virtuais (VNICs), enquanto NSGs valem para toda a sub-rede.
- [ ] Security Lists gerenciam apenas tráfego de saída, enquanto NSGs controlam exclusivamente o tráfego de entrada.
- [x] Security Lists aplicam-se no nível de sub-rede inteira, enquanto NSGs aplicam-se a conjuntos de placas de rede virtuais (VNICs), permitindo regras distintas na mesma sub-rede.
- [ ] NSGs exigem obrigatoriamente a fixação de endereços IP de origem, enquanto Security Lists permitem referenciar outros grupos.

*Justificativa:* As Security Lists aplicam-se a toda a sub-rede. Já os NSGs oferecem controle granular associando regras a conjuntos de placas de rede virtuais (VNICs), permitindo inclusive que um NSG referencie outro como origem sem fixar endereços IP.

### 3. Como funciona o roteamento de tráfego entre duas sub-redes distintas que pertencem à mesma VCN na OCI?

- [ ] O tráfego exige a configuração explícita de uma rota apontando para o Internet Gateway.
- [ ] É necessário criar um Local Peering Gateway para interconectar as sub-redes.
- [x] O roteamento é implícito, ou seja, recursos de sub-redes diferentes da mesma VCN se comunicam sem necessidade de regra explícita.
- [ ] Exige a criação de uma regra sem estado (stateless) na tabela de roteamento da VCN.

*Justificativa:* Na OCI, o roteamento dentro da própria VCN é implícito. Recursos localizados em sub-redes diferentes da mesma VCN se comunicam nativamente sem a necessidade de definir regras explícitas na tabela de roteamento.

### 4. Qual é a vantagem de utilizar o Service Gateway para acessar serviços como o Object Storage a partir de uma VCN?

- [ ] Permite que clientes externos acessem o Object Storage através da sub-rede privada.
- [x] Dá acesso privado a serviços da Oracle sem que o tráfego passe pela internet pública, garantindo segurança e evitando custo de saída de dados.
- [ ] Substitui a necessidade de utilizar tabelas de roteamento na sub-rede privada.
- [ ] Conecta diretamente a VCN ao data center corporativo do cliente via rede privada.

*Justificativa:* O Service Gateway provê acesso privado a serviços da própria Oracle (como o Object Storage) sem trafegar pela internet pública, o que aumenta a segurança e elimina custos de saída de dados.

### 5. Para estabelecer conectividade privada entre uma VCN na OCI e o data center corporativo de uma empresa via VPN IPSec ou FastConnect, qual gateway deve ser utilizado?

- [x] Dynamic Routing Gateway (DRG)
- [ ] Local Peering Gateway (LPG)
- [ ] Internet Gateway
- [ ] NAT Gateway

*Justificativa:* O Dynamic Routing Gateway (DRG) é o componente responsável por conectar a VCN a redes externas privadas, como o data center da empresa (via VPN IPSec ou FastConnect), além de conectar a outras VCNs.

---

*Observações da auditoria:* O quiz está inteiramente baseado nas informações do contexto fornecido, sem qualquer alucinação técnica. As perguntas testam conceitos práticos de redes na OCI com excelente clareza. Verificação léxica: cobertura léxica de 53%; 1 identificador(es) sem respaldo (aplicam-se).

*Gerado por NovaMente — Hackathon ONE G10 (Oracle Next Education & Alura).*