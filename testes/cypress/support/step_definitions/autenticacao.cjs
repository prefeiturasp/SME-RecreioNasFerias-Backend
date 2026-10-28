const { Given, When, Then } = require('@badeball/cypress-cucumber-preprocessor')

// A assercao recebe somente um booleano para nao revelar o token em falhas.
const validarToken = (token) => {
  expect(typeof token === 'string' && token.trim().length > 0, 'token de acesso foi informado').to.be.true
}


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
		// O login envia credenciais e retorna token/cookie de sessao.
		failOnStatusCode: false, log: false,
	}).then((response) => {
		validarStatusLogin(response, 200)
		validarToken(response.body.token)
		return response
	})
}

When('eu envio as credenciais para o login institucional', () => {
	autenticarNaApi().as('loginResponse')
})

Then('a API deve responder com status 200', () => {
	cy.get('@loginResponse', { log: false }).its('status').should('eq', 200)
})

Then('a resposta deve conter um token JWT', () => {
	cy.get('@loginResponse', { log: false }).then(({ body }) => validarToken(body.token))
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
		failOnStatusCode: false, log: false,
	}).as('loginErrorResponse')
})

When('eu envio um payload invalido para o login institucional', () => {
	const apiBaseUrl = Cypress.env('api_base_url').replace(/\/$/, '')

	cy.request({
		method: 'POST',
		url: `${apiBaseUrl}/api/v1/auth/login/`,
		body: {},
		failOnStatusCode: false, log: false,
	}).as('loginErrorResponse')
})

Then('a API deve responder ao login com status 401', () => {
	cy.get('@loginErrorResponse', { log: false }).then((response) => validarStatusLogin(response, 401))
})

Then('a API deve responder ao login com status 400', () => {
	cy.get('@loginErrorResponse', { log: false }).then((response) => validarStatusLogin(response, 400))
})

Given('que estou autenticado na API', () => {
	autenticarNaApi().then(({ body }) => body.token).as('authToken')
})

When('eu envio a requisicao de logout institucional', () => {
	const apiBaseUrl = Cypress.env('api_base_url').replace(/\/$/, '')

	cy.get('@authToken', { log: false }).then((token) => {
		cy.request({
			method: 'POST',
			url: `${apiBaseUrl}/api/v1/auth/logout/`,
			headers: {
				Authorization: `Bearer ${token}`,
			},
			failOnStatusCode: false, log: false,
		}).as('logoutResponse')
	})
})

Then('a API deve responder ao logout com status 204', () => {
	cy.get('@logoutResponse', { log: false }).its('status').should('eq', 204)
})

When('eu envio a requisicao de logout sem token', () => {
	const apiBaseUrl = Cypress.env('api_base_url').replace(/\/$/, '')

	cy.request({
		method: 'POST',
		url: `${apiBaseUrl}/api/v1/auth/logout/`,
		failOnStatusCode: false, log: false,
	}).as('logoutErrorResponse')
})

When('eu envio a requisicao de logout com token invalido', () => {
	const apiBaseUrl = Cypress.env('api_base_url').replace(/\/$/, '')

	cy.request({
		method: 'POST',
		url: `${apiBaseUrl}/api/v1/auth/logout/`,
		headers: { Authorization: 'Bearer token-invalido' },
		failOnStatusCode: false, log: false,
	}).as('logoutErrorResponse')
})

Then('a API deve responder ao logout sem token com status 204', () => {
	cy.get('@logoutErrorResponse', { log: false }).its('status').should('eq', 204)
})

Then('a API deve responder ao logout com token invalido com status 204', () => {
	cy.get('@logoutErrorResponse', { log: false }).its('status').should('eq', 204)
})

Given('que o login institucional foi realizado para renovar o token', () => {
	autenticarNaApi().then(({ body }) => body.token).as('authToken')
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
		failOnStatusCode: false, log: false,
	}).as('refreshResponse')
})

Then('a API deve responder a renovacao com status 200', () => {
	cy.get('@refreshResponse', { log: false }).its('status').should('eq', 200)
})

Then('a resposta da renovacao deve conter um novo token', () => {
	cy.get('@refreshResponse', { log: false }).then(({ body }) => validarToken(body.token))
})

Then('a API deve responder a renovacao sem refresh token com status 400', () => {
	cy.get('@refreshResponse', { log: false }).its('status').should('eq', 400)
})

