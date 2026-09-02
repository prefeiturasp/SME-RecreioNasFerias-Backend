const { When, Then } = require('cypress-cucumber-preprocessor/steps')

When('eu consulto o healthcheck da infraestrutura', () => {
	const apiBaseUrl = (Cypress.env('api_base_url') || Cypress.config('baseUrl')).replace(/\/$/, '')

	cy.request({
		method: 'GET',
		url: `${apiBaseUrl}/api/v1/health/`,
		failOnStatusCode: false,
	}).as('healthResponse')
})

Then('a API deve responder ao healthcheck com status 200', () => {
	cy.get('@healthResponse').its('status').should('eq', 200)
})

Then('a qualidade da aplicacao deve ser ok', () => {
	cy.get('@healthResponse').its('body.status').should('eq', 'ok')
})