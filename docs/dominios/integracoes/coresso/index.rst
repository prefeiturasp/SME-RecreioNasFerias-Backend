CoreSSO
=======

Esta página documenta a integração de autenticação institucional com o
CoreSSO, incluindo contrato externo, normalização interna, política de cargo
efetivo e gestão local de sessão JWT.

Visão resumida
--------------

- endpoint externo consumido: ``POST /api/v1/autenticacao/externa``
- app de integração: ``apps/integracoes/coresso/``
- orquestração local do login: ``apps/core/services/auth_service.py``
- endpoints públicos do fluxo: ``/api/v1/auth/``

Contrato externo consumido
--------------------------

Payload enviado ao CoreSSO:

.. code-block:: json

   {
     "usuario": "usuario_teste",
     "senha": "credencial_teste",
     "codigoSistema": 1009
   }

Campos de resposta relevantes hoje:

- ``usuarioId``
- ``nome``
- ``codigoRf``
- ``numeroDocumento``
- ``email``
- ``perfis``
- ``cargos``
- ``cargosSobrePosto``
- ``unidadesLotacao``
- ``unidadeExercicio``

Normalização interna
--------------------

O backend não propaga o payload cru do provedor para o restante da aplicação.
Ele o converte em um contrato interno tipado em ``apps/integracoes/coresso/``.

As decisões principais de mapeamento são:

- ``codigoRf`` -> ``rf`` local
- ``numeroDocumento`` -> ``cpf`` local
- ``cargos`` e ``cargosSobrePosto`` -> coleções tipadas de cargos
- ``unidadesLotacao`` e ``unidadeExercicio`` -> objetos tipados de unidade

Regra de cargo efetivo
----------------------

A regra aplicada pelo backend é:

1. quando ``cargosSobrePosto`` vier preenchido, ele prevalece;
2. quando ``cargosSobrePosto`` vier vazio ou ausente, o sistema usa ``cargos``.

Essa precedência vale para:

- autorização do login
- seleção do cargo permitido vinculado ao usuário local
- cargo retornado no contrato HTTP de login e ``me``
- auditoria de login

Autorização local
-----------------

O CoreSSO autentica identidade, mas não decide sozinho o acesso ao sistema.
Após o login externo, o backend cruza os códigos de cargo efetivo com a tabela
local ``usuarios_cargos_permitidos``.

Se nenhum código estiver autorizado localmente, o backend responde ``403``.

Vínculo local do cargo autorizado
---------------------------------

Para este sistema, o usuário autenticado opera com um único cargo de acesso.
Por isso, após validar os cargos efetivos recebidos do CoreSSO, o backend
seleciona o primeiro cargo autorizado na whitelist local e o vincula ao usuário
por ``ForeignKey`` em ``Usuario.cargo_permitido``.

Essa decisão simplifica a modelagem porque:

- a regra de negócio usa um único cargo autorizado por usuário;
- o ``/api/v1/auth/me/`` pode responder sem nova chamada externa;
- o cargo retornado pela API passa a vir do vínculo local autorizado;
- o modelo evita manter um JSON desnormalizado sem ganho funcional.

Se no futuro a integração passar a exigir múltiplos cargos simultâneos por
usuário, aí sim a próxima evolução natural será uma tabela própria de vínculo
entre usuário e cargos; não o retorno ao snapshot em JSON.

Sessão local
------------

Após o login bem-sucedido, a sessão passa a ser gerenciada localmente com
``djangorestframework-simplejwt``.

Decisões atuais:

- access token no corpo da resposta
- refresh token em cookie ``HttpOnly``
- rotação de refresh token ativa
- blacklist após rotação ativa
- endpoint ``/api/v1/auth/me/`` para bootstrap e validação de sessão

Endpoints expostos pelo backend
-------------------------------

- ``POST /api/v1/auth/login/``
- ``POST /api/v1/auth/token/refresh/``
- ``POST /api/v1/auth/token/verify/``
- ``POST /api/v1/auth/logout/``
- ``GET /api/v1/auth/me/``

Variáveis de ambiente usadas
----------------------------

Serviço backend:

- ``DJANGO_SECRET_KEY``
- ``DEBUG``
- ``ALLOWED_HOSTS``
- ``CORS_ALLOW_CREDENTIALS``
- ``CORS_ALLOWED_ORIGINS``
- ``CSRF_TRUSTED_ORIGINS``
- ``AUTH_REFRESH_COOKIE_SECURE``

Integração CoreSSO:

- ``AUTH_API_BASE_URL``
- ``AUTH_API_EOL_KEY``
- ``AUTH_API_AUTH_TIMEOUT_SECONDS``
- ``AUTH_API_CONNECT_TIMEOUT_SECONDS``
- ``AUTH_API_TIMEOUT_SECONDS``
- ``AUTH_CODIGO_SISTEMA``

Pontos de atenção para produção
-------------------------------
