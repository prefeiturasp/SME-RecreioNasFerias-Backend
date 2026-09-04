EOL / SME Integração
====================

Esta página documenta a integração de escolas com a SME Integração (EOL),
incluindo contrato externo, normalização interna, filtro de tipos de unidade e
enriquecimento das unidades elegíveis ao programa.

Visão resumida
--------------

- endpoints externos consumidos:
``GET /api/DREs``
``GET /api/escolas/tiposEscolas``
``GET /api/escolas/*``
- app de integração: ``apps/integracoes/eol/``
- contrato público consumido pelo domínio: ``EolPort``
- consumo previsto: sincronização de polos de gestão direta

Contrato externo consumido
--------------------------

A integração consome quatro endpoints, todos com o header ``x-api-eol-key``:

- ``GET /api/DREs`` — catálogo de Diretorias Regionais de Educação
- ``GET /api/escolas/tiposEscolas`` — catálogo de tipos de escola
- ``GET /api/escolas/todas-unidades`` — catálogo bruto de unidades escolares
- ``GET /api/escolas/dados/{eol}`` — dados detalhados da unidade
- ``GET /api/escolas/{eol}/funcionarios/cargos/{codigo}`` — funcionários no cargo

Campos do catálogo bruto usados hoje:

Para DREs:

- ``codigoDRE``
- ``nomeDRE``
- ``siglaDRE``
- ``codigoEscola``
- ``nomeEscola``
- ``siglaTipoEscola``
- ``nomeDRE``
- ``siglaDRE``
- ``codigoDRE``

Para tipos de escola:

- ``codigo``
- ``descricaoSigla``

Campos dos dados detalhados usados hoje:

- ``nome``
- ``siglaTipoEscola``
- ``nomeDRE`` / ``siglaDRE`` / ``codigoDRE``
- ``email``
- ``telefone``
- ``cep``
- ``tipoLogradouro`` / ``logradouro`` / ``numero`` / ``bairro`` / ``complemento``

Da consulta de funcionários por cargo, o sistema extrai ``nomeServidor`` do
primeiro registro retornado.

Normalização interna
--------------------

O backend não propaga os payloads brutos para o restante da aplicação. Ele os
converte em contratos internos tipados em ``apps/integracoes/eol/port.py``:

- ``UnidadeEol`` — unidade do catálogo bruto normalizada
- ``DreEol`` — Diretoria Regional de Educação normalizada
- ``TipoEscolaEol`` — tipo de unidade normalizado
- ``DadosUnidadeEol`` — dados detalhados normalizados (CEP e endereço em campos separados)
- ``UnidadeRecreioEol`` — unidade enriquecida pronta para a sincronização

Decisões principais de mapeamento:

- ``codigoEscola`` -> ``codigo_eol``
- ``cep`` é normalizado para o padrão ``00000-000``
- o endereço é mantido em campos separados: ``tipo_logradouro``,
  ``logradouro``, ``numero``, ``bairro`` e ``complemento``
- ``complemento`` fica vazio quando a integração não o envia
- os dados detalhados prevalecem sobre o catálogo bruto quando ambos existem

Filtro de tipos de unidade
--------------------------

Apenas unidades cujo ``siglaTipoEscola`` pertence ao conjunto elegível entram
no fluxo do Recreio nas Férias:

- ``EMEF``
- ``EMEI``
- ``EMEI P FOM``
- ``CEI DIRET``
- ``CEI INDIR``
- ``CEU``
- ``CEU EMEI``
- ``CEU CEI``
- ``CEU CEMEI``

O conjunto fica em ``SIGLAS_TIPO_UE_RECREIO``, em
``apps/integracoes/eol/constants.py``.

Enriquecimento
--------------

O ``EolAdapter`` oferece ``enriquecer_unidades``, que para cada unidade busca
dados detalhados e o nome do diretor.

Comportamentos importantes:

- enriquecimento executado em paralelo (``MAX_WORKERS_PADRAO = 8``)
- falhas pontuais em dados ou diretor não abortam o processo; nesses casos a
  unidade mantém apenas os dados do catálogo bruto
- o resultado é ordenado por nome da escola e código EOL
- ``listar_unidades_diretas_recreio(limite=None)`` integra filtro + limite +
  enriquecimento em uma única operação

Código do cargo de diretor
--------------------------

A consulta de diretor usa, por padrão, o código de cargo ``3360`` (Diretor de
Escola no catálogo oficial da SME), definido em
``CODIGO_CARGO_DIRETOR_ESCOLA``. O método ``obter_nome_diretor`` aceita um
código alternativo quando necessário.

Contrato público
----------------

O ``EolPort`` expõe as operações que o domínio consome:

- ``listar_dres()``
- ``listar_tipos_escola()``
- ``listar_todas_unidades()``
- ``obter_dados_unidade(codigo_eol)``
- ``obter_nome_diretor(codigo_eol, codigo_cargo=None)``
- ``filtrar_unidades_recreio(unidades)``
- ``enriquecer_unidades(unidades)``
- ``listar_unidades_diretas_recreio(limite=None)``

Exceções
--------

A integração traduz falhas em exceções específicas:

- ``EolConfigError`` — configuração ausente
- ``EolIndisponivelError`` — erro de rede ou HTTP 4xx/5xx
- ``EolContratoError`` — resposta fora do contrato esperado

Variáveis de ambiente usadas
----------------------------

A integração EOL reutiliza a mesma família ``AUTH_API_*`` da autenticação:

- ``AUTH_API_BASE_URL``
- ``AUTH_API_EOL_KEY``
- ``AUTH_API_CONNECT_TIMEOUT_SECONDS``
- ``AUTH_API_TIMEOUT_SECONDS``

Nenhuma variável nova foi introduzida para a integração de escolas.

Pontos de atenção para produção
-------------------------------

- os três endpoints dependem do header ``x-api-eol-key``; sem a chave a
  integração falha com ``EolConfigError``
- o timeout de leitura usa ``AUTH_API_TIMEOUT_SECONDS`` (60s), mais longo que
  o do login, porque a listagem completa e o enriquecimento são consultas
  pesadas
- a sincronização de polos diretos ainda não existe; quando for implementada,
  deve consumir ``EolPort`` sem acessar o client HTTP diretamente
