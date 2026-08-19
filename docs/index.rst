SME Recreio nas Férias Backend
==============================

Backend Django do SME Recreio nas Férias com execução recomendada via Docker
Compose e estrutura técnica validada localmente.

.. toctree::
   :maxdepth: 2
   :caption: Conteúdo

   getting_started
   configuration
   arquitetura
   dominios/index

Visão geral
-----------

A pasta ``docs/`` concentra os guias operacionais e estruturais do projeto. O
objetivo desta documentação é reduzir ambiguidade no onboarding e deixar claro
como a estrutura atual deve ser executada, configurada e evoluída.

Passo mínimo para iniciar o projeto localmente::

   cp .env.example .env
   make up

Depois do bootstrap, os pontos mais importantes ficam disponíveis em:

- ``/api/v1/health/`` para healthcheck
- ``/api/v1/schema/`` para schema OpenAPI
- ``/api/v1/docs/`` para Swagger UI

Os pontos de entrada da documentação ficaram organizados assim:

- ``getting_started`` para subida, validação e operação local.
- ``configuration`` para variáveis de ambiente e comportamento de runtime.
- ``arquitetura`` para a organização da estrutura e os critérios de evolução.
- ``dominios`` para a documentação aprofundada de áreas específicas, como
   integrações e regras que não cabem na visão geral.
- ``README.md`` para entrada rápida na raiz do repositório.

Índices e tabelas
-----------------

* :ref:`genindex`
* :ref:`search`
