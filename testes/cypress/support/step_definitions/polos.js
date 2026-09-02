const { Given, When, Then } = require('cypress-cucumber-preprocessor/steps')
const { autenticarNaApi } = require('./login')

const obterApiBaseUrl = () => Cypress.env('api_base_url').replace(/\/$/, '')

const obterPoloPayload = (sufixo = String(Date.now()).slice(-6)) => ({
	codigo_eol: sufixo,
	nome_polo: `Polo automatizado ${sufixo}`,
	nome_osc: 'OSC automatizada',
	dre_nome: 'DRE automatizada',
	dre_codigo_eol: `DRE${sufixo}`,
	tipo_ue: 'EMEF',
	quantidade_maxima_alunos: 100,
	tipo: 'oficial',
	gestao: 'direta',
	cep: '01000-000',
	tipo_logradouro: 'Rua',
	logradouro: 'Rua Automatizada',
	bairro: 'Centro',
	numero: '100',
	nome_gestor: 'Gestor automatizado',
	email: 'gestor.automatizado@example.com',
	telefone: '11999999999',
})

const autenticarPara = () => {
	autenticarNaApi().its('body.token').should('be.a', 'string').and('not.be.empty').as('authToken')
}

const buscarPolo = (alias = 'poloAtual') => {
	cy.get('@authToken').then((token) => {
		cy.request({
			method: 'GET',
			url: `${obterApiBaseUrl()}/api/v1/polos/`,
			headers: { Authorization: `Bearer ${token}` },
		}).then((response) => {
			expect(response.body).to.be.an('array').and.not.be.empty
			cy.wrap(response.body[0]).as(alias)
		})
	})
}

Given('que o login institucional foi realizado para consultar polos', () => autenticarPara('consultar polos'))

When('eu consulto a lista de polos', () => {
	cy.get('@authToken').then((token) => {
		cy.request({ method: 'GET', url: `${obterApiBaseUrl()}/api/v1/polos/`, headers: { Authorization: `Bearer ${token}` }, failOnStatusCode: false }).as('polosResponse')
	})
})

When('eu consulto a lista de polos sem token', () => {
	cy.request({ method: 'GET', url: `${obterApiBaseUrl()}/api/v1/polos/`, failOnStatusCode: false }).as('polosErrorResponse')
})

Then('a API deve responder a lista de polos com status 200', () => cy.get('@polosResponse').its('status').should('eq', 200))
Then('a resposta deve conter uma lista de polos', () => cy.get('@polosResponse').its('body').should('be.an', 'array'))
Then('a API deve responder a lista de polos com status 401', () => cy.get('@polosErrorResponse').its('status').should('eq', 401))

Given('que o login institucional foi realizado para consultar um polo', () => autenticarPara('consultar um polo'))
Given('existe um polo cadastrado', () => buscarPolo('poloUuid'))

When('eu consulto o polo pelo UUID', () => {
	cy.get('@authToken').then((token) => cy.get('@poloUuid').then((polo) => {
		cy.request({ method: 'GET', url: `${obterApiBaseUrl()}/api/v1/polos/${polo.uuid}/`, headers: { Authorization: `Bearer ${token}` }, failOnStatusCode: false }).as('poloResponse')
	}))
})

When('eu consulto um polo pelo UUID sem token', () => {
	cy.request({ method: 'GET', url: `${obterApiBaseUrl()}/api/v1/polos/00000000-0000-0000-0000-000000000000/`, failOnStatusCode: false }).as('poloErrorResponse')
})

Then('a API deve responder ao detalhe do polo com status 200', () => cy.get('@poloResponse').its('status').should('eq', 200))
Then('a resposta deve conter os dados principais do polo', () => cy.get('@poloResponse').its('body').should('include.all.keys', ['uuid', 'codigo_eol', 'nome_polo', 'nome_osc', 'dre_nome', 'dre_codigo_eol', 'tipo_ue', 'quantidade_maxima_alunos']))
Then('a API deve responder ao detalhe do polo com status 401', () => cy.get('@poloErrorResponse').its('status').should('eq', 401))

Given('que o login institucional foi realizado para criar polo', () => {
	autenticarNaApi().its('body.token').should('be.a', 'string').and('not.be.empty').as('authToken')
})

