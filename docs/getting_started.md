# Getting Started

Este guia mostra o caminho recomendado para subir, validar e operar o projeto
via Docker Compose.

## Requisitos

- Docker
- Docker Compose plugin
- GNU Make

## Execução recomendada

A forma principal de executar a API, o banco, os testes, a geração de schema
e a documentação é via Docker Compose. Isso reduz diferenças entre ambientes e
evita setup local solto.

Antes de iniciar:

```bash
cp .env.example .env
```

O arquivo `.env.example` contém os valores esperados para o ambiente local. A
referência completa das variáveis, defaults e efeitos por ambiente está em
[Configuração](configuration.md).

## Ambiente de desenvolvimento

Use este fluxo quando precisar editar código, testar endpoints, depurar a API
ou trabalhar com hot reload.

```bash
make up
```

Esse fluxo sobe a API em modo de desenvolvimento, com Postgres dedicado no
Compose local.

O container `api` usa o `Dockerfile.dev`, monta o código da workspace em
`/app` e sobe o Django com `runserver` via `debugpy`. Nesse modo, o
`scripts/entrypoint-dev.sh` aplica `migrate` automaticamente quando o comando
de bootstrap contém `manage.py runserver`.

## Acessos locais

- Healthcheck: `http://localhost:8000/api/v1/health/`
- Schema OpenAPI: `http://localhost:8000/api/v1/schema/`
- Swagger UI: `http://localhost:8000/api/v1/docs/`
- Debug remoto: porta `5678`
- Postgres: porta `5432`

## Ambiente local semelhante à produção

Use este fluxo para validar o comportamento da imagem de produção sem depender
do ambiente final.

```bash
make up-prod
```

Esse fluxo usa o `Dockerfile` de produção, executa `collectstatic` no build e
sobe a aplicação com Gunicorn.

Nesse modo:

- o serviço `api` lê `POSTGRES_HOST=db` do `.env` (nome do serviço Docker
  interno), junto com `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER` e
  `POSTGRES_PASSWORD`;
- o entrypoint de produção roda `migrate` por padrão, mesmo sem
  `RUN_MIGRATIONS` explícito;
- se `RUN_MIGRATIONS=false` estiver definido explicitamente no ambiente, esse
  comportamento é desativado;
- o comportamento em caso de falha de migração fica definido por
  `RUN_MIGRATIONS_MODE`.

## Comparação rápida dos fluxos

| Fluxo | Arquivo principal | Runtime da API | Uso esperado |
| --- | --- | --- | --- |
| Desenvolvimento | `docker-compose-dev.yml` | `runserver` com `debugpy` | codar, depurar e testar endpoints localmente |
| Semelhante à produção | `docker-compose.yml` | Gunicorn com entrypoint de produção | validar imagem, bootstrap e comportamento de runtime |

## Banco de dados nos testes

Os ambientes `make up`, `make up-prod`, `make test` e `make coverage` usam
Postgres.

Durante os testes, o Django não reutiliza as tabelas da aplicação. Ele cria um
banco temporário separado no mesmo servidor configurado por `POSTGRES_HOST`,
`POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER` e `POSTGRES_PASSWORD`, aplica
as migrations, executa a suíte e remove esse banco ao final. Em geral, o nome
desse banco é `test_<POSTGRES_DB>`.

Resumo prático:

- desenvolvimento usa Postgres em volume Docker;
- testes usam um banco temporário próprio no mesmo servidor configurado;
- `make down` derruba os containers sem apagar o volume do banco.

Importante: como a suíte usa o mesmo servidor configurado no `.env`, o
ambiente de testes precisa apontar para um Postgres isolado de produção.

## Operação do dia a dia

Os comandos mais comuns ficam centralizados no `Makefile`.

```bash
make build
make build-prod
make shell
make logs
make migrate
make test
make coverage
make lint
make typecheck
make schema
make docs
make precommit
make down
```

Resumo prático dos alvos mais usados:

- `make up`: sobe o ambiente de desenvolvimento
- `make up-prod`: sobe o ambiente local semelhante à produção
- `make shell`: abre um shell Django no container de desenvolvimento
- `make logs`: acompanha os logs do serviço `api`
- `make migrate`: aplica migrations no banco do Compose de desenvolvimento
- `make quality`: executa lint, typecheck, testes e build da docs

## Pre-commit

O projeto já versiona `.pre-commit-config.yaml`. Existem duas formas de usar
os hooks.

Para instalar o hook automático no Git da máquina host:

```bash
python3 -m pip install --user pre-commit
pre-commit install
```

Depois disso, cada `git commit` executa os hooks apenas nos arquivos staged.

Para rodar todos os hooks manualmente na máquina host:

```bash
pre-commit run --all-files
```

Se quiser validar os mesmos hooks sem instalar `pre-commit` no host, use o
alvo Dockerizado do projeto:

```bash
make precommit
```

## Validações do repositório

Para confirmar que o repositório continua íntegro depois de alterações:

```bash
make lint
make typecheck
make test
make coverage
make schema
make docs
make precommit
```

Esse conjunto cobre formatação, lint, tipagem estática, testes, cobertura,
schema OpenAPI, build da documentação e hooks do pre-commit.

## Saídas geradas localmente

- `make schema` escreve o schema em `docs/_build/schema.yml`
- `make docs` gera HTML em `docs/_build/html`
- `make coverage` gera HTML em `docs/_cov`

## Encerramento e limpeza

Para parar os ambientes Docker locais:

```bash
make down
```

Para remover artefatos locais gerados pelo fluxo de validação:

```bash
make clean-local
```

## Escopo operacional atual

A execução padrão do projeto é via Docker Compose. O uso de `.venv` local não
é o caminho principal deste repositório.

No estado atual, o objetivo do backend é garantir estrutura inicial,
validação local, healthcheck, schema e documentação. Autenticação funcional,
integrações HTTP reais e regras de negócio seguem como evoluções previstas.
