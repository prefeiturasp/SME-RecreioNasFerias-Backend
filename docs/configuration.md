# Configuração via variáveis de ambiente

A configuração operacional do projeto é orientada por variáveis de ambiente,
pelos arquivos de Compose e pelos entrypoints dos containers. As tabelas abaixo
mostram o valor padrão efetivamente aplicado quando o código, o Compose ou os
scripts definem um fallback. Quando não houver fallback real, a variável é
tratada como `sem padrão`.

## Como a configuração é resolvida

- O Django lê `.env` na raiz do repositório quando o arquivo existe.
- O `docker-compose-dev.yml` e o `docker-compose.yml` também usam `.env` como
  fonte de configuração do ambiente local.
- Em execução normal e em testes, `config/settings.py` usa sempre Postgres.
- Em `make test` e `make coverage`, o Django cria um banco temporário separado
  no mesmo servidor definido por `POSTGRES_HOST`, `POSTGRES_PORT`,
  `POSTGRES_DB`, `POSTGRES_USER` e `POSTGRES_PASSWORD`, aplica as migrations,
  executa a suíte e remove esse banco ao final. Em geral, o nome desse banco é
  `test_<POSTGRES_DB>`.
- O Compose usa `.env` como única fonte das variáveis de banco
  (`POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`,
  `POSTGRES_PASSWORD`). O `POSTGRES_HOST` no `.env.example` já vem com `db`
  (nome do serviço Docker); para rodar sem Docker, troque por `localhost` ou
  o IP do Postgres.
- No entrypoint de produção, `RUN_MIGRATIONS` assume `true` e
  `RUN_MIGRATIONS_MODE` assume `strict` quando essas variáveis não são
  informadas.
- No `docker-compose.yml` local semelhante à produção, o comportamento segue o
  mesmo default do entrypoint. Ou seja: ausência de `RUN_MIGRATIONS` implica
  migração automática; `RUN_MIGRATIONS=false` desativa migrations de forma
  explícita.

## Resumo rápido sobre banco de dados

- a aplicação roda sempre em Postgres, em qualquer ambiente (dev, teste ou
  prod);
- testes automatizados usam um banco temporário separado no mesmo servidor
  configurado por `POSTGRES_*`;
- não existe fallback de SQLite no projeto.

`make up` e `make up-prod` usam o banco principal da aplicação. `make test` e
`make coverage` usam esse mesmo servidor de Postgres, mas em um banco
temporário criado só para a suíte. Por isso, o `.env` de testes deve apontar
para um Postgres isolado de produção.

## Arquivos de referência

- `.env.example`: referência versionada das variáveis do projeto
- `.env`: configuração local não versionada
- `config/settings.py`: leitura do ambiente e configuração Django
- `docker-compose-dev.yml`: ambiente de desenvolvimento com volume montado
- `docker-compose.yml`: ambiente local semelhante à produção
- `scripts/entrypoint.sh`: estratégia de migração e Gunicorn em runtime de
  produção
- `scripts/entrypoint-dev.sh`: bootstrap do container de desenvolvimento

## Django e API

Essas variáveis controlam o comportamento principal da aplicação Django e são
lidas diretamente em `config/settings.py`.

| Variável | Padrão | Descrição |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | `django-inseguro-ajustar-em-producao` | Chave secreta do Django. O fallback existe apenas para não travar o ambiente local; em qualquer ambiente compartilhado, defina um valor próprio. |
| `DJANGO_DEBUG` | `False` | Liga ou desliga o modo debug do Django. Aceita valores booleanos lidos pelo `django-environ`. |
| `DJANGO_ALLOWED_HOSTS` | `localhost` | Lista separada por vírgula com os hosts aceitos pelo Django. Não inclua protocolo aqui. |
| `CSRF_TRUSTED_ORIGINS` | vazio | Lista separada por vírgula com origens completas confiáveis para CSRF, por exemplo `http://localhost:8000`. |

Exemplo mínimo para execução local sem Docker:

