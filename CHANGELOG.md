# Changelog

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
