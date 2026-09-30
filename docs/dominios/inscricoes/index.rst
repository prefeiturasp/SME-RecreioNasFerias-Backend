Inscrições
==========

Este domínio é responsável pelo cadastro e pela gestão das inscrições de
participantes no programa Recreio nas Férias. A inscrição reúne as
informações básicas do participante, o grupo, o tipo de estudante, o polo e,
opcionalmente, a edição vinculada.

Visão resumida
--------------

- endpoint base: ``/api/v1/inscricoes/``
- entidade principal: ``Inscricao``
- serviço: ``InscricaoService``
- acesso: todas as rotas exigem autenticação
- identificação pública: UUID
- vínculo com edição: opcional nesta fase

Modelo e choices
----------------

O domínio utiliza uma única entidade lógica para o cadastro completo. Os
campos de saúde e informações por grupo poderão ser adicionados ao mesmo
modelo em etapas posteriores.

Os principais campos são:

- ``tipo_estudante`` e ``grupo``
- ``codigo_eol`` e ``cpf``
- ``nome_participante`` e ``data_nascimento``
- ``responsavel_nome`` e ``responsavel_nome_social``
- ``cep``, ``tipo_logradouro``, ``logradouro``, ``numero``, ``complemento``,
  ``bairro`` e ``cidade``
- ``telefone_contato_1``, ``telefone_contato_2`` e ``email``
- ``dre_codigo_eol`` e ``dre_nome``
- ``polo`` e ``edicao``
- ``status``

Os choices de grupo são:

- ``BERCARIO_I`` — Berçário I
- ``BERCARIO_II`` — Berçário II
- ``MINI_GRUPO_I`` — Mini Grupo I
- ``MINI_GRUPO_II`` — Mini Grupo II
- ``QUATRO_A_14_ANOS`` — 4 a 14 anos

Os tipos de estudante são ``ESTUDANTE_DA_REDE`` e
``ESTUDANTE_EXTERNO``. Os status são ``RASCUNHO``, ``COMPLETA`` e
``CANCELADA``.

Regras de negócio
-----------------

Uma inscrição é considerada ``COMPLETA`` quando os seguintes dados estão
preenchidos:

- tipo de estudante e grupo;
- nome do participante e data de nascimento;
- nome do responsável;
- CEP, tipo de logradouro, logradouro, número, bairro e cidade;
- telefone de contato/emergência 1 e e-mail;
- DRE e polo.

O Código EOL é obrigatório para estudante da rede. O CPF é obrigatório para
estudante externo. A ausência de qualquer dado obrigatório mantém ou reverte
a inscrição para ``RASCUNHO``.

Berçário I/II e Mini Grupo I/II só podem ser utilizados por estudantes da
rede. O grupo ``QUATRO_A_14_ANOS`` pode ser utilizado por estudantes da rede
ou externos.

A unicidade lógica é validada dentro do polo:

- um Código EOL informado não pode se repetir no mesmo polo;
- um CPF informado não pode se repetir no mesmo polo;
- valores ausentes não participam da validação de duplicidade.

O polo selecionado precisa estar atualmente ativo e ter sido classificado
como ``oficial`` ao menos uma vez em ``DefinicaoPolo``. Essa elegibilidade é
histórica quanto ao tipo, mas considera o status atual do polo. A DRE
informada deve corresponder à DRE cadastrada no polo.

O status ``CANCELADA`` é definido somente por ação manual e permanece até a
ação explícita de reativação. A reativação recalcula o status como
``COMPLETA`` ou ``RASCUNHO`` conforme os dados existentes.

Serializers
-----------

``InscricaoInformacoesBasicasSerializer``
    Contrato de criação e atualização das informações básicas. Recebe os
    UUIDs de polo e edição.

``InscricaoListagemSerializer``
    Retorna os campos usados na listagem, incluindo ``polo_nome`` e os
    labels amigáveis dos choices.

``InscricaoDetalheSerializer``
    Serializer somente leitura para o detalhe. O campo ``polo`` utiliza
    ``PoloResumoSerializer`` e retorna ``uuid`` e ``nome_polo``. O campo
    ``edicao`` utiliza ``EdicaoResumoSerializer`` e retorna ``uuid`` e
    ``nome``.

``PoloElegivelSerializer``
    Retorna os dados de polos que podem ser selecionados no cadastro.

Todos os serializers de inscrição que exibem choices também retornam:
``tipo_estudante_label``, ``grupo_label`` e ``status_label``. Esses valores
são derivados dos métodos ``get_*_display()`` gerados pelo Django.

O endpoint ``valores-choices`` fornece os valores técnicos e labels de grupo,
tipo de estudante e status para montagem de componentes no Front.

Contrato HTTP
-------------

``GET /api/v1/inscricoes/``
    Lista inscrições. Os filtros são combinados com ``AND`` e incluem
    ``tipo_estudante``, ``polo``, ``codigo_eol``, ``cpf``,
    ``nome_participante``, ``grupo`` e ``status``.

``POST /api/v1/inscricoes/``
    Cria uma inscrição. O status não é controlado pelo cliente; o modelo o
    deriva do conteúdo informado.

``GET /api/v1/inscricoes/<uuid>/``
    Retorna o detalhe da inscrição, com nomes resumidos de polo e edição.

``PUT`` e ``PATCH``
    Atualizam a inscrição por meio do ``InscricaoService``. Campos protegidos
    como UUID, status e ativo não são aceitos como controle pelo cliente.

``DELETE /api/v1/inscricoes/<uuid>/``
    Remove fisicamente a inscrição.

``POST /api/v1/inscricoes/<uuid>/cancelar/``
    Executa o cancelamento manual.

``POST /api/v1/inscricoes/<uuid>/reativar/``
    Reativa a inscrição e recalcula seu status.

``GET /api/v1/inscricoes/polos-elegiveis/``
    Lista polos ativos que já foram oficiais. Aceita o filtro opcional
    ``dre_codigo_eol`` e os parâmetros de paginação compartilhados.

``GET /api/v1/inscricoes/valores-choices/``
    Retorna listas com ``value`` e ``label`` para os choices do domínio.

Status e persistência
---------------------

O cálculo do status ocorre no ``save()`` do modelo. A criação e a atualização
passam pelo service, que mantém a orquestração e as transações fora da camada
HTTP. ``refresh_from_db()`` é utilizado antes de atualizar, cancelar ou
reativar uma inscrição para trabalhar com o estado persistido mais recente.

O domínio usa ``select_related`` para carregar polo e edição nas consultas de
listagem e detalhe. A seleção de edição continua opcional até que a regra de
vinculação seja definida.

Testes
------

Os testes ficam em ``apps/inscricoes/tests/``:

- ``test_admin.py`` — registro e formulário do Admin;
- ``test_models.py`` — defaults, status, completude e representação;
- ``test_serializers.py`` — contratos básicos, listagem, detalhe e polos;
- ``test_services.py`` — criação, atualização, filtros, cancelamento,
  reativação e polos elegíveis;
- ``test_validators.py`` — completude, unicidade, DRE, polo e grupo/tipo;
- ``test_views.py`` — autenticação, CRUD, filtros, actions, choices e
  paginação.

As factories e fixtures são compartilhadas em ``apps/factories.py`` e
``apps/conftest.py``. O domínio possui 100% de cobertura de statements e
branches.
