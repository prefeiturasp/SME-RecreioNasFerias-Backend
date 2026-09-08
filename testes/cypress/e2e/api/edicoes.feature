# language: pt
Funcionalidade: Listagem de edicoes
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