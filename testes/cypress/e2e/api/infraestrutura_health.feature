# language: pt
Funcionalidade: Infraestrutura
  Como um consumidor da API
  Quero verificar a qualidade da aplicacao
  Para confirmar que o servico esta disponivel

  Cenario: Consultar healthcheck publico sem token
    Quando eu consulto o healthcheck da infraestrutura
    Entao a API deve responder ao healthcheck com status 200
    E a qualidade da aplicacao deve ser ok
    E o healthcheck deve retornar o contrato JSON esperado

  Cenario: Consultar healthcheck publico com token invalido
    Quando eu consulto o healthcheck com token invalido
    Entao a API deve responder ao healthcheck com status 200
    E o healthcheck deve retornar o contrato JSON esperado

  Cenario: Consultar disponibilidade usando HEAD
    Quando eu consulto o healthcheck usando "HEAD"
    Entao a API deve responder ao healthcheck com status 200
    E o healthcheck nao deve retornar corpo

  Cenario: Consultar os metodos permitidos usando OPTIONS
    Quando eu consulto o healthcheck usando "OPTIONS"
    Entao a API deve responder ao healthcheck com status 200
    E o healthcheck deve permitir apenas GET HEAD e OPTIONS

  Esquema do Cenario: Recusar metodo <metodo> no healthcheck
    Quando eu consulto o healthcheck usando "<metodo>"
    Entao o healthcheck deve rejeitar o metodo com status 405
    E o healthcheck deve permitir apenas GET HEAD e OPTIONS
    E o healthcheck deve informar o erro em JSON

    Exemplos:
      | metodo |
      | POST   |
      | PUT    |
      | PATCH  |
      | DELETE |
