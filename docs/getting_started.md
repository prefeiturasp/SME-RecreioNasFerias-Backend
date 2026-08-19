# Getting Started

Este guia cobre o fluxo recomendado para subir, validar e operar o projeto via
Docker Compose.

## Requisitos

- Docker
- Docker Compose plugin
- `make` disponível na máquina host

## Preparação

Copie o arquivo de ambiente base:

```bash
cp .env.example .env
```

O `.env.example` já traz os valores esperados para o fluxo local, incluindo as
origens de frontend em `localhost:3000`.

## Ambiente de desenvolvimento

Use este fluxo para editar código, testar endpoints, depurar a API e trabalhar
com hot reload.

```bash
make up
```

Nesse modo:

- o container `api` usa o `Dockerfile.dev`
- o código é montado em `/app`
- a aplicação sobe com `runserver` via `debugpy`
- o entrypoint de desenvolvimento aplica `migrate` automaticamente no fluxo de
  `runserver`

## Acessos locais

- Healthcheck: `http://localhost:8000/api/v1/health/`
- Login: `http://localhost:8000/api/v1/auth/login/`
- Perfil autenticado: `http://localhost:8000/api/v1/auth/me/`
- Schema OpenAPI: `http://localhost:8000/api/v1/schema/`
- Swagger UI: `http://localhost:8000/api/v1/docs/`
- Debug remoto: porta `5678`

## Ambiente local semelhante à produção

Use este fluxo para validar a imagem final, o bootstrap de produção e o
comportamento com Gunicorn.

```bash
make up-prod
```

Nesse modo:

- a imagem usa o `Dockerfile` de produção
- o build executa `collectstatic`
- a API sobe com Gunicorn
- o startup usa `RUN_MIGRATIONS` e `RUN_MIGRATIONS_MODE`

## Fluxos principais

| Fluxo | Comando | Uso |
| --- | --- | --- |
| desenvolvimento | `make up` | editar código, testar endpoints e usar hot reload |
| produção local | `make up-prod` | validar a imagem de produção com Gunicorn |
| shell Django | `make shell` | inspecionar models e serviços |
| logs | `make logs` | acompanhar a API |
| migrations | `make migrate` | aplicar migrations no banco local |
| qualidade | `make quality` | validar lint, tipagem, testes e docs |

## Validação do repositório

Para validar o repositório de ponta a ponta:

```bash
make quality
```

Se precisar rodar verificações separadas:

```bash
make lint
make typecheck
make test
make docs
make schema
make coverage
make precommit
```

## Pre-commit

O repositório já versiona `.pre-commit-config.yaml`.

Se quiser instalar os hooks no Git da máquina host:

```bash
python3 -m pip install --user pre-commit
pre-commit install
```

Para rodar os hooks manualmente na máquina host:

```bash
pre-commit run --all-files
```

Se preferir usar apenas o fluxo Dockerizado do projeto:

```bash
make precommit
```

## Banco de dados nos testes

- a aplicação roda sempre em Postgres
- `make test` e `make coverage` criam um banco temporário no mesmo servidor
  configurado por `POSTGRES_*`
- esse ambiente de testes deve permanecer isolado de produção

Na prática, `make up` e `make up-prod` usam o banco principal configurado no
`.env`, enquanto os testes usam um banco temporário `test_<POSTGRES_DB>` no
mesmo servidor.

## Artefatos gerados localmente

- `make schema` escreve `docs/_build/schema.yml`
- `make docs` gera HTML em `docs/_build/html`
- `make coverage` gera HTML em `docs/_cov`

## Encerramento e limpeza

```bash
make down
make clean-local
```

## Onde aprofundar

- detalhes de configuração: [Configuração](configuration.md)
- visão estrutural: [Arquitetura](arquitetura.md)
- detalhes por domínio e integração: `docs/dominios/`
