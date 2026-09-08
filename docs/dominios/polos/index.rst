Polos
=====

Esta página documenta a população de polos de gestão direta a partir da
integração EOL.

Visão resumida
--------------

- endpoint: ``POST /api/v1/polos/popular/``
- orquestração: ``PoloService.popular_unidades_diretas()``
- integração consumida: ``EolPort`` em ``apps/integracoes/eol/``
- persistência: tabela ``polos_polo``, com ``gestao=direta`` e
  ``tipo=pendente``

Fluxo
-----

A action autenticada não recebe payload. O serviço:

1. verifica se a carga do dia já rodou (fuso ``America/Sao_Paulo``)
2. lista e filtra as unidades elegíveis na EOL
3. compara pelo ``codigo_eol`` apenas com polos de gestão direta
4. enriquece em lotes de 40 somente as unidades ainda inexistentes
5. grava os polos novos e registra a execução

Quando a carga do dia já ocorreu, a API responde ``200`` com
``executada=false`` e ``motivo_ignorada=ja_executada_hoje``, sem nova
consulta à EOL.

Persistência
------------

Cada unidade nova vira um ``Polo`` com:

- ``gestao=direta``
- ``tipo=pendente``
- ``status=ativo``
- ``quantidade_maxima_alunos=1``
- endereço em campos separados (``cep``, ``tipo_logradouro``,
  ``logradouro``, ``bairro``, ``numero`` e ``complemento``)

A rotina só cria polos. Unidades já persistidas não são atualizadas nem
desativadas. A última execução bem-sucedida fica em
``ControleSincronizacaoPolos``, chave ``unidades_diretas``.

Contrato HTTP
-------------

Resposta em snake_case:

- ``total_consultados``
- ``total_novos``
- ``total_ja_existentes``
- ``unidades_novas``
- ``executada``
- ``motivo_ignorada``
- ``ultima_execucao_em``

Falhas de configuração da EOL retornam ``500``. Indisponibilidade ou
quebra de contrato retornam ``502``, no padrão ``{"detalhe": "..."}``.

Tipos de unidade elegíveis
--------------------------

O filtro de tipos de UE fica na integração EOL, em
``SIGLAS_TIPO_UE_RECREIO``. A lista atual está em
``docs/dominios/integracoes/eol/``.
