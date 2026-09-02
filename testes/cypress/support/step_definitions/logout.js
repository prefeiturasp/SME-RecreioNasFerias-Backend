const { Given, When, Then } = require('cypress-cucumber-preprocessor/steps')

Given('que estou autenticado na API', () => {
	const apiBaseUrl = Cypress.env('api_base_url')
	const usuario = Cypress.env('api_usuario')
	const senha = Cypress.env('api_senha')

	if (!apiBaseUrl) {
		throw new Error('Configure API_BASE_URL em tests/.env com a URL do backend.')
	}

	cy.request({
		method: 'POST',
		url: `${apiBaseUrl.replace(/\/$/, '')}/api/v1/auth/login/`,
		body: {
			login: usuario,
			senha,
		},
	}).its('body.token').should('be.a', 'string').and('not.be.empty').as('authToken')
})

When('eu envio a requisicao de logout institucional', () => {
	const apiBaseUrl = Cypress.env('api_base_url').replace(/\/$/, '')

	cy.get('@authToken').then((token) => {
		cy.request({
			method: 'POST',
			url: `${apiBaseUrl}/api/v1/auth/logout/`,
			headers: {
				Authorization: `Bearer ${token}`,
			},
			failOnStatusCode: false,
		}).as('logoutResponse')
	})
})

Then('a API deve responder ao logout com status 204', () => {
	cy.get('@logoutResponse').its('status').should('eq', 204)
})

When('eu envio a requisicao de logout sem token', () => {
	const apiBaseUrl = Cypress.env('api_base_url').replace(/\/$/, '')

	cy.request({
		method: 'POST',
		url: `${apiBaseUrl}/api/v1/auth/logout/`,
		failOnStatusCode: false,
	}).as('logoutErrorResponse')
})

When('eu envio a requisicao de logout com token invalido', () => {
	const apiBaseUrl = Cypress.env('api_base_url').replace(/\/$/, '')

	cy.request({
		method: 'POST',
		url: `${apiBaseUrl}/api/v1/auth/logout/`,
		headers: { Authorization: 'Bearer token-invalido' },
		failOnStatusCode: false,
	}).as('logoutErrorResponse')
})

Then('a API deve responder ao logout sem token com status 204', () => {
	cy.get('@logoutErrorResponse').its('status').should('eq', 204)
})

Then('a API deve responder ao logout com token invalido com status 204', () => {
	cy.get('@logoutErrorResponse').its('status').should('eq', 204)
})
