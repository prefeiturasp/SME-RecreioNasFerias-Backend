Definições de Polos
===================

Este domínio representa a participação de um polo em uma edição do
Recreio nas Férias. A definição reúne o tipo do polo na edição, a projeção
de inscritos, o total calculado de inscritos e os dados do ponto focal.

Visão resumida
--------------

- endpoint base: ``/api/v1/definicoes-polos/``
- entidade principal: ``DefinicaoPolo``
- serviço: ``DefinicaoPoloService``
- relacionamento: um polo pode participar de várias edições, mas apenas uma
  vez em cada edição
- acesso: todas as rotas exigem autenticação

Modelo e regras de negócio
--------------------------

Uma definição relaciona um ``Polo`` a uma ``Edicao`` e possui os seguintes
dados principais:

- ``tipo``: tipo do polo dentro da edição; novas definições começam como
  ``pendente``
- ``projecao_inscritos``: quantidade projetada de inscritos
- ``total_inscritos``: capacidade calculada automaticamente
- ``ponto_focal_nome``, ``ponto_focal_telefone`` e ``ponto_focal_email``:
  dados de contato do ponto focal

O campo ``total_inscritos`` é somente leitura e é recalculado a cada
persistência com acréscimo de 30% sobre a projeção, arredondando para baixo:

``total_inscritos = projecao_inscritos * 130 // 100``

A projeção não pode ser negativa. O par ``polo`` e ``edicao`` é único, e a
tentativa de criar uma participação duplicada resulta em erro de validação.

Cadastro e manutenção
---------------------

O CRUD padrão utiliza UUIDs públicos para identificar as definições.

``POST /api/v1/definicoes-polos/`` cria um vínculo entre um polo e uma
edição. O serviço força o tipo inicial para ``pendente`` e calcula o total de
inscritos.

``GET /api/v1/definicoes-polos/<uuid>/`` retorna o detalhamento da
participação, incluindo os dados completos do polo e um resumo da edição.

``PATCH`` e ``PUT`` atualizam os dados editáveis. O total de inscritos,
UUID, estado de atividade e timestamps são controlados pelo domínio e não
podem ser alterados diretamente.

``DELETE`` remove a participação.

Listagem consolidada
--------------------

``GET /api/v1/definicoes-polos/`` retorna polos com os dados da definição
associada à edição informada. Sem o parâmetro ``edicao``, a consulta usa a
participação mais recente de cada polo; polos sem definição também podem
aparecer, usando o tipo cadastrado no polo como fallback.

Filtros disponíveis:

- ``dre_codigos_eol``: um ou mais códigos de DRE; aceita parâmetros
  repetidos ou separados por vírgula
- ``tipo_ue``: sigla do tipo de unidade escolar
- ``busca``: nome do polo ou código EOL
- ``gestao``: gestão do polo
- ``edicao``: UUID da edição; quando informado, somente polos vinculados a
  essa edição são retornados
- ``tipo_polo``: tipo da participação mais recente
- ``page_size`` e ``desabilita_paginacao``: controles de paginação

Antes da listagem, o domínio tenta sincronizar os polos de gestão direta com
a EOL. Falhas nessa sincronização são registradas em log e não impedem a
consulta das definições já persistidas.

O resultado da listagem usa ``PoloComDefinicaoSerializer`` e inclui, entre
outros, os campos:

- ``polo_uuid``
- ``codigo_eol`` e ``nome_polo``
- ``dre_nome`` e ``dre_codigo_eol``
- ``tipo_ue``, ``gestao`` e ``status``
- ``definicao_uuid`` e ``edicao_uuid``
- ``nome_edicao``
- ``tipo_polo_edicao``
- ``projecao_inscritos_edicao``
- ``total_inscritos_edicao``

Histórico do polo
-----------------

``GET /api/v1/definicoes-polos/historico/?polo=<uuid>`` lista todas as
participações de um polo, ordenadas conforme a definição do modelo. O
parâmetro ``polo`` é obrigatório e a resposta contém os dados resumidos de
cada edição, o tipo, a projeção, o total calculado e os dados do ponto focal.

A action aceita os parâmetros usuais de paginação, incluindo
``desabilita_paginacao=true``.

Ações em massa
--------------

Vinculação em massa
~~~~~~~~~~~~~~~~~~~

``POST /api/v1/definicoes-polos/vincular-em-massa/`` cria participações para
uma lista de polos em uma edição:

.. code-block:: json

   {
     "polos": ["<uuid-do-polo-1>", "<uuid-do-polo-2>"],
     "edicao": "<uuid-da-edicao>",
     "projecao_inscritos": 200
   }

Polos já vinculados à edição são retornados em ``ignorados``; os novos
vínculos são retornados em ``criadas``. A lista de polos não pode conter UUIDs
repetidos.

Alteração de tipo em massa
~~~~~~~~~~~~~~~~~~~~~~~~~~

``POST /api/v1/definicoes-polos/alterar-tipo-em-massa/`` recebe uma lista de
operações com ``polo_uuid``, ``edicao`` e ``tipo``. Operações sem edição são
ignoradas e retornadas com o motivo. Quando a edição é informada, o vínculo é
criado com projeção zero caso ainda não exista, ou atualizado caso já exista.

Alteração de edição em massa
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``POST /api/v1/definicoes-polos/alterar-edicao-em-massa/`` move definições
selecionadas para uma edição de destino:

.. code-block:: json

   {
     "definicoes": ["<uuid-da-definicao-1>", "<uuid-da-definicao-2>"],
     "edicao_destino": "<uuid-da-edicao>"
   }

A operação é rejeitada quando o destino já possui o mesmo polo ou quando
mais de uma definição do mesmo polo é enviada para a mesma edição.

Erros e validações
------------------

Os UUIDs de polos, edições e definições são validados antes da execução das
ações. Recursos inexistentes retornam erro de validação HTTP ``400`` com a
indicação do campo correspondente.

As operações de serviço são transacionais. Em caso de falha de validação ou
conflito de negócio, nenhuma alteração parcial é persistida.
