# language: pt
Funcionalidade: Gerenciamento de polos
  Como um usuario autenticado
  Quero gerenciar polos pela API
  Para automatizar o cadastro e a manutencao de polos

  Cenario: Listar polos com token valido
    Dado que o login institucional foi realizado para consultar polos
    Quando eu consulto a lista de polos
    Entao a API deve responder a lista de polos com status 200
    E a resposta deve conter uma lista de polos

  Cenario: Recusar listagem de polos sem token
    Quando eu consulto a lista de polos sem token
    Entao a API deve responder a lista de polos com status 401

  Cenario: Consultar um polo pelo UUID
    Dado que o login institucional foi realizado para consultar um polo
    E existe um polo cadastrado
    Quando eu consulto o polo pelo UUID
    Entao a API deve responder ao detalhe do polo com status 200
    E a resposta deve conter os dados principais do polo

  Cenario: Recusar consulta de polo pelo UUID sem token
    Quando eu consulto um polo pelo UUID sem token
    Entao a API deve responder ao detalhe do polo com status 401

  Cenario: Criar um polo com token valido
    Dado que o login institucional foi realizado para criar polo
    Quando eu envio os dados de um novo polo
    Entao a API deve responder a criacao de polo com status 201
    E a resposta deve conter os dados do polo criado

  Cenario: Recusar criacao de polo com payload invalido
    Dado que o login institucional foi realizado para criar polo
    Quando eu envio um payload invalido para criar polo
    Entao a API deve responder a criacao de polo com status 400

  Cenario: Atualizar um polo pelo UUID
    Dado que o login institucional foi realizado para atualizar polo
    E existe um polo para atualizar
    Quando eu atualizo os dados do polo
    Entao a API deve responder a atualizacao de polo com status 200
    E a resposta deve conter os dados atualizados do polo

  Cenario: Recusar atualizacao de polo com payload invalido
    Dado que o login institucional foi realizado para atualizar polo
    E existe um polo para atualizar
    Quando eu envio um payload invalido para atualizar polo
    Entao a API deve responder a atualizacao de polo com status 400

  Cenario: Atualizar parcialmente um polo pelo UUID
    Dado que o login institucional foi realizado para atualizar polo parcialmente
    E existe um polo para atualizar parcialmente
    Quando eu atualizo parcialmente os dados do polo
    Entao a API deve responder a atualizacao parcial de polo com status 200
    E a resposta deve conter os dados do polo atualizado parcialmente

  Cenario: Recusar atualizacao parcial de polo com payload invalido
    Dado que o login institucional foi realizado para atualizar polo parcialmente
    E existe um polo para atualizar parcialmente
    Quando eu envio um payload invalido para atualizar polo parcialmente
    Entao a API deve responder a atualizacao parcial de polo com status 400

  Cenario: Excluir um polo pelo UUID
    Dado que o login institucional foi realizado para excluir polo
    E um polo exclusivo foi criado para exclusao
    Quando eu excluo o polo pelo UUID
    Entao a API deve responder a exclusao de polo com status 204

  Cenario: Listar DREs com token valido
    Dado que o login institucional foi realizado para consultar DREs
    Quando eu consulto a lista de DREs
    Entao a API deve responder a lista de DREs com status 200
    E a resposta deve conter uma lista de DREs

  Cenario: Recusar listagem de DREs sem token
    Quando eu consulto a lista de DREs sem token
    Entao a API deve responder a lista de DREs com status 401

  Cenario: Listar tipos de escola com token valido
    Dado que o login institucional foi realizado para consultar tipos de escola
    Quando eu consulto a lista de tipos de escola
    Entao a API deve responder a lista de tipos de escola com status 200
    E a resposta deve conter uma lista de tipos de escola

  Cenario: Recusar listagem de tipos de escola sem token
    Quando eu consulto a lista de tipos de escola sem token
    Entao a API deve responder a lista de tipos de escola com status 401

  @polos_validacoes
  Esquema do Cenario: Recusar <metodo> em <rota> com token <token>
    Quando valido acesso a polos com "<metodo>" em "<rota>" e token "<token>"
    Entao a validacao de polos deve retornar 401

    Exemplos:
      | metodo | rota | token |
      | POST | lista | ausente |
      | PUT | detalhe | ausente |
      | PATCH | detalhe | ausente |
      | DELETE | detalhe | ausente |
      | GET | dados-da-unidade | ausente |
      | POST | popular | ausente |
      | GET | lista | invalido |
      | POST | lista | invalido |
      | GET | detalhe | invalido |
      | PUT | detalhe | invalido |
      | PATCH | detalhe | invalido |
      | DELETE | detalhe | invalido |
      | GET | dres | invalido |
      | GET | tipos-escola | invalido |
      | GET | dados-da-unidade | invalido |
      | POST | popular | invalido |

  @polos_validacoes
  Esquema do Cenario: Recusar <metodo> para polo inexistente
    Dado que autentiquei para validar polos
    Quando valido polo inexistente com "<metodo>"
    Entao a validacao de polos deve retornar 404

    Exemplos:
      | metodo |
      | GET |
      | PUT |
      | PATCH |
      | DELETE |

  @polos_validacoes
  Esquema do Cenario: Recusar <regra> por POST PUT e PATCH
    Dado que existem dois polos exclusivos de validacao
    Quando valido a regra de polos "<regra>" por POST PUT e PATCH
    Entao as operacoes de polos devem retornar 400 e preservar os dados

    Exemplos:
      | regra |
      | nome duplicado |
      | nome duplicado em maiusculas |
      | codigo duplicado |
      | codigo curto |
      | codigo longo |
      | nome longo |
      | capacidade negativa |
      | capacidade nao numerica |
      | tipo invalido |
      | gestao invalida |
      | status invalido |

  @polos_validacoes
  Esquema do Cenario: Filtrar polos por <filtro>
    Dado que existem dois polos exclusivos de validacao
    Quando filtro os polos de validacao por "<filtro>"
    Entao o filtro deve retornar apenas o primeiro polo

    Exemplos:
      | filtro |
      | nome |
      | osc |
      | dre |
      | tipo_ue |
      | gestao |
      | combinados |

  @polos_validacoes
  Cenario: Paginar polos sem repetir registros
    Dado que existem dois polos exclusivos de validacao
    Quando consulto duas paginas dos polos de validacao
    Entao as paginas devem conter os dois polos sem repeticao

  @polos_validacoes
  Cenario: Retornar lista vazia para busca sem correspondencia
    Dado que existem dois polos exclusivos de validacao
    Quando busco um polo sem correspondencia
    Entao a validacao de polos deve retornar 200
    E a busca de polos deve retornar lista vazia

  @polos_validacoes
  Cenario: Persistir criacao PUT e PATCH e confirmar exclusao
    Dado que existem dois polos exclusivos de validacao
    Quando verifico a persistencia da criacao e das atualizacoes do polo
    Entao o PATCH do polo deve preservar os campos omitidos
    Quando excluo o polo exclusivo de validacao
    Entao a validacao de polos deve retornar 204
    E o polo excluido deve retornar 404

  @polos_validacoes
  Cenario: Consultar unidade sem codigo EOL retorna campos vazios
    Dado que autentiquei para validar polos
    Quando consulto dados da unidade sem codigo EOL
    Entao a validacao de polos deve retornar 200
    E os dados da unidade sem codigo devem estar vazios
