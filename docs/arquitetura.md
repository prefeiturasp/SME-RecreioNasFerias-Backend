# Arquitetura

Este documento descreve a organização do repositório e as responsabilidades de
cada área. O detalhamento profundo de domínios e integrações deve evoluir em
`docs/dominios/`, para evitar repetição nas páginas gerais.

## Princípio adotado

O projeto segue uma organização orientada por domínio, com um monolito Django
na raiz e isolamento explícito das integrações externas.

Na prática, isso significa:

- `core` concentra o que é compartilhado pelo sistema
- cada domínio principal evolui em seu próprio app Django
- integrações externas ficam em `apps/integracoes/`
- `config/`, `requirements/` e `scripts/` tratam configuração e runtime, não
  regra de negócio

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

| Área | Papel no projeto |
| --- | --- |
| `apps/core/` | infraestrutura compartilhada, autenticação, modelos base, usuário local e healthcheck |
| `apps/edicoes/` | domínio de edições |
| `apps/polos/` | domínio de polos |
| `apps/integracoes/` | bordas externas, como CoreSSO e EOL |
| `config/` | settings, URLs, ASGI e WSGI |
| `scripts/` | entrypoints e bootstrap dos containers |
| `requirements/` | dependências separadas por ambiente |
| `docs/` | documentação geral e navegação Sphinx |
| `testes/` | espaço reservado para E2E, smoke ou BDD |

As páginas gerais desta documentação devem responder rápido três perguntas:

- como o repositório está organizado
- como o projeto sobe e é validado
- quais configurações variam por ambiente

Quando um assunto exigir fluxo detalhado, contrato externo ou regra mais
específica, o aprofundamento deve acontecer em `docs/dominios/`.

## Core

O app `core` reúne o que hoje é transversal ao sistema.

Nesta etapa ele concentra:

- autenticação institucional via CoreSSO com sessão JWT local
- usuário local e vínculo ao cargo permitido autorizado
- auditoria simples de login
- healthcheck e contratos HTTP de autenticação
- tradução centralizada de exceções REST para respostas mais consistentes

Os pontos centrais do fluxo atual ficam distribuídos em:

- `apps/core/services/auth_service.py`
- `apps/core/authentication.py`
- `apps/core/api/serializers/auth_serializer.py`
- `apps/core/api/views/auth.py`
- `apps/core/models/identidade.py`

## Apps de domínio

`edicoes` e `polos` já possuem a estrutura do app, com `api/`, `models/`,
`services/`, testes e migrations. O domínio de polos já popula unidades
diretas a partir da EOL em `POST /api/v1/polos/popular/`.

Quando esses domínios crescerem, o detalhamento arquitetural deve evoluir em
`docs/dominios/` em vez de inflar esta página.

Em outras palavras: esta página explica a forma do sistema; a árvore de
domínios explica o conteúdo específico de cada área.

## Integrações externas

As integrações ficam separadas do domínio de negócio e seguem uma organização
hexagonal simples.

Estrutura típica:

| Arquivo | Responsabilidade |
| --- | --- |
| `port.py` | contrato público consumido pelo restante da aplicação |
| `adapter.py` | adaptação entre contrato interno e client externo |
| `client.py` | acesso HTTP ao serviço remoto |
| `exceptions.py` | exceções específicas da integração |
| `tests/` | testes da borda de integração |

Estado atual:

- `apps/integracoes/coresso/` já executa o login real e normaliza o payload
- `apps/integracoes/eol/` já consome os endpoints de escolas da integração EOL,
  normalizando, filtrando e enriquecendo as unidades elegíveis ao Recreio

## Regras de organização

- `config/` configura a aplicação inteira, mas não recebe regra de negócio
- `core` não deve virar depósito genérico de código por conveniência
- regra de negócio nova deve nascer no app de domínio correspondente
- chamadas HTTP externas e contratos remotos devem permanecer em
  `apps/integracoes/`
- testes devem ficar o mais perto possível do código que exercitam

## Documentação

- `README.md` cobre onboarding rápido e comandos do dia a dia
- `docs/` cobre visão geral, configuração e operação
- `docs/dominios/` cobre aprofundamento por domínio e integração
