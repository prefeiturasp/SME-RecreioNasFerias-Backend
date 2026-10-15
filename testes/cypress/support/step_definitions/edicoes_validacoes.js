const { Given, When, Then, Before, After } = require('@badeball/cypress-cucumber-preprocessor')
const { autenticarNaApi } = require('./autenticacao.cjs')

const raiz = '/api/v1/edicoes/'
const inexistente = '00000000-0000-0000-0000-000000000000'
const camposEditaveis = ['nome', 'data_inicio', 'data_fim', 'inscricoes_inicio', 'inscricoes_fim']
const editar = (edicao) => Object.fromEntries(camposEditaveis.map((campo) => [campo, edicao[campo]]))
const dia = (data, deslocamento) => new Date(Date.parse(`${data}T00:00:00Z`) + deslocamento * 86400000).toISOString().slice(0, 10)
let estado

Before({ tags: '@edicoes_validacoes' }, () => {
	estado = { criadas: [], edicoes: [], payloads: [], respostas: [] }
})

const requisitar = (method, uuid = '', body, token = estado.token) => cy.request({
	method, url: `${Cypress.env('api_base_url').replace(/\/$/, '')}${raiz}${uuid ? `${uuid}/` : ''}`,
	failOnStatusCode: false,
	...(token ? { headers: { Authorization: `Bearer ${token}` } } : {}),
	...(body === undefined ? {} : { body }),
})
const status = (res, esperado) => expect(res.status, JSON.stringify(res.body)).to.eq(esperado)
const autenticar = () => autenticarNaApi().then(({ body }) => { estado.token = body.token })
const registrar = (res) => {
	if (res.status === 201 && res.body.uuid) estado.criadas.push(res.body.uuid)
	return res
}

After({ tags: '@edicoes_validacoes' }, () => {
	const falhas = []
	return cy.wrap([...estado.criadas].reverse(), { log: false }).each((uuid) => requisitar('DELETE', uuid).then((res) => {
		if (![204, 404].includes(res.status)) falhas.push(`${uuid}: HTTP ${res.status}`)
	})).then(() => expect(falhas, 'Limpeza das edicoes criadas pelo cenario').to.be.empty)
})

Given('que autentiquei para validar as regras de edicoes', autenticar)
Given('que existem duas edicoes exclusivas para validar regras', () => autenticar().then(() => requisitar('GET')).then((res) => {
	status(res, 200)
	expect(res.body).to.be.an('array')
	const hoje = new Date().toISOString().slice(0, 10)
	const maiorFim = res.body.reduce((maior, edicao) => [maior, edicao.data_fim, edicao.inscricoes_fim].sort().pop(), dia(hoje, 30))
	return cy.wrap([0, 1], { log: false }).each((indice) => {
		const deslocamento = 1 + indice * 20
		const body = {
			nome: `Validacao de edicoes ${Date.now()}-${Cypress._.random(100000, 999999)}-${indice}`,
			inscricoes_inicio: dia(maiorFim, deslocamento), inscricoes_fim: dia(maiorFim, deslocamento + 2),
			data_inicio: dia(maiorFim, deslocamento + 3), data_fim: dia(maiorFim, deslocamento + 10),
		}
		estado.payloads.push(body)
		return requisitar('POST', '', body).then(registrar).then((response) => {
			status(response, 201)
			expect(response.body.uuid).to.be.a('string').and.not.be.empty
			estado.edicoes.push(response.body)
		})
	})
}))

When('acesso edicoes com {string} em {string} com token {string}', (metodo, rota, token) => {
	cy.clearCookies()
	return requisitar(metodo, rota === 'lista' ? '' : inexistente,
		['POST', 'PUT', 'PATCH'].includes(metodo) ? {} : undefined,
		token === 'invalido' ? 'token-invalido' : null).as('validacaoEdicoesResponse')
})
When('acesso uma edicao inexistente com {string}', (metodo) => requisitar(metodo, inexistente,
	['PUT', 'PATCH'].includes(metodo) ? {} : undefined).as('validacaoEdicoesResponse'))
Then('a validacao de edicoes deve responder com status {int}', (esperado) => cy.get('@validacaoEdicoesResponse').then((res) => status(res, esperado)))

