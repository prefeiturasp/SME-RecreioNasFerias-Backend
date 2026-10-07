# language: pt
Funcionalidade: Autenticacao
  Como um consumidor da API
  Quero autenticar usuarios, gerenciar tokens e consultar meu perfil
  Para gerenciar minha sessao institucional

  Cenario: Realizar login institucional com credenciais validas
    Quando eu envio as credenciais para o login institucional
    Entao a API deve responder com status 200
    E a resposta deve conter um token JWT

  Cenario: Recusar login com credenciais invalidas
    Quando eu envio credenciais invalidas para o login institucional
    Entao a API deve responder ao login com status 401

  Cenario: Recusar login com payload invalido
    Quando eu envio um payload invalido para o login institucional
    Entao a API deve responder ao login com status 400

  Cenario: Realizar logout institucional com token valido
    Dado que estou autenticado na API
    Quando eu envio a requisicao de logout institucional
    Entao a API deve responder ao logout com status 204

  Cenario: Tornar logout sem token uma operacao idempotente
    Quando eu envio a requisicao de logout sem token
    Entao a API deve responder ao logout sem token com status 204

  Cenario: Tornar logout com token invalido uma operacao idempotente
    Quando eu envio a requisicao de logout com token invalido
    Entao a API deve responder ao logout com token invalido com status 204

  Cenario: Renovar o token usando o refresh token gerado no login
    Dado que o login institucional foi realizado para renovar o token
    Quando eu envio a requisicao de renovacao do token
    Entao a API deve responder a renovacao com status 200
    E a resposta da renovacao deve conter um novo token

  Cenario: Recusar renovacao sem refresh token
    Dado que o login institucional foi realizado para renovar o token
    E o refresh token foi removido da sessao
    Quando eu envio a requisicao de renovacao do token
    Entao a API deve responder a renovacao sem refresh token com status 400

  Cenario: Verificar token gerado pelo login
    Dado que o login institucional foi realizado para verificar o token
    Quando eu envio o token para verificacao
    Entao a API deve responder a verificacao com status 200

  Cenario: Recusar verificacao de token invalido
    Quando eu envio um token invalido para verificacao
    Entao a API deve responder a verificacao com status 401

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
