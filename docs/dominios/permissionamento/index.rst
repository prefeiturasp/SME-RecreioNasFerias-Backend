Permissionamento e RBAC
=========================

O módulo de permissionamento usa ``django.contrib.auth.models.Group`` como
papel e ``Permission`` como autorização. As permissões podem ser concedidas
por grupo ou diretamente ao usuário. Os domínios fazem a verificação nas
classes DRF ``BasePermission`` de seus arquivos ``permissions.py``.

Autenticação e autorização
--------------------------

O CoreSSO continua autenticando usuários com cargos autorizados. A migration
associa ``USUARIO_UE`` às contas existentes com cargo permitido. Após um login
bem-sucedido, contas novas sem grupos ou permissões individuais recebem esse
papel. Se a conta já possuir grupo ou permissão individual, o login preserva
essa configuração. A migration associa o RF configurado em
``PRIMEIRO_ADMIN_COCEU_RF`` ao papel ``ADMINISTRADOR_COCEU`` sem converter a
conta em superusuário.

O catálogo atual de perfis é retornado em ``GET /api/v1/perfis/``. A rota exige
autenticação e a permissão ``core.visualizar_usuarios``. Cada item contém o ID
do grupo, seu código estável, nome, descrição e permissões por recurso. A
resposta ``GET /api/v1/auth/me/`` informa os códigos dos perfis e as permissões
efetivas do usuário autenticado.

Matriz aplicada
---------------

``Gerenciar`` corresponde a criar, visualizar, editar e excluir. O catálogo
ativo contempla usuários, polos, edições, definições de polos e inscrições de
participantes. Exportação e recursos ainda sem endpoints ficam fora do catálogo
até que suas rotas sejam implementadas. As permissões de CRUD de usuários já
estão disponíveis para o futuro endpoint de gestão de usuários.

A consulta ``GET /api/v1/polos/dres/`` possui a permissão específica
``core.visualizar_dres``. Ela é concedida aos perfis com consulta de polos e a
``USUARIO_UE``, permitindo buscar DREs durante o cadastro de inscrições sem
conceder ao perfil Usuário UE acesso geral às rotas de polos.

.. list-table:: Permissões por perfil
   :header-rows: 1

   * - Recurso
     - Administrador COCEU
     - Gestor DICEU
     - Gestor CODAE
     - Gestor ASCOM
     - Gestor COGED
     - Gestor de Polo
     - Usuário UE
   * - Usuários
     - Gerenciar
     - Visualizar
     - Nenhum
     - Nenhum
     - Nenhum
     - Nenhum
     - Nenhum
   * - Polos
     - Gerenciar
     - Gerenciar
     - Visualizar
     - Visualizar
     - Nenhum
     - Visualizar
     - Nenhum
   * - Edições do Programa
     - Gerenciar
     - Visualizar
     - Visualizar
     - Visualizar
     - Visualizar
     - Visualizar
     - Nenhum
   * - Inscrições de Participantes
     - Gerenciar
     - Visualizar
     - Visualizar
     - Nenhum
     - Nenhum
     - Visualizar
     - Criar, Visualizar e Editar
   * - Definições de Polos
     - Gerenciar
     - Gerenciar
     - Nenhum
     - Nenhum
     - Nenhum
     - Gerenciar
     - Nenhum

Implementação presente
----------------------

As regras estão ligadas aos ViewSets de edições, polos, definições de polos e
inscrições. Ações auxiliares de leitura seguem a permissão de visualização;
cancelar e reativar inscrições exigem edição; ações em massa de definições
exigem criação ou edição conforme a operação. O endpoint de perfis exige a
permissão de visualizar usuários e lista os sete grupos disponíveis. As
permissões de CRUD de usuários ficam provisionadas para a futura API de gestão.

Exportação e permissões de parceiros, profissionais, inscrições profissionais,
cronogramas, ocorrências, aferição, frequência qualitativa e relatórios não
fazem parte do catálogo ativo. Elas devem ser incluídas quando os respectivos
endpoints forem implementados.

Configuração inicial
--------------------

A migration ``core.0005_permissionamento_customizado`` cria os grupos e suas
permissões de forma idempotente, associa usuários existentes com cargo
permitido a ``USUARIO_UE``, cria o usuário inicial se necessário e o associa a
``ADMINISTRADOR_COCEU``. Ela falha explicitamente se
``PRIMEIRO_ADMIN_COCEU_RF`` estiver ausente, se o RF estiver associado a mais
de uma conta ou se a conta encontrada estiver inativa. Se o RF encontrar uma
conta existente com ``rf`` vazio, apenas esse campo e o grupo são atualizados.

Configure ``PRIMEIRO_ADMIN_COCEU_RF`` antes de aplicar a migration em cada
ambiente. Não versione o RF nem use ``is_superuser`` como substituto do papel.
