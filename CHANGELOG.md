# Changelog

## 0.6.0 - 2026-09-14

- Implementado o domínio de Definições de Polos, incluindo o vínculo entre
  polos e edições, projeção e total de inscritos, ponto focal e histórico de
  participações.
- Adicionadas ações em massa para vinculação, alteração de tipo e alteração
  de edição das definições de polos.
- Adicionada a documentação do domínio em `docs/dominios/definicoes_polos/`.

## 0.5.0 - 2026-09-08

- Implementada a população de polos de gestão direta a partir da EOL em
  `POST /api/v1/polos/popular/`.
- Documentado o consumo de `EolPort` pelo domínio de polos em
  `docs/dominios/`.

## 0.4.0 - 2026-08-27

- Implementado o domínio de Polos, incluindo cadastro, consulta, atualização,
  exclusão e filtros de listagem.
- Adicionadas as consultas de tipos de escola, DREs e dados detalhados de uma
  unidade pela integração EOL.
- Adicionada a documentação do domínio em `docs/dominios/polos/`.

## 0.3.0 - 2026-08-21

- Implementado o domínio de Edições, incluindo o ciclo de vida automático das
  edições, validação dos períodos e controle de edição ativa.
- Adicionada a documentação do domínio em `docs/dominios/edicoes/`.

## 0.2.0 - 2026-08-13

- Implementado o fluxo de autenticação institucional via CoreSSO com sessão
  JWT local (login, refresh, verify, logout e perfil do usuário).
- Implementada a integração EOL de escolas, consumindo os três endpoints de
  `/api/escolas` e enriquecendo as unidades elegíveis ao programa.
- Adicionada a documentação dedicada das integrações CoreSSO e EOL em
  `docs/dominios/integracoes/`.

## 0.1.0 - 2026-07-27

- Criada a estrutura inicial do backend.
- Configurado Django com `config/`, DRF e drf-spectacular.
- Criados os apps `core`, `edicoes`, `polos` e as integrações `coresso` e `eol`.
- Disponibilizado o endpoint público `/api/v1/health/`.
- Adicionados Dockerfiles, Compose, requirements, pyproject e pre-commit.
- Estruturada a documentação base do projeto em `README.md` e `docs/`.
