# language: pt
@definicoes_polos
Funcionalidade: Definições de Polos
  Como um usuario autenticado
  Quero gerenciar a participacao dos polos nas edicoes
  Para definir a oferta de atendimento de cada edicao

  Cenario: Listar definicoes com paginacao
    Dado que estou autenticado para gerenciar definicoes de polos
    Quando consulto as definicoes de polos com paginacao
    Entao a resposta de definicoes de polos deve ter status 200
    E a listagem de definicoes deve respeitar o contrato paginado

  Cenario: Filtrar definicoes por edicao e polo sem paginacao
    Dado que existe uma definicao de polo exclusiva para o teste
    Quando filtro as definicoes pela edicao e codigo EOL do teste
    Entao a resposta de definicoes de polos deve ter status 200
    E a listagem deve conter apenas a definicao do teste

  Cenario: Vincular um polo a uma edicao
    Dado que existem polos e edicoes exclusivos para definir participacoes
    Quando vinculo o primeiro polo a primeira edicao
    Entao a resposta de definicoes de polos deve ter status 201
    E a definicao criada deve corresponder aos dados enviados

  Cenario: Consultar uma definicao pelo UUID
    Dado que existe uma definicao de polo exclusiva para o teste
    Quando consulto a definicao de polo do teste
    Entao a resposta de definicoes de polos deve ter status 200
    E o detalhe deve identificar o polo e a edicao do teste

  Esquema do Cenario: Atualizar definicao de polo com <metodo>
    Dado que existe uma definicao de polo exclusiva para o teste
    Quando atualizo a definicao de polo com "<metodo>"
    Entao a resposta de definicoes de polos deve ter status 200
    E as alteracoes da definicao devem estar persistidas

    Exemplos:
      | metodo |
      | PUT    |
      | PATCH  |

  Cenario: Excluir uma definicao de polo
    Dado que existe uma definicao de polo exclusiva para o teste
    Quando excluo a definicao de polo do teste
    Entao a resposta de definicoes de polos deve ter status 204
    E a definicao excluida nao deve ser encontrada

  Cenario: Consultar historico de participacoes do polo
    Dado que existe uma definicao de polo exclusiva para o teste
    Quando consulto o historico do polo do teste
    Entao a resposta de definicoes de polos deve ter status 200
    E o historico deve conter a participacao criada

  Cenario: Vincular polos em massa
    Dado que existem polos e edicoes exclusivos para definir participacoes
    Quando vinculo os polos do teste em massa
    Entao a resposta de definicoes de polos deve ter status 201
    E os dois vinculos em massa devem estar persistidos

  Cenario: Alterar edicao de definicoes em massa
    Dado que existem duas definicoes de polos exclusivas para o teste
    Quando altero a edicao das definicoes em massa
    Entao a resposta de definicoes de polos deve ter status 200
    E as duas definicoes devem pertencer a edicao de destino

  Cenario: Alterar tipo de polos em massa
    Dado que existem duas definicoes de polos exclusivas para o teste
    Quando altero o tipo dos polos em massa
    Entao a resposta de definicoes de polos deve ter status 200
    E os dois polos devem ter o tipo atualizado na edicao

  Esquema do Cenario: Recusar <metodo> em <rota> sem autenticacao
    Quando acesso definicoes de polos com "<metodo>" em "<rota>" sem token
    Entao a resposta de definicoes de polos deve ter status 401

    Exemplos:
      | metodo | rota                      |
      | GET    | lista                     |
      | POST   | lista                     |
      | GET    | detalhe                   |
      | PUT    | detalhe                   |
      | PATCH  | detalhe                   |
      | DELETE | detalhe                   |
      | GET    | historico                 |
      | POST   | vincular-em-massa          |
      | POST   | alterar-edicao-em-massa    |
      | POST   | alterar-tipo-em-massa      |

  Esquema do Cenario: Recusar payload invalido em <rota>
    Dado que estou autenticado para gerenciar definicoes de polos
    Quando envio um payload invalido para definicoes em "<rota>"
    Entao a resposta de definicoes de polos deve ter status 400
    E a resposta de definicoes deve informar erros de validacao

    Exemplos:
      | rota                      |
      | lista                     |
      | vincular-em-massa          |
      | alterar-edicao-em-massa    |
      | alterar-tipo-em-massa      |

  Esquema do Cenario: Recusar projecao negativa com <metodo>
    Dado que existe uma definicao de polo exclusiva para o teste
    Quando envio uma projecao negativa com "<metodo>"
    Entao a resposta de definicoes de polos deve ter status 400
    E a projecao original da definicao deve ser preservada

    Exemplos:
      | metodo |
      | PUT    |
      | PATCH  |

  Cenario: Recusar consulta de historico sem polo
    Dado que estou autenticado para gerenciar definicoes de polos
    Quando consulto o historico sem informar um polo
    Entao a resposta de definicoes de polos deve ter status 400

  Cenario: Consultar definicao inexistente
    Dado que estou autenticado para gerenciar definicoes de polos
    Quando consulto uma definicao de polo inexistente
    Entao a resposta de definicoes de polos deve ter status 400
    E a resposta deve indicar definicao de polo nao encontrada
