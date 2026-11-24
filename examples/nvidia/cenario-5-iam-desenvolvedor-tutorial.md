# Desvendando o IAM da OCI: Controle de Acesso Seguro

> O Identity and Access Management (IAM) da Oracle Cloud Infrastructure é o serviço fundamental que define quem pode fazer o quê dentro da sua tenancy. Assim como um prédio tem andares e chaves de acesso, a OCI usa tenancies, compartimentos e políticas para garantir que recursos críticos permaneçam protegidos contra acessos não autorizados.

## Ficha do material

- **Perfil:** Desenvolvedor Júnior / Pleno
- **Formato:** Tutorial
- **Tempo estimado de estudo:** 7 min
- **Conceitos-chave:** Tenancy, Compartimento, Política IAM, Grupo de Usuários
- **Pré-requisitos:** Noções básicas de computação na nuvem
- **Ancoragem na fonte:** 0.55
- **Clareza pedagógica:** Média

## Conteúdo — Tutorial

### Passo 1 — Entenda a estrutura hierárquica da OCI

Comece compreendendo que a Tenancy é a conta raiz da organização. Dentro dela, os Compartimentos funcionam como divisórias que organizam recursos e, crucialmente, herdam políticas. Uma política escrita no compartimento raiz se aplica a todos os recursos descendentes, o que torna o gerenciamento hierárquico poderoso, mas propenso a excessos se não for cuidadoso.

### Passo 2 — Domine o modelo exclusivamente permissivo

Lembre-se de que, na OCI, nada é autorizado por padrão. A ausência de uma política que permita uma ação significa que ela está proibida. O serviço avalia as políticas de forma exclusiva permissiva, o que simplifica o raciocínio: não há declarações de negação para conflitar com permissões, tornando o modelo mais direto, mas exigindo atenção para não deixar lacunas de segurança.

### Passo 3 — Sempre escreva políticas para grupos, nunca para usuários

Esta é a regra de ouro do IAM. Conceder permissão a um usuário individual cria um privilégio invisível que ninguém revisa e que sobrevive à saída dessa pessoa da equipe. Agrupe usuários logicamente e escreva políticas para esses grupos. Se um usuário sair, basta removê-lo do grupo; a política continua válida para quem permanecer.

### Passo 4 — Utilize Grupos Dinâmicos para automação

Aproveite os grupos dinâmicos, onde a participação se ajusta automaticamente baseada nos recursos. As políticas escritas para esses grupos passam a valer automaticamente para novos recursos, sem intervenção manual. Isso é ideal para aplicações que sobem e descem dinamicamente, garantindo que tenham as permissões necessárias desde o lançamento.

### Passo 5 — Aplique o Princípio do Menor Privilégio

Comece pelo verbo de menor privilégio (inspeção) e aumente apenas quando algo falhar por falta de permissão. Os verbos formam uma escada: inspeção -> leitura -> uso -> gerência. Escolher o verbo mínimo suficiente é a aplicação prática do menor privilégio, evitando que permissões amplas se acumulem no compartimento raiz por conveniência de testes.

### Passo 6 — Evite criar recursos no compartimento raiz

Não crie recursos operacionais no compartimento raiz em ambientes reais. O excesso de privilégio costuma se acumular ali. Separe ambientes (desenvolvimento, teste, produção) em compartimentos distintos para que um erro ou acesso amplo em desenvolvimento não alcance produção.

### Passo 7 — Prefira Identidades de Serviço sobre Chaves de API

Para aplicações que rodam dentro da OCI, prefira Instance Principal e Resource Principal. Eles eliminam a necessidade de chaves de API estáticas, que precisam ser guardadas, rotacionadas periodicamente e revogadas em caso de incidente. As identidades de serviço permitem que máquinas tenham identidade própria de forma mais segura e gerenciável.

### Passo 8 — Exija Autenticação Multifator (MFA) para contas de gerência

Para contas com permissão de gerência, exija sempre a autenticação multifator. Isso adiciona uma camada crítica de segurança, garantindo que, mesmo se uma senha for comprometida, o acesso não autorizado de alto nível seja bloqueado.

---

*Observações da auditoria:* O material apresenta boa estrutura tutorial e abrange os conceitos centrais (hierarquia, modelo permissivo, grupos vs usuários, menor privilégio, MFA). No entanto, há generalizações arriscadas (itens sobre 'privilegio invisível' e 'validação automática' sem especificar grupos dinâmicos específicos) e o item 8 cita 'comune' em vez de 'comando', indicando pequeno erro de digitação/consistência no conteúdo gerado. A ancoragem em fontes cai para 0.55 devido a essas extrapolações de linguagem e falta de confirmação direta de alguns 'fatos' pedagógicos no contexto bruto. Verificação léxica: cobertura léxica de 56%.

*Gerado por NovaMente — Hackathon ONE G10 (Oracle Next Education & Alura).*