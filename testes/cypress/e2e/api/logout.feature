# language: pt
Funcionalidade: Encerramento da sessao institucional
  Como um usuario autenticado
  Quero encerrar minha sessao
  Para invalidar meu acesso atual

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