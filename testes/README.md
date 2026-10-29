# SME CDEP WebClient Tests

Automacao E2E usando Cypress e cenarios BDD escritos em Gherkin.

## Estrutura

- `cypress/e2e/api`: cenarios de API.
- `cypress/e2e/ui`: cenarios da interface.
- `cypress/fixtures`: dados de teste.
- `cypress/plugin`: configuracao do pre-processador Cucumber.
- `cypress/support/commands_api`: comandos de API.
- `cypress/support/commands_ui`: comandos de interface.
- `cypress/support/locators`: seletores compartilhados.
- `cypress/support/step_definitions`: implementacoes dos passos Gherkin.
- `cypress/support/utils`: utilitarios de teste.

## Executar

Na raiz de `tests`, instale as dependencias com `npm install`. Com o frontend rodando, use:

```bash
npm run e2e
```

Para abrir o Cypress:

```bash
npm run e2e:open
```

O alvo do frontend pode ser alterado com `CYPRESS_BASE_URL` ou `BASE_URL`. Para o login, `API_BASE_URL` deve apontar para o backend que expoe `/api/v1/auth/login/`. As credenciais de API devem ser configuradas localmente em `tests/.env`, usando `API_USUARIO` e `API_SENHA`.

## Relatorio Allure

Para rodar os testes coletando os resultados do Allure:

```bash
npm run e2e:allure
```

Para gerar e abrir o relatorio HTML a partir dos resultados (`allure-results/`):

```bash
npm run allure:generate
npm run allure:open
```

Ou para fazer tudo de uma vez (executar, gerar e abrir):

```bash
npm run allure:report
```

No Jenkins, o pipeline (`Jenkinsfile_qa`) ja executa os testes com `allure=true`, gera o relatorio com o Allure e publica os resultados via plugin do Allure Jenkins.