# SME-RecreioNasFerias-Backend

> Backend Django do SME Recreio nas Férias com execução recomendada via Docker
> Compose, endpoint público de saúde, schema OpenAPI e base técnica pronta
> para a evolução contínua do sistema.

## Objetivo e escopo

Este repositório entrega a base técnica do backend, com estrutura Django
organizada, operação local por Docker Compose, endpoint de saúde, schema
OpenAPI, autenticação institucional via CoreSSO, sessão JWT local, stack de
qualidade e documentação operacional.

O backend já implementa o fluxo de autenticação institucional, o
gerenciamento local de sessão, a integração EOL de escolas e a população
de polos de gestão direta.

## O que o projeto entrega hoje

- execução padronizada via Docker Compose para desenvolvimento, testes e
  validação;
- endpoint público de saúde em `/api/v1/health/`;
- schema OpenAPI em `/api/v1/schema/` e Swagger UI em `/api/v1/docs/`;
- autenticação via CoreSSO em `/api/v1/auth/login/`;
- renovação, verificação, logout e perfil do usuário em `/api/v1/auth/`;
- apps `core`, `edicoes` e `polos`, com CRUD de polos e população de
  unidades diretas em `/api/v1/polos/popular/`;
- integração `coresso` funcional para autenticação e `eol` funcional para
  consulta de unidades escolares;
- `mypy` estrito, cobertura com `fail_under = 80` e documentação Sphinx
  ativos.

## Comece por aqui

Suba o ambiente local com:

```bash
cp .env.example .env
make up
```

Pontos de acesso no ambiente de desenvolvimento:

- API: `http://localhost:8000/api/v1/health/`
- Login: `http://localhost:8000/api/v1/auth/login/`
- Schema OpenAPI: `http://localhost:8000/api/v1/schema/`
- Swagger UI: `http://localhost:8000/api/v1/docs/`
- Debug remoto: porta `5678`
- Postgres local: porta `5432`

Para validar o fluxo mais próximo da imagem de produção:

```bash
cp .env.example .env
make up-prod
```

Nesse modo, a API sobe com Gunicorn e usa o entrypoint de produção.

## Estrutura do projeto

```text
.
|-- apps/
|   |-- core/                 # base compartilhada, saúde, auth e usuário customizado
|   |-- edicoes/              # estrutura inicial do domínio de edições
|   |-- polos/                # estrutura inicial do domínio de polos
|   `-- integracoes/
|       |-- coresso/          # integração real de autenticação com o CoreSSO
|       `-- eol/              # integração real de escolas com EOL
|-- config/                   # settings, URLs, ASGI e WSGI
|-- docs/                     # documentação Sphinx do projeto
|-- requirements/             # dependências separadas por ambiente
|-- scripts/                  # entrypoints dos containers
`-- testes/                   # reservado para E2E, smoke ou BDD
```

## Requisitos locais

- Docker
- Docker Compose plugin
- GNU Make

## Fluxo de desenvolvimento

Os comandos principais do dia a dia ficam centralizados no `Makefile`:

```bash
make build
make up
make up-prod
make down
make migrate
make test
make coverage
make lint
make typecheck
make schema
make docs
make precommit
make quality
```

O alvo `make quality` agrupa lint, typecheck, testes e documentação. Para a
geração separada de artefatos, os alvos mais usados são:

- `make schema` para gerar `docs/_build/schema.yml`
- `make docs` para gerar `docs/_build/html`
- `make coverage` para gerar `docs/_cov`

## Configuração local

O arquivo `.env.example` é a referência versionada das variáveis usadas pelo
projeto. O arquivo `.env` deve ser usado apenas localmente.

As variáveis mais importantes para iniciar o ambiente são:

- `DJANGO_SECRET_KEY`, `DEBUG` e `ALLOWED_HOSTS`
- `CORS_ALLOW_CREDENTIALS`, `CORS_ALLOWED_ORIGINS` e `CSRF_TRUSTED_ORIGINS`
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER` e
  `POSTGRES_PASSWORD`
- `PORT_WEB` e `PORT_DEBUGPY`
- `AUTH_API_BASE_URL` e `AUTH_API_EOL_KEY`
- `AUTH_REFRESH_COOKIE_SECURE`
- `RUN_MIGRATIONS` e `RUN_MIGRATIONS_MODE`
- `GUNICORN_WORKERS` e `GUNICORN_TIMEOUT`

A referência completa das variáveis e dos comportamentos por ambiente está em
`docs/configuration.md`.

## Pre-commit

O repositório já versiona a configuração em `.pre-commit-config.yaml`.

Para instalar o hook automático na máquina host, use:

```bash
python3 -m pip install --user pre-commit
pre-commit install
```

Depois disso, cada `git commit` executa os hooks apenas nos arquivos staged.

Para rodar todos os hooks manualmente na máquina host:

```bash
pre-commit run --all-files
```

Se preferir validar os mesmos hooks sem instalar o `pre-commit` no host, use o
alvo Dockerizado do projeto:

```bash
make precommit
```

## Banco de dados em testes

Os ambientes `make up`, `make up-prod`, `make test` e `make coverage` usam
Postgres.

Quando o pytest roda, o Django cria um banco temporário separado no mesmo
servidor configurado pelas variáveis `POSTGRES_*`, aplica as migrations,
executa a suíte e remove esse banco ao final. Na prática, o nome costuma ser
`test_<POSTGRES_DB>`.

Resumo prático:

- o desenvolvimento usa Postgres persistido em volume Docker;
- os testes não usam as tabelas da aplicação; usam um banco temporário próprio
  no mesmo servidor configurado;
- `make down` derruba os containers, mas preserva o volume do banco.

Importante: os testes não usam o banco principal da aplicação, mas usam o
mesmo servidor configurado no `.env`. Por isso, o ambiente de testes deve
apontar para um Postgres isolado de produção.

## Ambiente local semelhante à produção

O compose usado por `make up-prod` trabalha com o `Dockerfile` de produção,
sobe a API com Gunicorn e usa o Postgres configurado no `.env`
(`POSTGRES_HOST=db`).

No entrypoint de produção, o comportamento padrão é:

- executar `migrate` automaticamente no startup;
- usar modo `strict` quando `RUN_MIGRATIONS_MODE` não for informado;
- abortar o boot se a migração falhar.

Em outras palavras: se a infraestrutura não enviar `RUN_MIGRATIONS`, a imagem
continua migrando por padrão. Para desabilitar esse comportamento de forma
explícita, é preciso enviar `RUN_MIGRATIONS=false`.

No fluxo `make up-prod`, a regra é a mesma do entrypoint:

- se `RUN_MIGRATIONS` não estiver definido, a imagem migra por padrão;
- se `RUN_MIGRATIONS=false` estiver definido explicitamente no ambiente, o
  startup não executa migrations.

## Documentação viva

A documentação principal do projeto fica em `docs/` e é gerada com Sphinx.

Páginas principais:

- `docs/index.rst` para a visão geral da documentação
- `docs/getting_started.md` para setup e operação local
- `docs/configuration.md` para variáveis de ambiente e runtime
- `docs/arquitetura.md` para a organização da estrutura do projeto

Para documentação mais aprofundada por área, a pasta `docs/` também pode usar
subárvores temáticas em `docs/dominios/`.

Build local da documentação:

```bash
make docs
```

## Fora do escopo atual

- atualização ou desativação automática de polos diretos já persistidos
- agendamento da população de polos fora da action autenticada

