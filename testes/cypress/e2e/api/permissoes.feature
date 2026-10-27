# language: pt
@perfis
Funcionalidade: Perfis e permissoes
  Cenario: Listar perfis com autenticacao
    Dado que autentiquei para consultar perfis
    Quando consulto a lista de perfis
    Entao a consulta de perfis deve retornar 200
    E os perfis e permissoes devem respeitar o contrato

  Esquema do Cenario: Recusar consulta de perfis com token <token>
    Quando consulto perfis com token "<token>"
    Entao a consulta de perfis deve retornar 401

    Exemplos:
      | token |
      | ausente |
      | invalido |
