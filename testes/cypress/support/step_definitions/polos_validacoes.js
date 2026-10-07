const { Given, When, Then, Before, After } = require('@badeball/cypress-cucumber-preprocessor')
const { autenticarNaApi } = require('./autenticacao.cjs')
const campos = require('../../fixtures/polos_campos.json')
const inexistente = '00000000-0000-0000-0000-000000000000'
let estado

Before({ tags: '@polos_validacoes' }, () => { estado = { criados: [], polos: [], payloads: [], respostas: [] } })
const request = (method, path = '', options = {}, token = estado.token) => cy.request({
	method, url: `${Cypress.env('api_base_url').replace(/\/$/, '')}/api/v1/polos/${path}`,
	failOnStatusCode: false, ...(token ? { headers: { Authorization: `Bearer ${token}` } } : {}), ...options,
})
const status = (res, esperado) => expect(res.status, JSON.stringify(res.body)).to.eq(esperado)
const contrato = (body, nome) => expect(body).to.include.all.keys(campos[nome])
const registrar = (res) => {
	if (res.status === 201 && res.body.uuid) estado.criados.push(res.body.uuid)
	return res
}
const autenticar = () => autenticarNaApi().then(({ body }) => { estado.token = body.token })
const rota = (nome) => nome === 'lista' ? '' : nome === 'detalhe' ? `${inexistente}/` : `${nome}/`
After({ tags: '@polos_validacoes' }, () => {
	const falhas = []
	return cy.wrap([...estado.criados].reverse(), { log: false }).each((uuid) => request('DELETE', `${uuid}/`).then((res) => {
		if (![204, 404].includes(res.status)) falhas.push(`${uuid}: HTTP ${res.status}`)
	})).then(() => expect(falhas, 'Limpeza de polos exclusivos').to.be.empty)
})
Given('que autentiquei para validar polos', autenticar)
Given('que existem dois polos exclusivos de validacao', () => autenticar().then(() => {
	estado.marca = `Validacao-${Date.now()}-${Cypress._.random(100000, 999999)}`
	return cy.wrap([0, 1], { log: false }).each((indice) => {
		const body = {
			codigo_eol: String(Cypress._.random(1000000, 9999999)), nome_polo: `${estado.marca}-polo-${indice}`,
			nome_osc: `${estado.marca}-osc-${indice}`, dre_nome: `DRE teste ${indice}`, dre_codigo_eol: `${estado.marca}-${indice}`,
			tipo_ue: indice ? 'CEI' : 'EMEF', gestao: indice ? 'parceira' : 'direta', tipo: 'pendente',
			quantidade_maxima_alunos: 100,
		}
		estado.payloads.push(body)
		return request('POST', '', { body }).then(registrar).then((res) => {
			status(res, 201)
			contrato(res.body, 'Polo')
			estado.polos.push(res.body)
		})
	})
}))
When('valido acesso a polos com {string} em {string} e token {string}', (metodo, nome, token) => {
	cy.clearCookies()
	return request(metodo, rota(nome), ['POST', 'PUT', 'PATCH'].includes(metodo) ? { body: {} } : {}, token === 'ausente' ? null : 'token-invalido').as('polosValidacaoResponse')
})
When('valido polo inexistente com {string}', (metodo) => request(metodo, `${inexistente}/`, ['PUT', 'PATCH'].includes(metodo) ? { body: {} } : {}).as('polosValidacaoResponse'))
Then('a validacao de polos deve retornar {int}', (esperado) => cy.get('@polosValidacaoResponse').then((res) => status(res, esperado)))

When('valido a regra de polos {string} por POST PUT e PATCH', (regra) => {
	const erros = {
		'nome duplicado': { nome_polo: estado.polos[1].nome_polo },
		'nome duplicado em maiusculas': { nome_polo: estado.polos[1].nome_polo.toUpperCase() },
		'codigo duplicado': { codigo_eol: estado.polos[1].codigo_eol },
		'codigo curto': { codigo_eol: '12345' }, 'codigo longo': { codigo_eol: '12345678' },
		'nome longo': { nome_polo: 'X'.repeat(256) }, 'capacidade negativa': { quantidade_maxima_alunos: -1 },
		'capacidade nao numerica': { quantidade_maxima_alunos: 'abc' }, 'tipo invalido': { tipo: 'invalido' },
		'gestao invalida': { gestao: 'invalida' }, 'status invalido': { status: 'invalido' },
	}
	expect(erros).to.have.property(regra)
	return cy.wrap(['POST', 'PUT', 'PATCH'], { log: false }).each((method) => {
		const base = method === 'POST' ? { ...estado.payloads[0], nome_polo: `${estado.marca}-novo`, codigo_eol: String(Cypress._.random(1000000, 9999999)) } : estado.payloads[0]
		return request(method, method === 'POST' ? '' : `${estado.polos[0].uuid}/`, { body: method === 'PATCH' ? erros[regra] : { ...base, ...erros[regra] } }).then(registrar).then((res) => { estado.respostas.push({ method, res }) })
	})
})
Then('as operacoes de polos devem retornar 400 e preservar os dados', () => {
	estado.respostas.forEach(({ method, res }) => {
		expect(res.status, `${method}: ${JSON.stringify(res.body)}`).to.eq(400)
		expect(res.body).not.to.be.empty
	})
	return cy.wrap(estado.polos, { log: false }).each((polo) => request('GET', `${polo.uuid}/`).then((res) => {
		status(res, 200)
		expect(res.body).to.deep.eq(polo)
	}))
})

