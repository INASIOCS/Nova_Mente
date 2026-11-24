# Arquitetura de Redes OCI: Entendendo a Virtual Cloud Network

> Imagine que você está montando a infraestrutura da sua empresa em uma nuvem. Assim como um prédio precisa de salas separadas para recepção, escritórios e arquivos, uma rede precisa de organização para separar o que é público do privado. Na Oracle Cloud Infrastructure, isso é feito através da Virtual Cloud Network (VCN), que é a sua rede privada virtual.

## Ficha do material

- **Perfil:** Iniciante
- **Formato:** Flashcards
- **Tempo estimado de estudo:** 5 min
- **Conceitos-chave:** Virtual Cloud Network (VCN), Sub-rede, Security List, Internet Gateway
- **Pré-requisitos:** Noções básicas de rede (IP, CIDR)
- **Ancoragem na fonte:** 0.66
- **Clareza pedagógica:** Alta

## Conteúdo — Flashcards

### 1. O que é uma VCN?

É a sua rede privada e personalizável dentro da Oracle Cloud, semelhante à rede de um data center tradicional. Você define um bloco de endereços (CIDR) que delimita os IPs privados disponíveis para seus recursos.

*Dica:* Pense nela como o terreno cercado onde seus servidores moram, com endereçamento próprio.

### 2. Qual a diferença entre sub-rede pública e privada?

Na sub-rede pública, os recursos recebem IP público e podem ser alcançados diretamente da internet (usando Internet Gateway). Na sub-rede privada, os recursos não têm IP público, sendo ideais para bancos de dados e serviços internos que não devem ser expostos.

*Dica:* Sub-rede pública = loja na rua; sub-rede privada = cofre no porão.

### 3. Para que serve o Internet Gateway?

Permite tráfego bidirecional entre a sub-rede pública e a internet. Só faz sentido ser usado em sub-redes públicas, permitindo que recursos acessem a internet e sejam acessados dela, desde que as regras de segurança permitam.

*Dica:* A porta de entrada da sua rede para o mundo exterior.

### 4. Como funciona o controle de tráfego com Security Lists?

São listas de regras associadas à sub-rede que controlam o que entra (ingress) e sai (egress) dos recursos. Cada regra especifica protocolo, porta e origem/destino. Se a regra tiver "estado", a OCI cuida automaticamente do tráfego de resposta.

*Dica:* É o segurança da sua rede: decide quem entra e quem sai.

### 5. O que faz um NAT Gateway?

Permite que recursos de uma sub-rede privada iniciem conexões de saída para a internet (como baixar atualizações), sem que esses recursos fiquem alcançáveis de fora. O tráfego de entrada não solicitado continua bloqueado.

*Dica:* Permite que o interno saia, mas nada entre sem convite.

---

*Observações da auditoria:* Material apresenta boas analogias e estrutura de flashcards adequada ao perfil iniciante. O score 0.65 reflete pequenas extrapolações de linguagem e a inclusão de uma afirmação que, embora verdadeira no contexto geral da OCI, não tem um parágrafo de apoio direto no texto fornecido (definição de VCN). Verificação léxica: cobertura léxica de 67%.

*Gerado por NovaMente — Hackathon ONE G10 (Oracle Next Education & Alura).*