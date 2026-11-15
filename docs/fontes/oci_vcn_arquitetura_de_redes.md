# Arquitetura de Redes na Oracle Cloud Infrastructure: a Virtual Cloud Network (VCN)

## O que é uma VCN

A Virtual Cloud Network (VCN) é uma rede privada e personalizável configurada na
Oracle Cloud Infrastructure. Semelhante a uma rede de data center tradicional, a
VCN oferece controle total sobre o ambiente de rede, incluindo sub-redes públicas
e privadas, tabelas de roteamento, gateways e listas de segurança.

Uma VCN existe dentro de uma única região da OCI, mas abrange todos os domínios
de disponibilidade dessa região. Ao criar a VCN, define-se um bloco de endereços
no formato CIDR (Classless Inter-Domain Routing), que delimita a faixa de
endereços IP privados disponíveis para todos os recursos que serão conectados a
ela. Esse bloco não pode se sobrepor ao de outras redes com as quais a VCN
precise se comunicar, sob pena de conflito de roteamento.

## Sub-redes

A VCN é subdividida em sub-redes. Cada sub-rede recebe um subconjunto do bloco
CIDR da VCN e funciona como uma unidade de organização e de controle de acesso.

Existem dois tipos de sub-rede:

- **Sub-rede pública**: os recursos nela podem receber endereços IP públicos e,
  portanto, ser alcançados diretamente da internet, desde que o roteamento e as
  regras de segurança permitam.
- **Sub-rede privada**: os recursos não recebem endereço IP público. Essa é a
  escolha padrão para bancos de dados, filas e serviços internos que nunca devem
  ser expostos diretamente.

Uma sub-rede pode ser regional (abrangendo toda a região) ou específica de um
domínio de disponibilidade. Sub-redes regionais são a recomendação atual, porque
simplificam o desenho de alta disponibilidade.

## Gateways

Os gateways conectam a VCN ao mundo externo. Cada tipo serve a um propósito
distinto:

- **Internet Gateway**: permite tráfego bidirecional entre a sub-rede pública e
  a internet. Só faz sentido em sub-redes públicas.
- **NAT Gateway**: permite que recursos de uma sub-rede privada iniciem conexões
  de saída para a internet, por exemplo para baixar atualizações de pacotes, sem
  que esses recursos se tornem alcançáveis de fora. O tráfego de entrada não
  solicitado continua bloqueado.
- **Service Gateway**: dá acesso privado a serviços da própria Oracle, como
  Object Storage, sem que o tráfego trafegue pela internet pública. Além do ganho
  de segurança, evita custo de saída de dados.
- **Dynamic Routing Gateway (DRG)**: conecta a VCN a redes externas privadas,
  como o data center da empresa via VPN IPSec ou FastConnect, e também a outras
  VCNs.
- **Local Peering Gateway**: conecta duas VCNs da mesma região diretamente.

## Tabelas de roteamento

Cada sub-rede está associada a uma tabela de roteamento, que contém regras
indicando para qual gateway enviar o tráfego destinado a um determinado bloco
CIDR. O roteamento dentro da própria VCN é implícito: recursos de sub-redes
diferentes da mesma VCN se comunicam sem necessidade de regra explícita.

Uma regra de rota típica de uma sub-rede privada envia todo o tráfego destinado a
0.0.0.0/0 para o NAT Gateway. Em uma sub-rede pública, a mesma rota aponta para o
Internet Gateway.

## Security Lists e Network Security Groups

O controle de tráfego na OCI acontece em duas camadas complementares.

As **Security Lists** são listas de regras associadas à sub-rede. Toda instância
dentro daquela sub-rede herda as mesmas regras. As regras se dividem em:

- **Regras de entrada (ingress)**: definem qual tráfego pode chegar aos recursos.
- **Regras de saída (egress)**: definem qual tráfego pode sair dos recursos.

Cada regra especifica protocolo, porta e origem ou destino. As regras podem ser
com estado (stateful) ou sem estado (stateless). Em uma regra com estado, a OCI
rastreia a conexão e libera automaticamente o tráfego de resposta, o que dispensa
criar uma regra inversa. Em uma regra sem estado, é necessário declarar
explicitamente as duas direções.

Os **Network Security Groups (NSG)** oferecem controle mais granular: em vez de
valer para a sub-rede inteira, as regras se aplicam a um conjunto nomeado de
placas de rede virtuais. Isso permite, por exemplo, que servidores de aplicação e
servidores de banco de dados convivam na mesma sub-rede com regras diferentes. Um
NSG pode referenciar outro NSG como origem, o que elimina a necessidade de fixar
endereços IP nas regras.

Quando uma Security List e um NSG se aplicam ao mesmo recurso, a união das regras
é avaliada: basta que uma delas permita o tráfego para que ele seja aceito.

## Resolução de nomes

A VCN inclui um resolvedor DNS privado. Ao criar a VCN e as sub-redes, é possível
definir rótulos de DNS que compõem nomes de host internos previsíveis, permitindo
que os recursos se encontrem por nome em vez de por endereço IP.

## Padrão de arquitetura de referência

O desenho mais comum para uma aplicação web na OCI usa duas camadas de sub-rede:

1. Uma sub-rede pública regional contendo o balanceador de carga, protegida por
   regras de entrada que liberam apenas as portas 80 e 443.
2. Uma sub-rede privada regional contendo as instâncias de aplicação e o banco de
   dados, com rota de saída pelo NAT Gateway e acesso ao Object Storage pelo
   Service Gateway.

Nesse desenho, nenhuma instância de aplicação tem endereço IP público. O único
ponto de entrada é o balanceador de carga, o que reduz drasticamente a superfície
de exposição e simplifica a auditoria de segurança.

## Boas práticas

- Planeje o bloco CIDR antes de criar a VCN. Alterar o endereçamento depois, com
  recursos em produção, é trabalhoso e arriscado.
- Mantenha bancos de dados sempre em sub-rede privada.
- Prefira Network Security Groups a Security Lists quando precisar de regras
  diferentes para recursos que compartilham a mesma sub-rede.
- Use o Service Gateway para acessar serviços da Oracle, em vez de rotear esse
  tráfego pela internet.
- Aplique o princípio do menor privilégio nas regras de entrada: libere apenas as
  portas e origens estritamente necessárias.
- Documente cada regra de segurança. Uma regra sem justificativa registrada tende
  a permanecer para sempre, mesmo depois de perder a finalidade.
