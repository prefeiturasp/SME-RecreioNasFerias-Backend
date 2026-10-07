const { Given, When, Then } = require('@badeball/cypress-cucumber-preprocessor')

const validarStatusLogin = (response, statusEsperado) => {
	const diagnostico = response.status === 502
		? 'POST /api/v1/auth/login/ retornou HTTP 502. Verifique os logs do backend e do gateway e a integracao com o Coresso.'
		: `POST /api/v1/auth/login/: esperado HTTP ${statusEsperado}, recebido HTTP ${response.status}`
	expect(response.status, diagnostico).to.eq(statusEsperado)
	return response
}

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
		failOnStatusCode: false,
	}).then((response) => validarStatusLogin(response, 200))
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
	cy.get('@loginErrorResponse').then((response) => validarStatusLogin(response, 401))
})

Then('a API deve responder ao login com status 400', () => {
	cy.get('@loginErrorResponse').then((response) => validarStatusLogin(response, 400))
})

Given('que estou autenticado na API', () => {
	autenticarNaApi().its('body.token').should('be.a', 'string').and('not.be.empty').as('authToken')
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

exports.autenticarNaApi = autenticarNaApi
