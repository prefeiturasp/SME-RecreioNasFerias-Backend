# language: pt
Funcionalidade: Verificacao do token de acesso
  Como um consumidor da API
  Quero verificar a validade de um token
  Para confirmar se ele pode ser utilizado

  Cenario: Verificar token gerado pelo login
    Dado que o login institucional foi realizado para verificar o token
    Quando eu envio o token para verificacao
    Entao a API deve responder a verificacao com status 200

  Cenario: Recusar verificacao de token invalido
    Quando eu envio um token invalido para verificacao
    Entao a API deve responder a verificacao com status 401