# language: pt
Funcionalidade: Perfil do usuario autenticado
  Como um usuario autenticado
  Quero consultar meu perfil
  Para obter meus dados cadastrais

  Cenario: Consultar perfil com token gerado pelo login
    Dado que o login institucional foi realizado
    Quando eu consulto meu perfil autenticado
    Entao a API deve responder ao perfil com status 200
    E a resposta do perfil deve conter os dados do usuario

  Cenario: Recusar consulta de perfil sem token
    Quando eu consulto meu perfil sem token
    Entao a API deve responder ao perfil com status 401

  Cenario: Recusar consulta de perfil com token invalido
    Quando eu consulto meu perfil com token invalido
    Entao a API deve responder ao perfil com status 401