When('eu envio os dados de um novo polo', () => {
	cy.get('@authToken').then((token) => {
		cy.request({
			method: 'POST',
			url: `${obterApiBaseUrl()}/api/v1/polos/`,
			headers: { Authorization: `Bearer ${token}` },
			body: obterPoloPayload(),
			failOnStatusCode: false,
		}).as('criacaoPoloResponse')
	})
})

When('eu envio um payload invalido para criar polo', () => {
	cy.get('@authToken').then((token) => {
		cy.request({
			method: 'POST',
			url: `${obterApiBaseUrl()}/api/v1/polos/`,
			headers: { Authorization: `Bearer ${token}` },
			body: {},
			failOnStatusCode: false,
		}).as('criacaoPoloErrorResponse')
	})
})

Then('a API deve responder a criacao de polo com status 201', () => {
	cy.get('@criacaoPoloResponse').then((response) => {
		expect(response.status, JSON.stringify(response.body)).to.eq(201)
	})
})

Then('a resposta deve conter os dados do polo criado', () => {
	cy.get('@criacaoPoloResponse').its('body').should('include.all.keys', [
		'uuid',
		'codigo_eol',
		'nome_polo',
		'nome_osc',
		'dre_nome',
		'dre_codigo_eol',
		'tipo_ue',
		'quantidade_maxima_alunos',
	])
})

Then('a API deve responder a criacao de polo com status 400', () => {
	cy.get('@criacaoPoloErrorResponse').its('status').should('eq', 400)
})

Given('que o login institucional foi realizado para atualizar polo', () => autenticarPara('atualizar polo'))
Given('existe um polo para atualizar', () => buscarPolo())

When('eu atualizo os dados do polo', () => {
	cy.get('@authToken').then((token) => cy.get('@poloAtual').then((polo) => {
		cy.request({
			method: 'PUT',
			url: `${obterApiBaseUrl()}/api/v1/polos/${polo.uuid}/`,
			headers: { Authorization: `Bearer ${token}` },
			body: {
				codigo_eol: polo.codigo_eol,
				nome_polo: `${polo.nome_polo} - atualizado`,
				nome_osc: polo.nome_osc,
				dre_nome: polo.dre_nome,
				dre_codigo_eol: polo.dre_codigo_eol,
				tipo_ue: polo.tipo_ue,
				quantidade_maxima_alunos: polo.quantidade_maxima_alunos,
				tipo: polo.tipo,
				gestao: polo.gestao,
			},
			failOnStatusCode: false,
		}).as('atualizacaoPoloResponse')
	}))
})

When('eu envio um payload invalido para atualizar polo', () => {
	cy.get('@authToken').then((token) => cy.get('@poloAtual').then((polo) => {
		cy.request({ method: 'PUT', url: `${obterApiBaseUrl()}/api/v1/polos/${polo.uuid}/`, headers: { Authorization: `Bearer ${token}` }, body: {}, failOnStatusCode: false }).as('atualizacaoPoloErrorResponse')
	}))
})

Then('a API deve responder a atualizacao de polo com status 200', () => cy.get('@atualizacaoPoloResponse').its('status').should('eq', 200))
Then('a resposta deve conter os dados atualizados do polo', () => cy.get('@atualizacaoPoloResponse').its('body').should('include.all.keys', ['uuid', 'codigo_eol', 'nome_polo', 'nome_osc', 'dre_nome', 'dre_codigo_eol', 'tipo_ue', 'quantidade_maxima_alunos']))
Then('a API deve responder a atualizacao de polo com status 400', () => cy.get('@atualizacaoPoloErrorResponse').its('status').should('eq', 400))

Given('que o login institucional foi realizado para atualizar polo parcialmente', () => autenticarPara('atualizar polo parcialmente'))
Given('existe um polo para atualizar parcialmente', () => buscarPolo('poloParcial'))

When('eu atualizo parcialmente os dados do polo', () => {
	cy.get('@authToken').then((token) => cy.get('@poloParcial').then((polo) => {
		cy.request({ method: 'PATCH', url: `${obterApiBaseUrl()}/api/v1/polos/${polo.uuid}/`, headers: { Authorization: `Bearer ${token}` }, body: { nome_polo: `${polo.nome_polo} - parcial` }, failOnStatusCode: false }).as('atualizacaoPoloParcialResponse')
	}))
})

