const { When, Then } = require('@badeball/cypress-cucumber-preprocessor')

const consultarHealthcheck = (method = 'GET', headers = {}) => {
	const apiBaseUrl = (Cypress.env('api_base_url') || Cypress.config('baseUrl')).replace(/\/$/, '')

	cy.clearCookies()
	return cy.request({
		method,
		url: `${apiBaseUrl}/api/v1/health/`,
		failOnStatusCode: false,
		followRedirect: false,
		headers: { Accept: 'application/json', ...headers },
	}).as('healthResponse')
}

When('eu consulto o healthcheck da infraestrutura', () => consultarHealthcheck())
When('eu consulto o healthcheck com token invalido', () => consultarHealthcheck('GET', { Authorization: 'Bearer token-invalido' }))
When('eu consulto o healthcheck usando {string}', (metodo) => consultarHealthcheck(metodo))

Then('a API deve responder ao healthcheck com status 200', () => {
	cy.get('@healthResponse').its('status').should('eq', 200)
})

Then('a qualidade da aplicacao deve ser ok', () => {
	cy.get('@healthResponse').its('body.status').should('eq', 'ok')
})

const validarJson = (response) => {
	expect(response.headers['content-type']).to.match(/^application\/json(?:\s*;|$)/i)
	expect(response.body).to.be.an('object')
}

Then('o healthcheck deve retornar o contrato JSON esperado', () => {
	cy.get('@healthResponse').then((response) => {
		validarJson(response)
		expect(response.body).to.deep.eq({ status: 'ok' })
	})
})

Then('o healthcheck nao deve retornar corpo', () => {
	cy.get('@healthResponse').its('body').should('be.empty')
})

Then('o healthcheck deve permitir apenas GET HEAD e OPTIONS', () => {
	cy.get('@healthResponse').then((response) => {
		expect(response.headers.allow, 'Cabecalho Allow').to.be.a('string')
		const metodos = response.headers.allow.split(',').map((metodo) => metodo.trim().toUpperCase())
		expect(metodos).to.have.members(['GET', 'HEAD', 'OPTIONS'])
	})
})

Then('o healthcheck deve rejeitar o metodo com status 405', () => {
	cy.get('@healthResponse').then((response) => {
		expect(response.status, JSON.stringify(response.body)).to.eq(405)
	})
})

Then('o healthcheck deve informar o erro em JSON', () => {
	cy.get('@healthResponse').then((response) => {
		validarJson(response)
		expect(response.body).to.deep.eq({ detalhe: 'Metodo nao permitido.' })
	})
})
