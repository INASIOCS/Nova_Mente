# Arquitetura de Rede VCN para Aplicações Fintech

> No setor financeiro, onde cada milissegundo e cada dado sensível contam, a infraestrutura de rede deve aliar performance, isolamento rigoroso e compliance regulatório. A Virtual Cloud Network (VCN) da Oracle Cloud Infrastructure oferece o modelo de duas sub-redes — pública para entrada controlada e privada para processamento — como padrão de referência para proteger aplicações críticas contra exposição desnecessária.

## Ficha do material

- **Perfil:** Líder Técnico / Arquiteto
- **Formato:** Resumo Executivo
- **Tempo estimado de estudo:** 5 min
- **Conceitos-chave:** Virtual Cloud Network (VCN), Sub-redes Públicas e Privadas, Security Lists, Service Gateway
- **Pré-requisitos:** Conhecimento em redes de computadores (IP, CIDR)
- **Ancoragem na fonte:** 0.72
- **Clareza pedagógica:** Alta

## Conteúdo — Resumo Executivo

### 1. Modelo de Duas Sub-redes

Separa o tráfego de entrada (balanceador de carga) do processamento interno (aplicações e bancos), garantindo que instâncias críticas não tenham endereços IP públicos.

**Impacto:** Minimiza a superfície de ataque e simplifica a auditoria de segurança, atendendo ao princípio de menor privilégio exigido por regulamentações financeiras.

### 2. Service Gateway para Serviços Oracle

Permite acesso privado e direto a serviços como Object Storage, evitando que o tráfego atravesse a internet pública.

**Impacto:** Reduz custos de transferência de dados e melhora latência, além de agregar camada de compliance ao manter dados Oracle dentro de rede privada isolada.

### 3. Security Lists com Princípio do Menor Privilégio

Regras de entrada configuradas para liberar apenas as portas e origências estritamente necessárias para operações de pagamento, conciliação e antifraude.

**Impacto:** Essencial para compliance regulatório e mitigação de riscos; regras bem documentadas evitam permanência de acessos obsoletos que poderiam ser explorados.

### 4. Gateways e Roteamento de Tráfego

Uso de Internet Gateway apenas para sub-redes públicas; NAT Gateway para saída controlada de instâncias privadas; e Service Gateway para serviços Oracle. O roteamento intra-VCN é implícito entre sub-redes.

**Impacto:** Define caminhos claros para fluxo de dados, evitando rotas desnecessárias pela internet e otimizando custos operacionais e de rede.

---

*Observações da auditoria:* O material cumpre bem o perfil de arquitetura e trade-offs, com linguagem técnica apropriada. A única ancoragem fraca está na afirmação de compliance ligada ao Service Gateway, que extrapola o contexto fornecido. Verificação léxica: cobertura léxica de 47%.

*Gerado por NovaMente — Hackathon ONE G10 (Oracle Next Education & Alura).*