# language: pt
Funcionalidade: Renovacao do token de acesso
  Como um usuario autenticado
  Quero renovar meu token de acesso
  Para manter minha sessao ativa

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