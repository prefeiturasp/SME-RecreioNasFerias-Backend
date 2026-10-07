# language: pt
@inscricoes
Funcionalidade: Inscrições
  Como um usuario autenticado
  Quero cadastrar e gerenciar inscricoes
  Para acompanhar os participantes

  Cenario: Criar e consultar inscricao em rascunho
    Dado que criei uma inscricao exclusiva em rascunho
    Entao a inscricao deve estar persistida em rascunho

  Esquema do Cenario: Atualizar inscricao com <metodo>
    Dado que criei uma inscricao exclusiva em rascunho
    Quando atualizo a inscricao exclusiva com "<metodo>"
    Entao a inscricao deve responder com status 200
    E a alteracao da inscricao deve persistir preservando os demais campos

    Exemplos:
      | metodo |
      | PUT |
      | PATCH |

  Cenario: Cancelar e reativar inscricao em rascunho
    Dado que criei uma inscricao exclusiva em rascunho
    Quando cancelo a inscricao exclusiva
    Entao a inscricao deve responder com status 200
    E a inscricao deve estar persistida com status "CANCELADA"
    Quando reativo a inscricao exclusiva
    Entao a inscricao deve responder com status 200
    E a inscricao deve estar persistida com status "RASCUNHO"

  Cenario: Excluir inscricao exclusiva
    Dado que criei uma inscricao exclusiva em rascunho
    Quando excluo a inscricao exclusiva
    Entao a inscricao deve responder com status 204
    E a inscricao excluida deve ser informada como nao encontrada

  Cenario: Listar e filtrar inscricao pelo nome
    Dado que criei uma inscricao exclusiva em rascunho
    Quando filtro inscricoes pelo nome exclusivo
    Entao a inscricao deve responder com status 200
    E a lista paginada deve conter apenas a inscricao exclusiva

  Cenario: Consultar lista sem correspondencia
    Dado que autentiquei para gerenciar inscricoes
    Quando busco inscricoes sem correspondencia
    Entao a inscricao deve responder com status 200
    E a lista de inscricoes deve estar vazia

  Esquema do Cenario: Consultar <rota>
    Dado que autentiquei para gerenciar inscricoes
    Quando consulto o recurso de inscricoes "<rota>"
    Entao a inscricao deve responder com status 200
    E o recurso de inscricoes "<rota>" deve respeitar o contrato

    Exemplos:
      | rota |
      | polos-elegiveis |
      | valores-choices |

  Esquema do Cenario: Recusar <metodo> em <rota> com token <token>
    Quando acesso inscricoes com "<metodo>" em "<rota>" com token "<token>"
    Entao a inscricao deve responder com status 401

    Exemplos:
      | metodo | rota | token |
      | GET | lista | ausente |
      | POST | lista | ausente |
      | GET | detalhe | ausente |
      | PUT | detalhe | ausente |
      | PATCH | detalhe | ausente |
      | DELETE | detalhe | ausente |
      | POST | cancelar | ausente |
      | POST | reativar | ausente |
      | GET | polos-elegiveis | ausente |
      | GET | participante-eol | ausente |
      | GET | valores-choices | ausente |
      | GET | lista | invalido |
      | POST | lista | invalido |
      | GET | detalhe | invalido |
      | PUT | detalhe | invalido |
      | PATCH | detalhe | invalido |
      | DELETE | detalhe | invalido |
      | POST | cancelar | invalido |
      | POST | reativar | invalido |
      | GET | polos-elegiveis | invalido |
      | GET | participante-eol | invalido |
      | GET | valores-choices | invalido |

  Esquema do Cenario: Recusar <metodo> em <rota> para inscricao inexistente
    Dado que autentiquei para gerenciar inscricoes
    Quando acesso inscricao inexistente com "<metodo>" em "<rota>"
    Entao a inscricao deve responder com status 400
    E a resposta deve indicar inscricao nao encontrada

    Exemplos:
      | metodo | rota |
      | GET | detalhe |
      | PUT | detalhe |
      | PATCH | detalhe |
      | DELETE | detalhe |
      | POST | cancelar |
      | POST | reativar |

  Esquema do Cenario: Recusar <regra> por POST PUT e PATCH
    Dado que criei uma inscricao exclusiva em rascunho
    Quando envio a violacao de inscricao "<regra>" por POST PUT e PATCH
    Entao as operacoes de inscricao devem retornar 400 e preservar os dados

    Exemplos:
      | regra |
      | email invalido |
      | data invalida |
      | nome longo |
      | tipo invalido |
      | grupo invalido |
      | polo inexistente |
      | edicao inexistente |

  Cenario: Recusar consulta EOL sem codigo
    Dado que autentiquei para gerenciar inscricoes
    Quando consulto o recurso de inscricoes "participante-eol"
    Entao a inscricao deve responder com status 400
