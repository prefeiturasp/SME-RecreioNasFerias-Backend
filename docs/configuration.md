# Configuração via variáveis de ambiente

Este guia resume as variáveis que costumam mudar por ambiente e os efeitos mais
importantes de runtime. O arquivo `.env.example` continua sendo a referência
para desenvolvimento local.

## Como a configuração é resolvida

- o Django lê `.env` na raiz quando o arquivo existe
- variáveis já presentes no ambiente do processo têm prioridade sobre `.env`
- valores sem default real precisam ser informados pelo ambiente
- o runtime de produção usa `scripts/entrypoint.sh` para migrations e Gunicorn

Arquivos de referência:

- `.env.example`: referência versionada das variáveis locais
- `.env`: configuração local não versionada
- `config/settings.py`: leitura do ambiente e configuração Django
- `scripts/entrypoint.sh`: runtime e migrations da imagem de produção

## Django e API

| Variável | Padrão | Descrição |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | sem padrão | chave secreta do Django; a aplicação não deve subir sem ela |
| `DEBUG` | `False` | liga ou desliga o modo debug |
| `ALLOWED_HOSTS` | `localhost` | lista de hosts aceitos no header `Host` |

## CORS e CSRF

| Variável | Padrão no código | Descrição |
| --- | --- | --- |
| `CORS_ALLOW_CREDENTIALS` | `True` | permite uso do cookie HttpOnly de refresh em chamadas cross-origin |
| `CORS_ALLOWED_ORIGINS` | vazio | origens do frontend autorizadas a chamar a API |
| `CSRF_TRUSTED_ORIGINS` | vazio | origens confiáveis para fluxos que dependam do CSRF do Django |

Observações importantes:

- `ALLOWED_HOSTS` usa apenas host, sem esquema
- `CORS_ALLOWED_ORIGINS` usa origem completa, com esquema
- `CSRF_TRUSTED_ORIGINS` não substitui `CORS_ALLOWED_ORIGINS`
- no fluxo atual de autenticação, `CORS_ALLOW_CREDENTIALS=True` faz sentido
  porque o refresh token é armazenado em cookie `HttpOnly`
- o `.env.example` local já traz valores de exemplo para `localhost:3000`, mas
  isso não é o default real do código

## Banco de dados

| Variável | Padrão | Descrição |
| --- | --- | --- |
| `POSTGRES_HOST` | `db` | host do Postgres |
| `POSTGRES_PORT` | `5432` | porta do Postgres |
| `POSTGRES_DB` | sem padrão | banco principal da aplicação |
| `POSTGRES_USER` | sem padrão | usuário do banco |
| `POSTGRES_PASSWORD` | sem padrão | senha do banco |

A aplicação roda sempre em Postgres. Nos testes, o Django reutiliza essas
mesmas variáveis para criar um banco temporário no mesmo servidor.

## CoreSSO e autenticação

| Variável | Padrão | Descrição |
| --- | --- | --- |
| `AUTH_API_BASE_URL` | vazio | URL base da integração CoreSSO |
| `AUTH_API_EOL_KEY` | vazio | valor enviado no header `x-api-eol-key` |
| `AUTH_API_AUTH_TIMEOUT_SECONDS` | `10` | timeout de leitura do login CoreSSO |
| `AUTH_API_CONNECT_TIMEOUT_SECONDS` | `5` | timeout de conexão TCP |
| `AUTH_API_TIMEOUT_SECONDS` | `60` | timeout genérico reservado para integrações `AUTH_API_*` |
| `AUTH_CODIGO_SISTEMA` | `1009` | código do sistema enviado ao CoreSSO |
| `AUTH_REFRESH_COOKIE_SECURE` | `not DEBUG` | atributo `Secure` do cookie de refresh |

Pontos fixos no código atual:

- access token com 15 minutos
- refresh token com 7 dias
- cookie `refresh_token`
- path do cookie em `/api/v1/auth/`
- `SameSite=Lax`

O detalhamento do fluxo de autenticação e da normalização do CoreSSO fica em
`docs/dominios/integracoes/coresso/index.rst`.

A integração EOL de escolas reutiliza essa mesma família `AUTH_API_*`
(`AUTH_API_BASE_URL`, `AUTH_API_EOL_KEY` e os timeouts). O detalhamento dessa
borda fica em `docs/dominios/integracoes/eol/index.rst`.

## Runtime de produção

| Variável | Padrão | Descrição |
| --- | --- | --- |
| `GUNICORN_WORKERS` | `3` | quantidade de workers do Gunicorn |
| `GUNICORN_TIMEOUT` | `60` | timeout do Gunicorn em segundos |
| `RUN_MIGRATIONS` | `true` | executa `migrate` no startup de produção |
| `RUN_MIGRATIONS_MODE` | `strict` | aborta o boot ou segue em `best-effort` se a migração falhar |

## Desenvolvimento local

| Variável | Padrão | Descrição |
| --- | --- | --- |
| `PORT_WEB` | `8000` | porta publicada da API no host |
| `PORT_DEBUGPY` | `5678` | porta publicada do debug remoto |

## Testes e artefatos

- `make test` e `make coverage` criam um banco temporário no mesmo servidor
  configurado por `POSTGRES_*`
- `make schema` gera `docs/_build/schema.yml`
- `make docs` gera `docs/_build/html`
- `make coverage` gera `docs/_cov`

## Exemplo mínimo local

```bash
DJANGO_SECRET_KEY=desenvolvimento-local
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

CORS_ALLOW_CREDENTIALS=True
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=recreio_ferias
POSTGRES_USER=recreio_ferias
POSTGRES_PASSWORD=recreio_ferias

AUTH_REFRESH_COOKIE_SECURE=False
```

## Observações operacionais

- a aplicação roda sempre em Postgres, sem fallback de SQLite
- `make test` e `make coverage` criam um banco temporário no mesmo servidor
- o healthcheck do container usa `GET /api/v1/health/`
- o `.env.example` cobre o fluxo local; produção e homologação devem usar
  variáveis do ambiente
