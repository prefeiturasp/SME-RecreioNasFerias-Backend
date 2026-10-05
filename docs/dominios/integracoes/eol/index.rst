EOL / SME Integração
====================

Esta página documenta a integração com a SME Integração (EOL): escolas
(catálogo, tipos e enriquecimento das unidades elegíveis) e a consulta de
aluno da rede pelo código EOL.

Visão resumida
--------------

- endpoints externos: ``GET /api/DREs``, ``GET /api/escolas/tiposEscolas``,
  ``GET /api/escolas/*``, ``GET /api/alunos/alunos`` e
  ``GET /api/alunos/{codigoAluno}/informacoes``
- app de integração: ``apps/integracoes/eol/``
- contrato público: ``EolPort``
- consumo atual: ``PoloService.popular_unidades_diretas()`` e
  ``InscricaoService.consultar_participante_por_eol()``

Contrato externo consumido
--------------------------

A integração consome sete endpoints, todos com o header ``x-api-eol-key``:

- ``GET /api/DREs`` — catálogo de Diretorias Regionais de Educação
- ``GET /api/escolas/tiposEscolas`` — catálogo de tipos de escola
- ``GET /api/escolas/todas-unidades`` — catálogo bruto de unidades escolares
- ``GET /api/escolas/dados/{eol}`` — dados detalhados da unidade
- ``GET /api/escolas/{eol}/funcionarios/cargos/{codigo}`` — funcionários no cargo
- ``GET /api/alunos/alunos?codigoAluno=`` — aluno pelo código EOL
- ``GET /api/alunos/{codigoAluno}/informacoes`` — ficha do aluno

Campos do catálogo bruto usados hoje:

Para DREs:

- ``codigoDRE``
- ``nomeDRE``
- ``siglaDRE``

Para unidades:

- ``codigoEscola``
- ``nomeEscola``
- ``siglaTipoEscola``
- ``nomeDRE``
- ``siglaDRE``
- ``codigoDRE``

Para tipos de escola:

- ``codigo``
- ``descricaoSigla``

Campos dos dados detalhados usados hoje:

- ``nome``
- ``siglaTipoEscola``
- ``nomeDRE`` / ``siglaDRE`` / ``codigoDRE``
- ``email``
- ``telefone``
- ``cep``
- ``tipoLogradouro`` / ``logradouro`` / ``numero`` / ``bairro`` / ``complemento``

Da consulta de funcionários por cargo, o sistema extrai ``nomeServidor`` do
primeiro registro retornado.

Campos da lista de alunos usados hoje:

- ``codigoAluno``
- ``nomeAluno`` / ``nomeSocialAluno``
- ``nomeResponsavel`` / ``celularResponsavel``
- ``dataNascimento``
- situação, turma, etapa e ciclo de ensino

Campos da ficha usados hoje:

- ``nomeMae``
- ``sexo`` / ``grupoEtnico`` / ``nacionalidade`` / ``ehImigrante``
- ``nis`` / ``cns``
- ``endereco.tipologradouro`` / ``logradouro`` / ``nro`` / ``bairro`` /
  ``complemento`` / ``cep`` / ``nomeMunicipio`` / ``siglaUF``

A amostra da SME não traz e-mail, segundo telefone nem nome social do
responsável. Esses três campos saem vazios no contrato interno.

Normalização interna
--------------------

O backend não propaga os payloads brutos para o restante da aplicação. Ele os
converte em contratos internos tipados em ``apps/integracoes/eol/port.py``:

- ``UnidadeEol`` — unidade do catálogo bruto normalizada
- ``DreEol`` — Diretoria Regional de Educação normalizada
- ``TipoEscolaEol`` — tipo de unidade normalizado
- ``DadosUnidadeEol`` — dados detalhados normalizados (CEP e endereço em campos separados)
- ``UnidadeRecreioEol`` — unidade enriquecida pronta para a sincronização
- ``AlunoEol`` — aluno da lista ``/api/alunos/alunos``
- ``InformacoesAlunoEol`` — ficha com endereço em campos soltos
- ``ParticipanteRedeEol`` — aluno unido à ficha, pronto para o domínio

Decisões principais de mapeamento:

- ``codigoEscola`` -> ``codigo_eol``
- ``cep`` é normalizado para o padrão ``00000-000``
- o endereço é mantido em campos separados: ``tipo_logradouro``,
  ``logradouro``, ``numero``, ``bairro`` e ``complemento``
- ``complemento`` fica vazio quando a integração não o envia
- os dados detalhados prevalecem sobre o catálogo bruto quando ambos existem
- ``nomeSocialAluno`` -> ``nome_social_aluno``
- ``nomeResponsavel`` -> ``nome_responsavel``
- ``nomeMae`` -> ``nome_mae``
- ``dataNascimento`` fica só com a data ``AAAA-MM-DD``
- o CEP do aluno usa a mesma normalização ``00000-000``
- a consulta usa o primeiro item da lista de alunos
- lista vazia em ``/api/alunos/alunos`` devolve ``None`` e não chama a ficha
- HTTP 404 na ficha mantém o aluno e deixa o endereço vazio

Filtro de tipos de unidade
--------------------------

Apenas unidades cujo ``siglaTipoEscola`` pertence ao conjunto elegível entram
no fluxo do Recreio nas Férias:

- ``EMEF``
- ``EMEI``
- ``EMEI P FOM``
- ``CEI DIRET``
- ``CEI INDIR``
- ``CEU``
- ``CEU EMEI``
- ``CEU CEI``
- ``CEU CEMEI``

O conjunto fica em ``SIGLAS_TIPO_UE_RECREIO``, em
``apps/integracoes/eol/constants.py``.

Enriquecimento
--------------

O ``EolAdapter`` oferece ``enriquecer_unidades``, que para cada unidade busca
dados detalhados e o nome do diretor.

Comportamentos importantes:

- enriquecimento executado em paralelo (``MAX_WORKERS_PADRAO = 8``)
- falhas pontuais em dados ou diretor não abortam o processo; nesses casos a
  unidade mantém apenas os dados do catálogo bruto
- o resultado é ordenado por nome da escola e código EOL
- ``listar_unidades_diretas_recreio(limite=None)`` integra filtro + limite +
  enriquecimento em uma única operação

Código do cargo de diretor
--------------------------

A consulta de diretor usa, por padrão, o código de cargo ``3360`` (Diretor de
Escola no catálogo oficial da SME), definido em
``CODIGO_CARGO_DIRETOR_ESCOLA``. O método ``obter_nome_diretor`` aceita um
código alternativo quando necessário.

Contrato público
----------------

O ``EolPort`` expõe as operações que o domínio consome:

- ``listar_dres()``
- ``listar_tipos_escola()``
- ``listar_todas_unidades()``
- ``obter_dados_unidade(codigo_eol)``
- ``obter_nome_diretor(codigo_eol, codigo_cargo=None)``
- ``filtrar_unidades_recreio(unidades)``
- ``enriquecer_unidades(unidades)``
- ``listar_unidades_diretas_recreio(limite=None)``
- ``listar_alunos(codigo_eol)``
- ``obter_informacoes_aluno(codigo_eol)``
- ``consultar_participante(codigo_eol)``

Exceções
--------

A integração traduz falhas em exceções específicas:

- ``EolConfigError`` — configuração ausente
- ``EolIndisponivelError`` — erro de rede ou HTTP 4xx/5xx
- ``EolContratoError`` — resposta fora do contrato esperado

Variáveis de ambiente usadas
----------------------------

A integração EOL reutiliza a mesma família ``AUTH_API_*`` da autenticação:

- ``AUTH_API_BASE_URL``
- ``AUTH_API_EOL_KEY``
- ``AUTH_API_CONNECT_TIMEOUT_SECONDS``
- ``AUTH_API_TIMEOUT_SECONDS``

Nenhuma variável nova foi introduzida para a integração de escolas.

Pontos de atenção para produção
-------------------------------

- os endpoints dependem do header ``x-api-eol-key``; sem a chave a
  integração falha com ``EolConfigError``
- o timeout de leitura usa ``AUTH_API_TIMEOUT_SECONDS`` (60s), mais longo que
  o do login, porque a listagem completa e o enriquecimento são consultas
  pesadas
- os domínios de polos e de inscrições consomem apenas ``EolPort``; o
  client HTTP permanece isolado em ``apps/integracoes/eol/``

Consumo pelo domínio de polos
-----------------------------

A população de polos diretos vive em ``apps/polos`` e é disparada por
``POST /api/v1/polos/popular/``.

O ``PoloService``:

1. lista o catálogo bruto via ``listar_todas_unidades()``
2. filtra as unidades elegíveis via ``filtrar_unidades_recreio()``
3. compara os códigos EOL com os polos de gestão direta já persistidos
4. enriquece somente as unidades novas via ``enriquecer_unidades()``
5. grava os polos em ``polos_polo`` com ``gestao=direta`` e ``tipo=pendente``

A carga executa no máximo uma vez por dia. O instante da última execução
fica em ``ControleSincronizacaoPolos``. Detalhes do domínio estão em
``docs/dominios/polos/``.

Consumo pelo domínio de inscrições
----------------------------------

A consulta do participante da rede vive em ``apps/inscricoes`` e é disparada
por ``GET /api/v1/inscricoes/participante-eol/?codigo_eol=``.

O ``InscricaoService.consultar_participante_por_eol()``:

1. recusa código vazio com ``Informe o código EOL.`` e não chama a SME
2. consulta ``consultar_participante()`` na ``EolPort``
3. traduz lista vazia em
   ``Código EOL não encontrado. Verifique o número digitado e tente novamente.``
4. devolve o ``ParticipanteRedeEol`` sem gravar inscrição

``EolConfigError`` responde HTTP 500. ``EolIndisponivelError`` e
``EolContratoError`` respondem HTTP 502. Indisponibilidade da SME não usa a
mensagem de código não encontrado.
