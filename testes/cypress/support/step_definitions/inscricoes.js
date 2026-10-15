const { Given, When, Then, Before, After } = require('@badeball/cypress-cucumber-preprocessor')
const { autenticarNaApi } = require('./autenticacao.cjs')
const campos = require('../../fixtures/inscricoes_campos.json')
const inexistente = '00000000-0000-0000-0000-000000000000'
let estado
Before({ tags: '@inscricoes' }, () => { estado = { criadas: [], respostas: [] } })
// Nao imprime respostas com dados pessoais do participante consultado na EOL.
const request = (method, path = '', options = {}, token = estado.token) => cy.request({
	method, url: `${Cypress.env('api_base_url').replace(/\/$/, '')}/api/v1/inscricoes/${path}`,
	failOnStatusCode: false, log: false,
	...(token ? { headers: { Authorization: `Bearer ${token}` } } : {}), ...options,
})
const status = (res, esperado) => expect(res.status, `HTTP esperado ${esperado}, recebido ${res.status}`).to.eq(esperado)
const contrato = (body, nome) => expect(body).to.include.all.keys(campos[nome])
const autenticar = () => autenticarNaApi().then(({ body }) => { estado.token = body.token })
const registrar = (res) => {
	if (res.status === 201 && res.body.uuid) estado.criadas.push(res.body.uuid)
	return res
}
const rota = (nome, uuid = inexistente) => nome === 'lista' ? '' : nome === 'detalhe' ? `${uuid}/` : ['cancelar', 'reativar'].includes(nome) ? `${uuid}/${nome}/` : `${nome}/`
const resposta = (chain) => chain.as('inscricaoResponse')
After({ tags: '@inscricoes' }, () => {
	const falhas = []
	return cy.wrap([...estado.criadas].reverse(), { log: false }).each((uuid) => request('DELETE', `${uuid}/`).then((res) => {
		const ausente = res.status === 400 && res.body?.detalhe === 'Inscrição não encontrada.'
		if (![204, 404].includes(res.status) && !ausente) falhas.push(`${uuid}: HTTP ${res.status}`)
	})).then(() => expect(falhas, 'Limpeza de inscricoes exclusivas').to.be.empty)
})
Given('que autentiquei para gerenciar inscricoes', autenticar)
Given('que criei uma inscricao exclusiva em rascunho', () => autenticar().then(() => {
	estado.payload = { nome_participante: `Participante teste ${Date.now()}-${Cypress._.random(100000, 999999)}`, responsavel_nome: 'Responsavel ficticio', email: 'teste@example.com' }
	return request('POST', '', { body: estado.payload }).then(registrar)
}).then((res) => {
	status(res, 201)
	contrato(res.body, 'InscricaoInformacoesBasicas')
	expect(res.body.uuid).to.be.a('string').and.not.be.empty
	expect(res.body).to.include(estado.payload)
	expect(res.body.status).to.eq('RASCUNHO')
	estado.uuid = res.body.uuid
	return request('GET', `${estado.uuid}/`)
}).then((res) => {
	status(res, 200)
	contrato(res.body, 'InscricaoDetalhe')
	estado.original = res.body
}))
Then('a inscricao deve estar persistida em rascunho', () => {
	expect(estado.original).to.include({ ...estado.payload, uuid: estado.uuid, status: 'RASCUNHO' })
})
When('atualizo a inscricao exclusiva com {string}', (metodo) => {
	estado.nomeAtualizado = `${estado.payload.nome_participante} atualizado`
	return resposta(request(metodo, `${estado.uuid}/`, { body: metodo === 'PUT' ? { ...estado.payload, nome_participante: estado.nomeAtualizado } : { nome_participante: estado.nomeAtualizado } }))
})
Then('a alteracao da inscricao deve persistir preservando os demais campos', () => request('GET', `${estado.uuid}/`).then((res) => {
	status(res, 200)
	contrato(res.body, 'InscricaoDetalhe')
	expect(res.body.nome_participante).to.eq(estado.nomeAtualizado)
	for (const [campo, valor] of Object.entries(estado.original)) if (!['nome_participante', 'atualizado_em'].includes(campo)) expect(res.body[campo], campo).to.deep.eq(valor)
}))
When('cancelo a inscricao exclusiva', () => resposta(request('POST', `${estado.uuid}/cancelar/`)))
When('reativo a inscricao exclusiva', () => resposta(request('POST', `${estado.uuid}/reativar/`)))
Then('a inscricao deve estar persistida com status {string}', (esperado) => {
	cy.get('@inscricaoResponse', { log: false }).its('body.status', { log: false }).should('eq', esperado)
	return request('GET', `${estado.uuid}/`).then((res) => {
		status(res, 200)
		contrato(res.body, 'InscricaoDetalhe')
		expect(res.body.status).to.eq(esperado)
		expect(res.body).to.include(estado.payload)
	})
})
When('excluo a inscricao exclusiva', () => resposta(request('DELETE', `${estado.uuid}/`)))
Then('a inscricao excluida deve ser informada como nao encontrada', () => {
	cy.get('@inscricaoResponse', { log: false }).its('body', { log: false }).should('be.empty')
	return request('GET', `${estado.uuid}/`).then((res) => {
		status(res, 400)
		expect(res.body).to.deep.eq({ detalhe: 'Inscrição não encontrada.' })
	})
})
When('filtro inscricoes pelo nome exclusivo', () => resposta(request('GET', '', { qs: { nome_participante: estado.payload.nome_participante, page_size: 1 } })))
Then('a lista paginada deve conter apenas a inscricao exclusiva', () => cy.get('@inscricaoResponse', { log: false }).then(({ body }) => {
	expect(body.count).to.eq(1)
	expect(body.results).to.be.an('array').and.have.length(1)
	contrato(body.results[0], 'InscricaoListagem')
	expect(body.results[0].uuid).to.eq(estado.uuid)
}))
When('busco inscricoes sem correspondencia', () => resposta(request('GET', '', { qs: { nome_participante: `Inexistente-${Date.now()}-${Cypress._.random(100000, 999999)}` } })))
Then('a lista de inscricoes deve estar vazia', () => cy.get('@inscricaoResponse', { log: false }).then(({ body }) => {
	expect(body.count).to.eq(0)
	expect(body.results).to.deep.eq([])
}))
When('consulto o recurso de inscricoes {string}', (nome) => resposta(request('GET', rota(nome))))
Then('o recurso de inscricoes {string} deve respeitar o contrato', (nome) => cy.get('@inscricaoResponse', { log: false }).then(({ body }) => {
	if (nome === 'polos-elegiveis') {
		expect(body.count).to.be.a('number').and.at.least(0)
		expect(body.results).to.be.an('array')
		body.results.forEach((polo) => contrato(polo, 'PoloElegivel'))
	} else {
		contrato(body, 'ValoresChoicesResponse')
		campos.ValoresChoicesResponse.forEach((campo) => {
			expect(body[campo], campo).to.be.an('array').and.not.be.empty
			body[campo].forEach((item) => expect(item).to.be.an('object').and.not.be.empty)
		})
	}
}))
When('acesso inscricoes com {string} em {string} com token {string}', (metodo, nome, token) => {
	cy.clearCookies()
	return resposta(request(metodo, rota(nome), ['POST', 'PUT', 'PATCH'].includes(metodo) ? { body: {} } : {}, token === 'ausente' ? null : 'token-invalido'))
})
When('acesso inscricao inexistente com {string} em {string}', (metodo, nome) => resposta(request(metodo, rota(nome), ['PUT', 'PATCH'].includes(metodo) ? { body: {} } : {})))
Then('a inscricao deve responder com status {int}', (esperado) => cy.get('@inscricaoResponse', { log: false }).then((res) => status(res, esperado)))
When('envio a violacao de inscricao {string} por POST PUT e PATCH', (regra) => {
	const erros = {
		'email invalido': { email: 'email-invalido' }, 'data invalida': { data_nascimento: '2020-02-30' },
		'nome longo': { nome_participante: 'X'.repeat(256) }, 'tipo invalido': { tipo_estudante: 'INVALIDO' },
		'grupo invalido': { grupo: 'INVALIDO' }, 'polo inexistente': { polo: inexistente }, 'edicao inexistente': { edicao: inexistente },
	}
	expect(erros).to.have.property(regra)
	return cy.wrap(['POST', 'PUT', 'PATCH'], { log: false }).each((method) => request(method, method === 'POST' ? '' : `${estado.uuid}/`, {
		body: method === 'PATCH' ? erros[regra] : { ...estado.payload, ...erros[regra] },
	}).then(registrar).then((res) => { estado.respostas.push({ method, res }) }))
})
Then('as operacoes de inscricao devem retornar 400 e preservar os dados', () => {
	estado.respostas.forEach(({ method, res }) => {
		expect(res.status, `${method}: status HTTP`).to.eq(400)
		expect(res.body).not.to.be.empty
	})
	return request('GET', `${estado.uuid}/`).then((res) => {
		status(res, 200)
		expect(res.body).to.deep.eq(estado.original)
	})
})
Then('a resposta deve indicar inscricao nao encontrada', () => cy.get('@inscricaoResponse', { log: false }).its('body', { log: false }).should('deep.eq', { detalhe: 'Inscrição não encontrada.' }))