When('filtro os polos de validacao por {string}', (filtro) => {
	const polo = estado.polos[0]
	const filtros = {
		nome: { busca: polo.nome_polo }, osc: { busca: polo.nome_osc },
		dre: { busca: estado.marca, dre_codigo_eol: polo.dre_codigo_eol },
		tipo_ue: { busca: estado.marca, tipo_ue: polo.tipo_ue },
		gestao: { busca: estado.marca, gestao: polo.gestao },
		combinados: { busca: estado.marca, dre_codigo_eol: polo.dre_codigo_eol, tipo_ue: polo.tipo_ue, gestao: polo.gestao },
	}
	return request('GET', '', { qs: { ...filtros[filtro], desabilita_paginacao: true } }).as('polosValidacaoResponse')
})
Then('o filtro deve retornar apenas o primeiro polo', () => cy.get('@polosValidacaoResponse').then((res) => {
	status(res, 200)
	expect(res.body).to.be.an('array').and.have.length(1)
	contrato(res.body[0], 'Polo')
	expect(res.body[0].uuid).to.eq(estado.polos[0].uuid)
}))
When('consulto duas paginas dos polos de validacao', () => cy.wrap([1, 2], { log: false }).each((page) => request('GET', '', { qs: { busca: estado.marca, page_size: 1, page } }).then((res) => {
	status(res, 200)
	expect(res.body.count).to.eq(2)
	expect(res.body.results).to.be.an('array').and.have.length(1)
	contrato(res.body.results[0], 'Polo')
	estado.respostas.push(res.body.results[0].uuid)
})))
Then('as paginas devem conter os dois polos sem repeticao', () => expect(estado.respostas).to.have.members(estado.polos.map((polo) => polo.uuid)))
When('busco um polo sem correspondencia', () => request('GET', '', { qs: { busca: `${estado.marca}-inexistente`, desabilita_paginacao: true } }).as('polosValidacaoResponse'))
Then('a busca de polos deve retornar lista vazia', () => cy.get('@polosValidacaoResponse').its('body').should('deep.eq', []))

When('verifico a persistencia da criacao e das atualizacoes do polo', () => request('GET', `${estado.polos[0].uuid}/`).then((res) => {
	status(res, 200)
	expect(res.body).to.include(estado.payloads[0])
	estado.put = { ...estado.payloads[0], nome_polo: `${estado.marca}-PUT`, quantidade_maxima_alunos: 120 }
	return request('PUT', `${estado.polos[0].uuid}/`, { body: estado.put })
}).then((res) => {
	status(res, 200)
	expect(res.body).to.include(estado.put)
	return request('GET', `${estado.polos[0].uuid}/`)
}).then((res) => {
	status(res, 200)
	expect(res.body).to.include(estado.put)
	estado.antesPatch = res.body
	return request('PATCH', `${estado.polos[0].uuid}/`, { body: { nome_polo: `${estado.marca}-PATCH` } })
}).then((res) => { status(res, 200); expect(res.body.nome_polo).to.eq(`${estado.marca}-PATCH`) }))
Then('o PATCH do polo deve preservar os campos omitidos', () => request('GET', `${estado.polos[0].uuid}/`).then((res) => {
	status(res, 200)
	expect(res.body.nome_polo).to.eq(`${estado.marca}-PATCH`)
	for (const [campo, valor] of Object.entries(estado.antesPatch)) if (!['nome_polo', 'atualizado_em'].includes(campo)) expect(res.body[campo], campo).to.deep.eq(valor)
}))
When('excluo o polo exclusivo de validacao', () => request('DELETE', `${estado.polos[0].uuid}/`).as('polosValidacaoResponse'))
Then('o polo excluido deve retornar 404', () => {
	cy.get('@polosValidacaoResponse').its('body').should('be.empty')
	return request('GET', `${estado.polos[0].uuid}/`).then((res) => status(res, 404))
})
When('consulto dados da unidade sem codigo EOL', () => request('GET', 'dados-da-unidade/').as('polosValidacaoResponse'))
Then('os dados da unidade sem codigo devem estar vazios', () => cy.get('@polosValidacaoResponse').its('body').then((body) => {
	contrato(body, 'DadosUnidade')
	Object.entries(body).forEach(([campo, valor]) => expect(valor, campo).to.eq(''))
}))
