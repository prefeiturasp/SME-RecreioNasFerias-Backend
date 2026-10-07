# language: pt
@edicoes
Funcionalidade: Edicoes
  Como um usuario autenticado
  Quero consultar as edicoes cadastradas
  Para acompanhar seus periodos e status

  Cenario: Listar edicoes com token valido
    Dado que o login institucional foi realizado para consultar edicoes
    Quando eu consulto a lista de edicoes
    Entao a API deve responder a lista de edicoes com status 200
    E a resposta deve conter uma lista de edicoes
    E cada edicao deve possuir os campos principais

  Cenario: Recusar listagem de edicoes sem token
    Quando eu consulto a lista de edicoes sem token
    Entao a API deve responder a lista de edicoes com status 401

  Cenario: Consultar uma edicao pelo UUID
    Dado que o login institucional foi realizado para consultar uma edicao
    E existe uma edicao cadastrada
    Quando eu consulto a edicao pelo UUID
    Entao a API deve responder ao detalhe da edicao com status 200
    E a resposta deve conter os dados principais da edicao

  Cenario: Recusar consulta de edicao pelo UUID sem token
    Quando eu consulto uma edicao pelo UUID sem token
    Entao a API deve responder ao detalhe da edicao com status 401

  Cenario: Criar uma edicao com token valido
    Dado que o login institucional foi realizado para criar edicao
    Quando eu envio os dados de uma nova edicao
    Entao a API deve responder a criacao de edicao com status 201
    E a resposta deve conter os dados da edicao criada

  Cenario: Recusar criacao de edicao com payload invalido
    Dado que o login institucional foi realizado para criar edicao
    Quando eu envio um payload invalido para criar edicao
    Entao a API deve responder a criacao de edicao com status 400

  Cenario: Atualizar uma edicao pelo UUID
    Dado que o login institucional foi realizado para atualizar edicao
    E existe uma edicao para atualizar
    Quando eu atualizo os dados da edicao
    Entao a API deve responder a atualizacao de edicao com status 200
    E a resposta deve conter os dados atualizados da edicao

  Cenario: Recusar atualizacao de edicao com payload invalido
    Dado que o login institucional foi realizado para atualizar edicao
    E existe uma edicao para atualizar
    Quando eu envio um payload invalido para atualizar edicao
    Entao a API deve responder a atualizacao de edicao com status 400

  Cenario: Atualizar parcialmente uma edicao pelo UUID
    Dado que o login institucional foi realizado para atualizar edicao parcialmente
    E existe uma edicao para atualizar parcialmente
    Quando eu atualizo parcialmente os dados da edicao
    Entao a API deve responder a atualizacao parcial com status 200
    E a resposta deve conter os dados da edicao atualizada parcialmente

  Cenario: Recusar atualizacao parcial com payload invalido
    Dado que o login institucional foi realizado para atualizar edicao parcialmente
    E existe uma edicao para atualizar parcialmente
    Quando eu envio um payload invalido para atualizar edicao parcialmente
    Entao a API deve responder a atualizacao parcial com status 400

  Cenario: Excluir uma edicao pelo UUID
    Dado que o login institucional foi realizado para excluir edicao
    E uma edicao exclusiva foi criada para exclusao
    Quando eu excluo a edicao pelo UUID
    Entao a API deve responder a exclusao de edicao com status 204
  @edicoes_validacoes
  Esquema do Cenario: Recusar <metodo> em <rota> com autenticacao <token>
    Quando acesso edicoes com "<metodo>" em "<rota>" com token "<token>"
    Entao a validacao de edicoes deve responder com status 401

    Exemplos:
      | metodo | rota    | token    |
      | POST   | lista   | ausente  |
      | PUT    | detalhe | ausente  |
      | PATCH  | detalhe | ausente  |
      | DELETE | detalhe | ausente  |
      | GET    | lista   | invalido |
      | POST   | lista   | invalido |
      | GET    | detalhe | invalido |
      | PUT    | detalhe | invalido |
      | PATCH  | detalhe | invalido |
      | DELETE | detalhe | invalido |

  @edicoes_validacoes
  Esquema do Cenario: Recusar <metodo> para UUID inexistente
    Dado que autentiquei para validar as regras de edicoes
    Quando acesso uma edicao inexistente com "<metodo>"
    Entao a validacao de edicoes deve responder com status 404

    Exemplos:
      | metodo |
      | GET    |
      | PUT    |
      | PATCH  |
      | DELETE |

  @edicoes_validacoes
  Esquema do Cenario: Recusar <regra> na criacao e nas atualizacoes
    Dado que existem duas edicoes exclusivas para validar regras
    Quando envio edicoes com a violacao "<regra>" por POST PUT e PATCH
    Entao as tres operacoes devem retornar 400 sem alterar as edicoes

    Exemplos:
      | regra                           |
      | nome duplicado                  |
      | nome duplicado em maiusculas     |
      | nome acima de 255 caracteres     |
      | data invalida                   |
      | fim anterior ao inicio          |
      | inscricoes invertidas           |
      | inscricoes apos fim da edicao    |
      | sobreposicao de edicoes          |
      | sobreposicao de inscricoes       |

  @edicoes_validacoes
  Cenario: Persistir criacao e atualizacoes preservando campos omitidos
    Dado que existem duas edicoes exclusivas para validar regras
    Entao a primeira edicao deve estar persistida conforme enviada
    Quando altero a primeira edicao por PUT e PATCH
    Entao os valores devem persistir e o PATCH deve preservar os demais campos

  @edicoes_validacoes
  Cenario: Confirmar ausencia de uma edicao excluida
    Dado que existem duas edicoes exclusivas para validar regras
    Quando excluo a primeira edicao exclusiva de validacao
    Entao a validacao de edicoes deve responder com status 204
    E consultar a edicao excluida deve retornar 404