When('eu envio um payload invalido para atualizar polo parcialmente', () => {
	cy.get('@authToken').then((token) => cy.get('@poloParcial').then((polo) => {
		cy.request({ method: 'PATCH', url: `${obterApiBaseUrl()}/api/v1/polos/${polo.uuid}/`, headers: { Authorization: `Bearer ${token}` }, body: { nome_polo: '' }, failOnStatusCode: false }).as('atualizacaoPoloParcialErrorResponse')
	}))
})

Then('a API deve responder a atualizacao parcial de polo com status 200', () => cy.get('@atualizacaoPoloParcialResponse').its('status').should('eq', 200))
Then('a resposta deve conter os dados do polo atualizado parcialmente', () => cy.get('@atualizacaoPoloParcialResponse').its('body').should('include.all.keys', ['uuid', 'codigo_eol', 'nome_polo', 'nome_osc', 'dre_nome', 'dre_codigo_eol', 'tipo_ue', 'quantidade_maxima_alunos']))
Then('a API deve responder a atualizacao parcial de polo com status 400', () => cy.get('@atualizacaoPoloParcialErrorResponse').its('status').should('eq', 400))

Given('que o login institucional foi realizado para excluir polo', () => autenticarPara('excluir polo'))

Given('um polo exclusivo foi criado para exclusao', () => {
	cy.get('@authToken').then((token) => {
		cy.request({ method: 'POST', url: `${obterApiBaseUrl()}/api/v1/polos/`, headers: { Authorization: `Bearer ${token}` }, body: obterPoloPayload(), failOnStatusCode: false }).then((response) => {
			expect(response.status, JSON.stringify(response.body)).to.eq(201)
			cy.wrap(response.body.uuid).as('poloExclusaoUuid')
		})
	})
})

When('eu excluo o polo pelo UUID', () => {
	cy.get('@authToken').then((token) => cy.get('@poloExclusaoUuid').then((uuid) => {
		cy.request({ method: 'DELETE', url: `${obterApiBaseUrl()}/api/v1/polos/${uuid}/`, headers: { Authorization: `Bearer ${token}` }, failOnStatusCode: false }).as('exclusaoPoloResponse')
	}))
})

Then('a API deve responder a exclusao de polo com status 204', () => {
	cy.get('@exclusaoPoloResponse').its('status').should('eq', 204)
	cy.get('@exclusaoPoloResponse').its('body').should('be.empty')
})

Given('que o login institucional foi realizado para consultar DREs', () => autenticarPara('consultar DREs'))
When('eu consulto a lista de DREs', () => {
	cy.get('@authToken').then((token) => cy.request({ method: 'GET', url: `${obterApiBaseUrl()}/api/v1/polos/dres/`, headers: { Authorization: `Bearer ${token}` }, failOnStatusCode: false }).as('dresResponse'))
})
When('eu consulto a lista de DREs sem token', () => cy.request({ method: 'GET', url: `${obterApiBaseUrl()}/api/v1/polos/dres/`, failOnStatusCode: false }).as('dresErrorResponse'))
Then('a API deve responder a lista de DREs com status 200', () => cy.get('@dresResponse').its('status').should('eq', 200))
Then('a resposta deve conter uma lista de DREs', () => cy.get('@dresResponse').its('body').should('be.an', 'array'))
Then('a API deve responder a lista de DREs com status 401', () => cy.get('@dresErrorResponse').its('status').should('eq', 401))

Given('que o login institucional foi realizado para consultar tipos de escola', () => autenticarPara('consultar tipos de escola'))
When('eu consulto a lista de tipos de escola', () => {
	cy.get('@authToken').then((token) => cy.request({ method: 'GET', url: `${obterApiBaseUrl()}/api/v1/polos/tipos-escola/`, headers: { Authorization: `Bearer ${token}` }, failOnStatusCode: false }).as('tiposEscolaResponse'))
})
When('eu consulto a lista de tipos de escola sem token', () => cy.request({ method: 'GET', url: `${obterApiBaseUrl()}/api/v1/polos/tipos-escola/`, failOnStatusCode: false }).as('tiposEscolaErrorResponse'))
Then('a API deve responder a lista de tipos de escola com status 200', () => cy.get('@tiposEscolaResponse').its('status').should('eq', 200))
Then('a resposta deve conter uma lista de tipos de escola', () => cy.get('@tiposEscolaResponse').its('body').should('be.an', 'array'))
Then('a API deve responder a lista de tipos de escola com status 401', () => cy.get('@tiposEscolaErrorResponse').its('status').should('eq', 401))
