Edições
======

Este domínio representa as edições do programa Recreio nas Férias. Uma
edição define o período em que as atividades acontecem, o período de
inscrições e o status do seu ciclo de vida.

Visão resumida
--------------

- endpoint base: ``/api/v1/edicoes/``
- entidade principal: ``Edicao``
- serviço: ``EdicaoService``
- status possíveis: ``planejada``, ``ativa`` e ``encerrada``
- acesso: todas as rotas exigem autenticação

Modelo
------

Cada edição possui os seguintes dados de planejamento:

- ``nome``: identificação única da edição, sem distinção entre maiúsculas e
  minúsculas
- ``data_inicio`` e ``data_fim``: período de realização da edição
- ``inscricoes_inicio`` e ``inscricoes_fim``: período em que as inscrições
  ficam disponíveis
- ``status``: situação atual da edição, calculada automaticamente

O modelo também possui indicadores consolidados, mantidos como somente
leitura pela API:

- ``quantidade_inscritos``
- ``quantidade_atendimento_efetivo``
- ``quantidade_passeios``
- ``quantidade_apresentacoes``

Esses indicadores começam com valor zero e serão atualizados conforme os
domínios responsáveis por inscrições, atendimentos e atividades forem
integrados.

Regras de negócio
-----------------

Os períodos devem respeitar as seguintes regras:

- a data final da edição não pode ser anterior à data inicial
- a data final das inscrições não pode ser anterior à data inicial das
  inscrições
- as inscrições devem terminar até o último dia da edição
- os períodos de realização e de inscrições não podem se sobrepor aos de
  outra edição
- somente uma edição pode estar ativa simultaneamente
- o nome não pode ser repetido entre edições

As validações são centralizadas no domínio e executadas antes da
persistência, retornando mensagens associadas aos campos quando aplicável.

Ciclo de vida e status automático
----------------------------------

O status é calculado com base na data atual, considerando os limites do
período de forma inclusiva:

- antes de ``data_inicio``: ``planejada``
- entre ``data_inicio`` e ``data_fim``: ``ativa``
- após ``data_fim``: ``encerrada``

As operações de listagem e consulta sincronizam os status antes de retornar
os dados. A sincronização bloqueia as edições em ordem determinística dentro
de uma transação, encerra primeiro as edições finalizadas e só então promove
a edição correspondente ao período atual. Isso evita conflitos com a regra
de edição ativa única.

Uma edição encerrada não pode ser atualizada nem excluída. Alterações nos
dados cadastrais ou nos indicadores consolidados de uma edição já encerrada
também são rejeitadas pelo modelo.

Contrato HTTP
-------------

O CRUD utiliza UUIDs públicos para identificar as edições.

``GET /api/v1/edicoes/``
    Lista as edições ordenadas por ``data_inicio`` e ``nome``. Antes da
    resposta, atualiza os status automáticos.

``POST /api/v1/edicoes/``
    Cria uma edição. O status informado pelo cliente é ignorado e a nova
    edição começa como ``planejada``; o status efetivo é recalculado conforme
    as datas.

``GET /api/v1/edicoes/<uuid>/``
    Recupera uma edição específica pelo UUID.

``PUT`` e ``PATCH``
    Atualizam os campos editáveis de uma edição que ainda não foi encerrada.
    Status, indicadores, UUID, timestamps e estado de atividade são somente
    leitura.

``DELETE /api/v1/edicoes/<uuid>/``
    Exclui uma edição que ainda não foi encerrada.

O serializer da API retorna, além dos dados de período e status, os quatro
indicadores consolidados e os metadados de auditoria ``criado_em`` e
``atualizado_em``.

Integração com outros domínios
------------------------------

As definições de polos usam a edição como referência para vincular polos,
projeções de inscritos, tipos de participação e dados de ponto focal. O
serializer resumido de edição, utilizado nesses vínculos, expõe apenas
``uuid`` e ``nome``.

O domínio de Edições não calcula diretamente os indicadores consolidados. Os
campos são preparados para receber dados dos domínios de inscrições,
atendimento e atividades, mantendo a edição como ponto de consolidação.

Erros e validações
------------------

Conflitos de nome, período ou edição ativa retornam erro de validação HTTP
``400``. Tentativas de alterar ou excluir edição encerrada também retornam
``400`` com a mensagem de regra de negócio correspondente.

Todas as operações de criação, atualização, exclusão e sincronização de
status são transacionais.
