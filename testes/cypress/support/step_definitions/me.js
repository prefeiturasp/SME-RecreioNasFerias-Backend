const { Given, When, Then } = require('@badeball/cypress-cucumber-preprocessor')
const { autenticarNaApi } = require('./login.cjs')

Given('que o login institucional foi realizado', () => {
	autenticarNaApi().its('body.token').should('be.a', 'string').and('not.be.empty').as('authToken')
})

When('eu consulto meu perfil autenticado', () => {
	const apiBaseUrl = Cypress.env('api_base_url').replace(/\/$/, '')

	cy.get('@authToken').then((token) => {
		cy.request({
			method: 'GET',
			url: `${apiBaseUrl}/api/v1/auth/me/`,
			headers: {
				Authorization: `Bearer ${token}`,
			},
			failOnStatusCode: false,
		}).as('meResponse')
	})
})

Then('a API deve responder ao perfil com status 200', () => {
	cy.get('@meResponse').its('status').should('eq', 200)
})

Then('a resposta do perfil deve conter os dados do usuario', () => {
	cy.get('@meResponse').its('body').should('be.an', 'object').and('not.be.empty')
})

When('eu consulto meu perfil sem token', () => {
	const apiBaseUrl = Cypress.env('api_base_url').replace(/\/$/, '')

	cy.request({
		method: 'GET',
		url: `${apiBaseUrl}/api/v1/auth/me/`,
		failOnStatusCode: false,
	}).as('meErrorResponse')
})

When('eu consulto meu perfil com token invalido', () => {
	const apiBaseUrl = Cypress.env('api_base_url').replace(/\/$/, '')

	cy.request({
		method: 'GET',
		url: `${apiBaseUrl}/api/v1/auth/me/`,
		headers: { Authorization: 'Bearer token-invalido' },
		failOnStatusCode: false,
	}).as('meErrorResponse')
})

Then('a API deve responder ao perfil com status 401', () => {
	cy.get('@meErrorResponse').its('status').should('eq', 401)
})