```bash
DJANGO_SECRET_KEY=desenvolvimento-local
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000

POSTGRES_HOST=192.168.0.10
POSTGRES_PORT=5432
POSTGRES_DB=recreio_ferias
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

Sem Docker, troque `POSTGRES_HOST` por `localhost` ou o IP do Postgres.

## Banco de dados (Postgres)

Variáveis de conexão com o Postgres, lidas em `config/settings.py`. O `.env`
é a única fonte desses valores — o Compose não sobrescreve nada. O default de
`POSTGRES_HOST` no `settings.py` é `db` (nome do serviço Docker); para rodar
sem Docker, ajuste no `.env` para `localhost` ou o IP do Postgres.

Essas mesmas variáveis também são usadas pela suíte de testes para abrir a
conexão com o servidor e criar o banco temporário da execução.

| Variável | Padrão | Descrição |
| --- | --- | --- |
| `POSTGRES_HOST` | `db` | Host ou IP do Postgres. `db` é o nome do serviço no Compose; sem Docker, use `localhost` ou o IP do Postgres externo. |
| `POSTGRES_PORT` | `5432` | Porta de conexão com o Postgres. Em `docker-compose-dev.yml` também controla a porta publicada no host (mapeamento `${POSTGRES_PORT:-5432}:5432`); dentro do Compose o banco continua ouvindo em `5432`. |
| `POSTGRES_DB` | sem padrão | Nome do banco usado pela aplicação. |
| `POSTGRES_USER` | sem padrão | Usuário do banco usado pela aplicação. |
| `POSTGRES_PASSWORD` | sem padrão | Senha do usuário do banco. |

## Portas publicadas no host

Essas variáveis controlam apenas as portas expostas pela máquina host. As
portas internas dos containers permanecem fixas.

| Variável | Padrão | Descrição |
| --- | --- | --- |
| `PORT_WEB` | `8000` | Porta publicada para a API Django/Gunicorn no host local. O container continua ouvindo em `8000`. |
| `PORT_DEBUGPY` | `5678` | Porta publicada para debug remoto no ambiente de desenvolvimento. Só faz efeito no `docker-compose-dev.yml`. |

## Runtime web e Gunicorn

Essas variáveis são usadas somente pelo entrypoint de produção quando o
container sobe com `CMD ["gunicorn"]`.

| Variável | Padrão | Descrição |
| --- | --- | --- |
| `GUNICORN_WORKERS` | `3` | Quantidade de workers do Gunicorn. O valor `3` assume container com 1 core, conforme fórmula `(2 × cores) + 1` recomendada pelo Gunicorn (tipicamente 4–12). Aumente se o container tiver mais cores. Ignorada no fluxo de desenvolvimento com `runserver`. |
| `GUNICORN_TIMEOUT` | `60` | Timeout, em segundos, para requisições tratadas pelo Gunicorn. O default da ferramenta é `30`; o valor `60` dá margem para queries e integrações HTTP mais lentas. Ignorada no fluxo de desenvolvimento com `runserver`. |

## Estratégia de migração no startup

O runtime de produção executa migração automaticamente por padrão. Isso evita
o cenário silencioso em que a imagem sobe sem aplicar migrations apenas porque
a infraestrutura esqueceu de injetar `RUN_MIGRATIONS`.

Quando a estratégia de deploy exigir migração em job ou etapa separada, a
desativação deve ser explícita via `RUN_MIGRATIONS=false`.

| Variável | Padrão | Descrição |
| --- | --- | --- |
| `RUN_MIGRATIONS` | `true` | Quando `true`, o `scripts/entrypoint.sh` executa `python manage.py migrate --noinput` antes de subir a API. Para desabilitar esse comportamento, a infraestrutura precisa enviar `RUN_MIGRATIONS=false` explicitamente. |
| `RUN_MIGRATIONS_MODE` | `strict` | Define o comportamento quando a migração falha. Aceita `strict` para abortar o boot e `best-effort` para registrar aviso e continuar a subida. |

No ambiente de desenvolvimento existe uma regra separada: o
`scripts/entrypoint-dev.sh` roda `migrate` automaticamente quando o comando do
container contém `manage.py runserver`.

## Testes

Os testes não introduzem variáveis de ambiente próprias. A suíte reutiliza
`POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER` e
`POSTGRES_PASSWORD` para conectar ao servidor configurado e criar um banco
temporário separado para a execução.

Na prática, o fluxo padrão é:

```bash
make test
make coverage
```

Em geral, o banco temporário recebe o nome `test_<POSTGRES_DB>`. Ele não usa
as tabelas do banco principal da aplicação, mas continua no mesmo servidor de
Postgres configurado no `.env`.

## Variáveis internas e comportamento por ambiente

Alguns comportamentos importantes não dependem de variável nova no `.env`, mas
influenciam diretamente a forma como o ambiente sobe.

| Item | Valor padrão | Descrição |
| --- | --- | --- |
| `DJANGO_SETTINGS_MODULE` | `config.settings` | Definida na imagem de produção e também pelos entrypoints Django (`manage.py`, `wsgi.py`, `asgi.py`). Em geral não precisa ser configurada manualmente. |
| Banco em testes | Postgres temporário | O Django cria um banco temporário separado no mesmo servidor configurado por `POSTGRES_*`, aplica as migrations, executa a suíte e remove esse banco ao final. Em geral o nome é `test_<POSTGRES_DB>`. |
| Banco da aplicação | Postgres principal | Fora dos testes a aplicação usa `POSTGRES_DB` normalmente. O default de `POSTGRES_HOST` é `db` (serviço do Compose). Sem Docker, ajuste para `localhost` ou o IP do Postgres. |
| Healthcheck dos containers | `GET /api/v1/health/` | Tanto a imagem de desenvolvimento quanto a de produção usam esse endpoint para validar a saúde local do serviço. |

## Cuidados com o ambiente de testes

- Nunca aponte o `.env` usado em `make test` ou `make coverage` para um
  servidor produtivo.
- Garanta que o usuário configurado em `POSTGRES_USER` tenha permissão para
  criar o banco temporário de testes.
- No fluxo local padrão, `make test` e `make coverage` sobem o serviço `db` do
  `docker-compose-dev.yml`, então esse isolamento já vem pronto no repositório.

## Exemplo recomendado para Docker Compose local

```bash
DJANGO_SECRET_KEY=desenvolvimento-local
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000

POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=recreio_ferias
POSTGRES_USER=recreio_ferias
POSTGRES_PASSWORD=recreio_ferias

PORT_WEB=8000
PORT_DEBUGPY=5678

GUNICORN_WORKERS=3
GUNICORN_TIMEOUT=60

RUN_MIGRATIONS=true
RUN_MIGRATIONS_MODE=strict
```

## Artefatos locais gerados pelos comandos

- `make schema` gera `docs/_build/schema.yml`
- `make docs` gera `docs/_build/html`
- `make coverage` gera `docs/_cov`

Esses artefatos ajudam na validação local e não fazem parte do código-fonte
versionado.
