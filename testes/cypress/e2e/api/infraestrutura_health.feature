# language: pt
Funcionalidade: Qualidade da infraestrutura
  Como um consumidor da API
  Quero verificar a qualidade da aplicacao
  Para confirmar que o servico esta disponivel

  Cenario: Verificar a qualidade da aplicacao
    Quando eu consulto o healthcheck da infraestrutura
    Entao a API deve responder ao healthcheck com status 200
    E a qualidade da aplicacao deve ser ok