
# language: pt
Funcionalidade: Autenticacao institucional
  Como um consumidor da API
  Quero autenticar um usuario institucional
  Para obter um token JWT

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