COMPOSE ?= docker compose
COMPOSE_DEV ?= docker compose -f docker-compose-dev.yml
RUN_API = $(COMPOSE_DEV) run --rm --build api
RUN_API_NODEPS = $(COMPOSE_DEV) run --rm --no-deps --build api
PYTEST_ARGS ?= -q -p no:cacheprovider

.PHONY: help ensure-env up up-prod down build build-prod logs shell migrate test coverage lint typecheck schema docs docs-clean precommit quality clean-local

help:
	@echo "Uso: make <alvo>"
	@echo ""
	@echo "Ambiente:"
	@echo "  make build        - build da imagem dev"
	@echo "  make build-prod   - build da imagem de producao"
	@echo "  make up           - sobe ambiente de desenvolvimento"
	@echo "  make up-prod      - sobe ambiente prod-like local"
	@echo "  make down         - derruba os ambientes docker locais sem apagar volumes"
	@echo "  make logs         - acompanha logs do servico api"
	@echo "  make shell        - abre shell Django via container dev"
	@echo ""
	@echo "Banco e app:"
	@echo "  make migrate      - aplica migrations no banco do compose dev"
	@echo "  make schema       - gera schema OpenAPI em docs/_build/schema.yml"
	@echo ""
	@echo "Qualidade:"
	@echo "  make test         - executa pytest em container"
	@echo "  make coverage     - gera relatorio de coverage"
	@echo "  make lint         - executa black --check e ruff"
	@echo "  make typecheck    - executa mypy"
	@echo "  make docs         - gera documentacao Sphinx"
	@echo "  make docs-clean   - remove artefatos de docs"
	@echo "  make precommit    - executa os hooks do pre-commit em container"
	@echo "  make quality      - executa lint, typecheck, test e docs"
	@echo ""
	@echo "Limpeza:"
	@echo "  make clean-local  - remove artefatos locais temporarios"

ensure-env:
	@test -f .env || cp .env.example .env

up: ensure-env
	$(COMPOSE_DEV) up --build

up-prod: ensure-env
	$(COMPOSE) up --build

down:
	$(COMPOSE_DEV) down
	$(COMPOSE) down

build: ensure-env
	$(COMPOSE_DEV) build

build-prod: ensure-env
	$(COMPOSE) build

logs: ensure-env
	$(COMPOSE_DEV) logs -f api

shell: ensure-env
	$(RUN_API) python manage.py shell

migrate: ensure-env
	$(RUN_API) python manage.py migrate --noinput

test: ensure-env
	$(RUN_API_NODEPS) python -m pytest $(PYTEST_ARGS)

coverage: ensure-env
	$(RUN_API_NODEPS) sh -c 'rm -rf docs/_cov && COVERAGE_FILE=/tmp/.coverage python -m coverage erase && COVERAGE_FILE=/tmp/.coverage python -m coverage run --source=apps -m pytest $(PYTEST_ARGS) && COVERAGE_FILE=/tmp/.coverage python -m coverage report -m && COVERAGE_FILE=/tmp/.coverage python -m coverage html -d docs/_cov'

lint: ensure-env
	$(RUN_API_NODEPS) sh -c 'RUFF_CACHE_DIR=/tmp/.ruff_cache python -m black --check apps config manage.py && RUFF_CACHE_DIR=/tmp/.ruff_cache python -m ruff check apps config manage.py'

typecheck: ensure-env
	$(RUN_API_NODEPS) python -m mypy --cache-dir /tmp/.mypy_cache apps config

schema: ensure-env
	$(RUN_API_NODEPS) sh -c 'mkdir -p docs/_build && python manage.py spectacular --file docs/_build/schema.yml'

docs: ensure-env
	$(RUN_API_NODEPS) sh -c 'rm -rf docs/_build/html docs/_build/doctrees && python -m sphinx -b html docs docs/_build/html'

docs-clean:
	rm -rf docs/_build docs/_cov

precommit: ensure-env
	$(RUN_API_NODEPS) sh -c 'git config --global --add safe.directory /app && python -m pre_commit run --files $$(find apps config docs requirements scripts testes -type f) .env.example .gitignore .pre-commit-config.yaml Dockerfile Dockerfile.dev docker-compose.yml docker-compose-dev.yml pyproject.toml README.md CHANGELOG.md Makefile manage.py'

quality: lint typecheck test docs

clean-local:
	rm -rf .venv .pytest_cache .mypy_cache .ruff_cache htmlcov docs/_build docs/_cov recreio_ferias_backend.egg-info .coverage db.sqlite3
	find . -type d -name '__pycache__' -prune -exec rm -rf {} +