Given('que o login institucional foi realizado para verificar o token', () => {
	autenticarNaApi().then(({ body }) => body.token).as('authToken')
})

When('eu envio o token para verificacao', () => {
	const apiBaseUrl = Cypress.env('api_base_url').replace(/\/$/, '')

	cy.get('@authToken', { log: false }).then((token) => {
		cy.request({
			method: 'POST',
			url: `${apiBaseUrl}/api/v1/auth/token/verify/`,
			body: { token },
			failOnStatusCode: false, log: false,
		}).as('verifyResponse')
	})
})

When('eu envio um token invalido para verificacao', () => {
	const apiBaseUrl = Cypress.env('api_base_url').replace(/\/$/, '')

	cy.request({
		method: 'POST',
		url: `${apiBaseUrl}/api/v1/auth/token/verify/`,
		body: { token: 'token-invalido' },
		failOnStatusCode: false, log: false,
	}).as('verifyResponse')
})

Then('a API deve responder a verificacao com status 200', () => {
	cy.get('@verifyResponse', { log: false }).its('status').should('eq', 200)
})

Then('a API deve responder a verificacao com status 401', () => {
	cy.get('@verifyResponse', { log: false }).its('status').should('eq', 401)
})

Given('que o login institucional foi realizado', () => {
	autenticarNaApi().then(({ body }) => body.token).as('authToken')
})

When('eu consulto meu perfil autenticado', () => {
	const apiBaseUrl = Cypress.env('api_base_url').replace(/\/$/, '')

	cy.get('@authToken', { log: false }).then((token) => {
		cy.request({
			method: 'GET',
			url: `${apiBaseUrl}/api/v1/auth/me/`,
			headers: {
				Authorization: `Bearer ${token}`,
			},
			failOnStatusCode: false, log: false,
		}).as('meResponse')
	})
})

Then('a API deve responder ao perfil com status 200', () => {
	cy.get('@meResponse', { log: false }).its('status').should('eq', 200)
})

Then('a resposta do perfil deve conter os dados do usuario', () => {
	cy.get('@meResponse', { log: false }).its('body').should('be.an', 'object').and('not.be.empty')
})

When('eu consulto meu perfil sem token', () => {
	const apiBaseUrl = Cypress.env('api_base_url').replace(/\/$/, '')

	cy.request({
		method: 'GET',
		url: `${apiBaseUrl}/api/v1/auth/me/`,
		failOnStatusCode: false, log: false,
	}).as('meErrorResponse')
})

When('eu consulto meu perfil com token invalido', () => {
	const apiBaseUrl = Cypress.env('api_base_url').replace(/\/$/, '')

	cy.request({
		method: 'GET',
		url: `${apiBaseUrl}/api/v1/auth/me/`,
		headers: { Authorization: 'Bearer token-invalido' },
		failOnStatusCode: false, log: false,
	}).as('meErrorResponse')
})

Then('a API deve responder ao perfil com status 401', () => {
	cy.get('@meErrorResponse', { log: false }).its('status').should('eq', 401)
})

exports.autenticarNaApi = autenticarNaApi
exports.validarToken = validarToken

When('envio verificacao sem token no payload', () => cy.request({
  method: 'POST', url: Cypress.env('api_base_url').replace(/\/$/, '') + '/api/v1/auth/token/verify/',
  body: {}, failOnStatusCode: false, log: false,
}).as('verifyResponse'))
Then('a verificacao sem token deve retornar 400', () => cy.get('@verifyResponse', { log: false }).its('status').should('eq', 400))
When('envio um refresh token invalido', () => {
  cy.clearCookies()
  return cy.request({ method: 'POST', url: Cypress.env('api_base_url').replace(/\/$/, '') + '/api/v1/auth/token/refresh/', body: { refresh: 'token-invalido' }, failOnStatusCode: false, log: false }).as('refreshResponse')
})
Then('o refresh invalido deve retornar 401', () => cy.get('@refreshResponse', { log: false }).its('status').should('eq', 401))
Then('o token renovado deve permitir consultar meu perfil', () => cy.get('@refreshResponse', { log: false }).then(({ body }) => {
  validarToken(body.token)
  return cy.request({ url: Cypress.env('api_base_url').replace(/\/$/, '') + '/api/v1/auth/me/', headers: { Authorization: 'Bearer ' + body.token }, failOnStatusCode: false, log: false }).then((res) => {
    expect(res.status).to.eq(200)
    expect(res.body).to.be.an('object').and.not.be.empty
  })
}))
