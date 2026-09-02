const { Given, When, Then } = require('cypress-cucumber-preprocessor/steps')
const { autenticarNaApi } = require('./login')

Given('que o login institucional foi realizado para renovar o token', () => {
	autenticarNaApi().its('body.token').should('be.a', 'string').and('not.be.empty').as('authToken')
})

Given('o refresh token foi removido da sessao', () => {
	cy.clearCookies()
})

When('eu envio a requisicao de renovacao do token', () => {
	const configuredApiBaseUrl = Cypress.env('api_base_url')

	if (!configuredApiBaseUrl) {
		throw new Error('Configure API_BASE_URL em tests/.env com a URL do backend.')
	}

	cy.request({
		method: 'POST',
		url: `${configuredApiBaseUrl.replace(/\/$/, '')}/api/v1/auth/token/refresh/`,
		failOnStatusCode: false,
	}).as('refreshResponse')
})

Then('a API deve responder a renovacao com status 200', () => {
	cy.get('@refreshResponse').its('status').should('eq', 200)
})

Then('a resposta da renovacao deve conter um novo token', () => {
	cy.get('@refreshResponse').its('body.token').should('be.a', 'string').and('not.be.empty')
})

Then('a API deve responder a renovacao sem refresh token com status 400', () => {
	cy.get('@refreshResponse').its('status').should('eq', 400)
})
