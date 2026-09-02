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