const violacao = (regra, base, outra) => {
	switch (regra) {
		case 'nome duplicado': return { nome: outra.nome }
		case 'nome duplicado em maiusculas': return { nome: outra.nome.toUpperCase() }
		case 'nome acima de 255 caracteres': return { nome: 'X'.repeat(256) }
		case 'data invalida': return { data_inicio: '2030-02-30' }
		case 'fim anterior ao inicio': return { data_fim: dia(base.data_inicio, -1) }
		case 'inscricoes invertidas': return { inscricoes_fim: dia(base.inscricoes_inicio, -1) }
		case 'inscricoes apos fim da edicao': return { inscricoes_fim: dia(base.data_fim, 1) }
		case 'sobreposicao de edicoes': return { data_inicio: outra.data_inicio, data_fim: outra.data_fim }
		case 'sobreposicao de inscricoes': return { inscricoes_inicio: outra.inscricoes_inicio, inscricoes_fim: outra.inscricoes_fim }
		default: throw new Error(`Regra desconhecida: ${regra}`)
	}
}

When('envio edicoes com a violacao {string} por POST PUT e PATCH', (regra) => {
	// A segunda edicao tem datas posteriores: sobrepor apenas as inscricoes da
	// primeira nao viola a regra independente de inscricoes apos o fim da edicao.
	const base = editar(estado.edicoes[1])
	const outra = estado.edicoes[0]
	return cy.wrap(['POST', 'PUT', 'PATCH'], { log: false }).each((metodo) => {
		const candidato = metodo === 'POST' ? {
			nome: `Nova validacao ${Date.now()}-${Cypress._.random(100000, 999999)}`,
			inscricoes_inicio: dia(base.data_fim, 1), inscricoes_fim: dia(base.data_fim, 3),
			data_inicio: dia(base.data_fim, 4), data_fim: dia(base.data_fim, 10),
		} : base
		let alteracoes = violacao(regra, candidato, outra)
		if (regra === 'sobreposicao de edicoes') {
			// Mantem inscricoes validas e isoladas do periodo da outra edicao.
			alteracoes = { ...alteracoes, inscricoes_inicio: candidato.inscricoes_inicio, inscricoes_fim: candidato.inscricoes_fim,
				data_inicio: outra.data_inicio, data_fim: candidato.data_fim }
		}
		const body = metodo === 'PATCH' ? alteracoes : { ...candidato, ...alteracoes }
		return requisitar(metodo, metodo === 'POST' ? '' : estado.edicoes[1].uuid, body).then(registrar).then((res) => {
			estado.respostas.push({ metodo, response: res })
		})
	})
})
Then('as tres operacoes devem retornar 400 sem alterar as edicoes', () => {
	for (const { metodo, response } of estado.respostas) {
		expect(response.status, `${metodo}: ${JSON.stringify(response.body)}`).to.eq(400)
		expect(response.body, `${metodo}: mensagem de validacao`).not.to.be.empty
	}
	return cy.wrap(estado.edicoes, { log: false }).each((edicao) => requisitar('GET', edicao.uuid).then((res) => {
		status(res, 200)
		expect(editar(res.body)).to.deep.eq(editar(edicao))
	}))
})

Then('a primeira edicao deve estar persistida conforme enviada', () => requisitar('GET', estado.edicoes[0].uuid).then((res) => {
	status(res, 200)
	expect(res.body).to.include(estado.payloads[0])
	expect(res.body.status).to.eq('planejada')
	expect(res.body.status_label).to.eq('Planejada')
}))
When('altero a primeira edicao por PUT e PATCH', () => {
	estado.put = { ...estado.payloads[0], nome: `${estado.payloads[0].nome} PUT`, data_fim: dia(estado.payloads[0].data_fim, 1) }
	return requisitar('PUT', estado.edicoes[0].uuid, estado.put).then((res) => {
		status(res, 200)
		expect(res.body).to.include(estado.put)
		return requisitar('GET', estado.edicoes[0].uuid)
	}).then((res) => {
		status(res, 200)
		expect(res.body).to.include(estado.put)
		estado.antesPatch = res.body
		estado.nomePatch = `${estado.payloads[0].nome} PATCH`
		return requisitar('PATCH', estado.edicoes[0].uuid, { nome: estado.nomePatch })
	}).then((res) => {
		status(res, 200)
		expect(res.body.nome).to.eq(estado.nomePatch)
	})
})
Then('os valores devem persistir e o PATCH deve preservar os demais campos', () => requisitar('GET', estado.edicoes[0].uuid).then((res) => {
	status(res, 200)
	expect(res.body.nome).to.eq(estado.nomePatch)
	for (const [campo, valor] of Object.entries(estado.antesPatch)) {
		if (!['nome', 'atualizado_em'].includes(campo)) expect(res.body[campo], campo).to.deep.eq(valor)
	}
}))
When('excluo a primeira edicao exclusiva de validacao', () => requisitar('DELETE', estado.edicoes[0].uuid).as('validacaoEdicoesResponse'))
Then('consultar a edicao excluida deve retornar 404', () => {
	cy.get('@validacaoEdicoesResponse').its('body').should('be.empty')
	return requisitar('GET', estado.edicoes[0].uuid).then((res) => status(res, 404))
})
