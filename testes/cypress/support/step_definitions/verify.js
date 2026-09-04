const { Given, When, Then } = require('@badeball/cypress-cucumber-preprocessor')
const { autenticarNaApi } = require('./login.cjs')

Given('que o login institucional foi realizado para verificar o token', () => {
	autenticarNaApi().its('body.token').should('be.a', 'string').and('not.be.empty').as('authToken')
})

When('eu envio o token para verificacao', () => {
	const apiBaseUrl = Cypress.env('api_base_url').replace(/\/$/, '')

	cy.get('@authToken').then((token) => {
		cy.request({
			method: 'POST',
			url: `${apiBaseUrl}/api/v1/auth/token/verify/`,
			body: { token },
			failOnStatusCode: false,
		}).as('verifyResponse')
	})
})

When('eu envio um token invalido para verificacao', () => {
	const apiBaseUrl = Cypress.env('api_base_url').replace(/\/$/, '')

	cy.request({
		method: 'POST',
		url: `${apiBaseUrl}/api/v1/auth/token/verify/`,
		body: { token: 'token-invalido' },
		failOnStatusCode: false,
	}).as('verifyResponse')
})

Then('a API deve responder a verificacao com status 200', () => {
	cy.get('@verifyResponse').its('status').should('eq', 200)
})

Then('a API deve responder a verificacao com status 401', () => {
	cy.get('@verifyResponse').its('status').should('eq', 401)
})
