const { When, Then } = require('cypress-cucumber-preprocessor/steps')

const autenticarNaApi = () => {
	const configuredApiBaseUrl = Cypress.env('api_base_url')
	const usuario = Cypress.env('api_usuario')
	const senha = Cypress.env('api_senha')

	if (!configuredApiBaseUrl) {
		throw new Error('Configure API_BASE_URL em tests/.env com a URL do backend.')
	}

	return cy.request({
		method: 'POST',
		url: `${configuredApiBaseUrl.replace(/\/$/, '')}/api/v1/auth/login/`,
		body: {
			login: usuario,
			senha,
		},
	})
}

When('eu envio as credenciais para o login institucional', () => {
	autenticarNaApi().as('loginResponse')
})

Then('a API deve responder com status 200', () => {
	cy.get('@loginResponse').its('status').should('eq', 200)
})

Then('a resposta deve conter um token JWT', () => {
	cy.get('@loginResponse').its('body.token').should('be.a', 'string').and('not.be.empty')
})

When('eu envio credenciais invalidas para o login institucional', () => {
	const apiBaseUrl = Cypress.env('api_base_url').replace(/\/$/, '')

	cy.request({
		method: 'POST',
		url: `${apiBaseUrl}/api/v1/auth/login/`,
		body: {
			login: 'usuario-inexistente',
			senha: 'senha-invalida',
		},
		failOnStatusCode: false,
	}).as('loginErrorResponse')
})

When('eu envio um payload invalido para o login institucional', () => {
	const apiBaseUrl = Cypress.env('api_base_url').replace(/\/$/, '')

	cy.request({
		method: 'POST',
		url: `${apiBaseUrl}/api/v1/auth/login/`,
		body: {},
		failOnStatusCode: false,
	}).as('loginErrorResponse')
})

Then('a API deve responder ao login com status 401', () => {
	cy.get('@loginErrorResponse').its('status').should('eq', 401)
})

Then('a API deve responder ao login com status 400', () => {
	cy.get('@loginErrorResponse').its('status').should('eq', 400)
})

module.exports = { autenticarNaApi }
