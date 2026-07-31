# Arquitetura

Este documento descreve a organização da estrutura atual e o papel de cada
área do repositório.

## Princípio adotado

O projeto segue uma organização orientada por domínio de aplicação, com um
monolito Django na raiz e isolamento explícito das integrações externas.

Na prática, isso significa:

- `core` concentra a infraestrutura compartilhada do projeto;
- cada domínio possui seu próprio app Django;
- integrações externas ficam separadas em `apps/integracoes/`;
- configuração, runtime e documentação não disputam responsabilidade com os
  apps de domínio.

## Estrutura principal

```text
.
|-- apps/
|   |-- core/
|   |-- edicoes/
|   |-- polos/
|   `-- integracoes/
|       |-- coresso/
|       `-- eol/
|-- config/
|-- docs/
|-- requirements/
|-- scripts/
`-- testes/
```

## Responsabilidades por área

### Visão resumida

| Área | Papel no projeto |
| --- | --- |
| `apps/core/` | infraestrutura compartilhada, modelos base, usuário customizado, healthcheck e componentes iniciais de autenticação |
| `apps/edicoes/` | estrutura inicial do domínio de edições |
| `apps/polos/` | estrutura inicial do domínio de polos |
| `apps/integracoes/coresso/` | contrato e stub da integração CoreSSO |
| `apps/integracoes/eol/` | contrato e stub da integração EOL |
| `config/` | settings, URLs, ASGI e WSGI |
| `scripts/` | entrypoints e bootstrap dos containers |
| `requirements/` | dependências separadas por ambiente |
| `docs/` | documentação operacional e estrutural |
| `testes/` | espaço reservado para suítes E2E, smoke ou BDD |

### `apps/core/`

Infraestrutura compartilhada do projeto, modelos base, usuário customizado,
healthcheck e componentes iniciais de autenticação.

O `core` existe para evitar duplicação do que é transversal ao sistema. Nesta
etapa ele concentra o que precisa estar pronto desde o primeiro dia, sem tentar
resolver antecipadamente regras de negócio que pertencem a outros apps.

Também fica em `core` o tratamento centralizado de exceções REST em
`exception_handler.py`, responsável por traduzir respostas padrão do DRF para
pt-BR nos cenários comuns de autenticação, permissão e validação de request.

A organização de autenticação foi simplificada em cinco pontos centrais:

- `apps/core/services/auth_service.py` concentra o fluxo de login, resolução
  de token, logout e helpers diretamente ligados à autenticação;
- `apps/core/authentication.py` concentra a integração DRF da autenticação por
  token;
- `apps/core/api/serializers/auth_serializer.py` concentra o contrato HTTP do
  login;
- `apps/core/api/views/auth.py` concentra o contrato HTTP do login e do
  logout;
- `apps/core/models/identidade.py` concentra os modelos locais ligados a
  identidade e auditoria (`Usuario`, `CargoPermitido` e `LogLogin`).

### `apps/edicoes/` e `apps/polos/`

Apps de domínio do projeto. No estado atual, a estrutura existe, mas as regras
de negócio e os modelos ORM concretos ainda não foram implementados.

Esses apps já possuem `api/`, `models/`, `services/`, testes e `migrations`
para que a evolução posterior aconteça sem reorganização estrutural.

Arquivos como `admin.py` e `repository.py` deixam de fazer parte da estrutura
padrão e passam a existir apenas sob demanda.

### `apps/integracoes/coresso/` e `apps/integracoes/eol/`

Estruturas iniciais das integrações externas em formato hexagonal, com
contratos e stubs preparados para evolução futura.

O objetivo aqui é separar desde cedo a borda com sistemas externos. Mesmo sem
HTTP real nesta etapa, a árvore já deixa explícito onde ficam contrato,
adaptador, client e exceções da integração.

### `config/`

Configuração central do Django, incluindo settings, ASGI, WSGI e URLs.

Essa pasta governa o comportamento da aplicação inteira e não deve receber
regra de negócio de domínio.

### `requirements/`

Dependências separadas por ambiente.

- `base.txt` concentra o runtime comum
- `local.txt` adiciona dependências de desenvolvimento, testes, docs e tipagem
- `production.txt` mantém o runtime enxuto da imagem final

### `scripts/`

Entrypoints usados pelos containers de desenvolvimento e produção.

Os scripts controlam detalhes de bootstrap, como migrations no startup,
escolha do comando final e execução de Gunicorn no runtime de produção.

### `docs/`

Documentação navegável do projeto, gerada com Sphinx.

Ela complementa o `README.md` com guias mais estruturados de início,
configuração e arquitetura.

### `testes/`

Espaço reservado para suítes E2E, smoke ou BDD quando essas camadas entrarem
no escopo.

## Regras de dependência

Para a estrutura continuar coerente nas próximas evoluções, o fluxo de
responsabilidades precisa permanecer previsível.

Regras práticas para revisão de código:

- `config/` configura a aplicação, mas não concentra regra de negócio
- `core` oferece base compartilhada, mas não deve absorver tudo por
  conveniência
- `edicoes` e `polos` devem evoluir a própria regra de negócio dentro de seus
  apps
- integrações externas devem permanecer isoladas em `apps/integracoes/`
- scripts de container cuidam de bootstrap e runtime, não de comportamento de
  domínio

## Estrutura das integrações

As integrações externas foram organizadas para explicitar papéis desde o
início.

| Arquivo | Responsabilidade |
| --- | --- |
| `port.py` | contrato público que o resto da aplicação consome |
| `adapter.py` | implementação que adapta o contrato para o client externo |
| `client.py` | camada de acesso ao serviço remoto |
| `exceptions.py` | exceções específicas da integração |
| `tests/` | testes da borda de integração |

Essa separação ajuda a evitar que chamadas HTTP, tratamento de erro e regra de
aplicação fiquem misturados no mesmo ponto do código.

## Decisões de escopo atuais

- autenticação funcional permanece como evolução futura
- integrações HTTP reais com CoreSSO e EOL permanecem como evolução futura
- regras reais de negócio de `edicoes` e `polos` permanecem em aberto para a
  evolução do domínio

## Como evoluir a arquitetura sem gerar retrabalho

Ao adicionar comportamento novo nas próximas iterações, alguns critérios ajudam
a manter a árvore coerente:

1. Coloque cada regra de negócio no app de domínio correspondente.
2. Use `core` apenas para o que for realmente compartilhado.
3. Mantenha adaptadores externos fora dos apps de domínio.
4. Adicione testes no mesmo app ou pacote que recebeu a alteração.
5. Evite mover código para camadas genéricas sem necessidade concreta.

## Organização da documentação

- `README.md` cobre onboarding rápido e comandos do dia a dia
- `docs/` concentra os guias navegáveis do projeto
