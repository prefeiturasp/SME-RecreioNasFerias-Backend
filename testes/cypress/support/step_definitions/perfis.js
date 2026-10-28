const { Given, When, Then, Before } = require('@badeball/cypress-cucumber-preprocessor')
const { autenticarNaApi } = require('./autenticacao.cjs')
let token

Before({ tags: '@perfis' }, () => { token = null })
// O alias guarda somente status e body, sem headers/cookies da resposta.
const consultar = (credencial) => cy.request({
  url: Cypress.env('api_base_url').replace(/\/$/, '') + '/api/v1/perfis/',
  ...(credencial ? { headers: { Authorization: 'Bearer ' + credencial } } : {}), failOnStatusCode: false, log: false,
}).then(({ status, body }) => ({ status, body })).as('perfisResponse')
Given('que autentiquei para consultar perfis', () => autenticarNaApi().then(({ body }) => { token = body.token }))
When('consulto a lista de perfis', () => consultar(token))
When('consulto perfis com token {string}', (tipo) => { cy.clearCookies(); return consultar(tipo === 'ausente' ? null : 'token-invalido') })
Then('a consulta de perfis deve retornar {int}', (status) => cy.get('@perfisResponse', { log: false }).its('status', { log: false }).should('eq', status))
Then('os perfis e permissoes devem respeitar o contrato', () => cy.get('@perfisResponse', { log: false }).then(({ body }) => {
  expect(body).to.be.an('array')
  body.forEach((perfil) => {
    expect(perfil).to.include.all.keys('id', 'codigo', 'nome', 'descricao', 'permissoes')
    for (const campo of ['codigo', 'nome', 'descricao']) expect(perfil[campo], campo).to.be.a('string')
    expect(perfil.id === null || Number.isInteger(perfil.id)).to.eq(true)
    expect(perfil.permissoes).to.be.an('array')
    perfil.permissoes.forEach((permissao) => {
      expect(permissao).to.include.all.keys('codigo', 'recurso', 'nome_recurso', 'acao')
      for (const campo of ['codigo', 'recurso', 'nome_recurso', 'acao']) expect(permissao[campo], campo).to.be.a('string')
    })
  })
}))
