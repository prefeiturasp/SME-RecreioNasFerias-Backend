const { Given, When, Then, Before, After } = require('@badeball/cypress-cucumber-preprocessor')
const { autenticarNaApi, validarToken } = require('./autenticacao.cjs')
const campos = require('../../fixtures/definicoes_polos_campos.json')

// Contrato: /api/v1/schema/ de QA, consultado em 07/10/2026.

const uuidInexistente = '00000000-0000-0000-0000-000000000000'
const raiz = '/api/v1/definicoes-polos/'
let contexto

Before({ tags: '@definicoes_polos' }, () => {
	contexto = { polos: [], edicoes: [], definicoes: [], limpeza: [] }
})

const requisitar = (method, path, options = {}, autenticado = true) => cy.request({
	method,
	url: `${Cypress.env('api_base_url').replace(/\/$/, '')}${path}`,
	failOnStatusCode: false, log: false,
	...(autenticado ? { headers: { Authorization: `Bearer ${contexto.token}` } } : {}),
	...options,
})

const validarStatus = (response, status) => {
	expect(response.status, `HTTP esperado: ${status}; resposta: ${JSON.stringify(response.body)}`).to.eq(status)
}

const validarCampos = (objeto, contrato) => {
	expect(objeto).to.be.an('object')
	expect(objeto).to.include.all.keys(campos[contrato])
}

const autenticar = () => autenticarNaApi().then(({ body }) => {
	validarToken(body.token)
	contexto.token = body.token
})

// Registra imediatamente os recursos criados, inclusive se uma assercao posterior falhar.
const registrar = (response, recurso) => {
	if (response.status === 201 && response.body.uuid) {
		contexto.limpeza.push(`/api/v1/${recurso}/${response.body.uuid}/`)
	}
	validarStatus(response, 201)
	expect(response.body.uuid).to.be.a('string').and.not.be.empty
	return response.body
}

After({ tags: '@definicoes_polos' }, () => {
	if (!contexto.token) return
	const falhas = []
	// Vinculos antes de polos e edicoes; remove apenas UUIDs criados neste cenario.
	return cy.wrap([...contexto.limpeza].reverse(), { log: false }).each((path) => {
		return requisitar('DELETE', path).then((response) => {
			const ausente = response.status === 400 && response.body?.detalhe === 'Definição de Polo não encontrada.'
			if (![204, 404].includes(response.status) && !ausente) falhas.push(`${path}: HTTP ${response.status}`)
		})
	}).then(() => expect(falhas, 'Falhas na limpeza dos dados exclusivos').to.be.empty)
})

const criarDados = () => autenticar().then(() => {
	return requisitar('GET', '/api/v1/edicoes/').then((response) => {
		validarStatus(response, 200)
		expect(response.body).to.be.an('array')
		const maiorFim = response.body.reduce((maior, item) => [maior, item.data_fim, item.inscricoes_fim].sort().pop(), '2030-01-01')
		const data = new Date(`${maiorFim}T00:00:00Z`)
		const dia = (offset) => new Date(data.getTime() + offset * 86400000).toISOString().slice(0, 10)
		const identificador = `${Date.now()}-${Cypress._.random(100000, 999999)}`
		return cy.wrap([0, 1], { log: false }).each((indice) => {
			const inicio = 1 + indice * 10
			return requisitar('POST', '/api/v1/edicoes/', { body: {
				nome: `Definicoes automatizadas ${identificador}-${indice}`,
				data_inicio: dia(inicio + 2), data_fim: dia(inicio + 7),
				inscricoes_inicio: dia(inicio), inscricoes_fim: dia(inicio + 1),
			} }).then((res) => { contexto.edicoes.push(registrar(res, 'edicoes')) })
		}).then(() => cy.wrap([0, 1], { log: false }).each((indice) => {
			return requisitar('POST', '/api/v1/polos/', { body: {
				codigo_eol: String(Cypress._.random(1000000, 9999999)),
				nome_polo: `Polo definicoes ${identificador}-${indice}`,
				nome_osc: 'OSC automatizada', dre_nome: 'DRE automatizada',
				dre_codigo_eol: `TESTE-${identificador}-${indice}`, tipo_ue: indice ? 'CEI' : 'EMEF',
				quantidade_maxima_alunos: 100, tipo: 'oficial', gestao: indice ? 'parceira' : 'direta',
				ponto_focal_nome: 'Contato de teste', ponto_focal_email: 'teste@example.com', ponto_focal_telefone: '11999999999',
			} }).then((res) => { contexto.polos.push(registrar(res, 'polos')) })
		}))
	})
})

const payload = (indice = 0) => ({
	polo: contexto.polos[indice].uuid, edicao: contexto.edicoes[0].uuid,
	tipo: indice ? 'reserva' : 'pendente', projecao_inscritos: 20,
})

const criarDefinicao = (indice = 0) => requisitar('POST', raiz, { body: payload(indice) }).then((response) => {
	contexto.definicoes.push(registrar(response, 'definicoes-polos'))
	return response
})

const detalhe = (indice = 0) => `${raiz}${contexto.definicoes[indice].uuid}/`
const rota = (nome) => nome === 'lista' ? raiz : nome === 'detalhe' ? `${raiz}${uuidInexistente}/` : `${raiz}${nome}/`
const responder = (chain) => chain.as('definicoesResponse')

Given('que estou autenticado para gerenciar definicoes de polos', autenticar)
Given('que existem polos e edicoes exclusivos para definir participacoes', criarDados)
Given('que existe uma definicao de polo exclusiva para o teste', () => criarDados().then(() => criarDefinicao()))
Given('que existem duas definicoes de polos exclusivas para o teste', () => criarDados()
  .then(() => criarDefinicao(0))
  .then(() => criarDefinicao(1))
  .then(() => requisitar('PATCH', detalhe(1), { body: { tipo: 'reserva' } }))
  .then((res) => {
    validarStatus(res, 200)
    expect(res.body.tipo, 'Segundo vinculo preparado como reserva').to.eq('reserva')
    contexto.definicoes[1].tipoPreparado = res.body.tipo
  }))

When('consulto as definicoes de polos com paginacao', () => responder(requisitar('GET', raiz, { qs: { page_size: 2 } })))
When('filtro as definicoes pela edicao e codigo EOL do teste', () => responder(requisitar('GET', raiz, {
	qs: { edicao: contexto.edicoes[0].uuid, busca: contexto.polos[0].codigo_eol, desabilita_paginacao: true },
})))
When('vinculo o primeiro polo a primeira edicao', () => responder(criarDefinicao()))
When('consulto a definicao de polo do teste', () => responder(requisitar('GET', detalhe())))
When('atualizo a definicao de polo com {string}', (metodo) => {
	contexto.alteracoes = { projecao_inscritos: 35, tipo: 'reserva' }
	return responder(requisitar(metodo, detalhe(), { body: metodo === 'PUT' ? { ...payload(), ...contexto.alteracoes } : contexto.alteracoes }))
})
When('excluo a definicao de polo do teste', () => responder(requisitar('DELETE', detalhe())))
When('consulto o historico do polo do teste', () => responder(requisitar('GET', `${raiz}historico/`, { qs: { polo: contexto.polos[0].uuid } })))
When('consulto o historico sem informar um polo', () => responder(requisitar('GET', `${raiz}historico/`)))
When('consulto uma definicao de polo inexistente', () => responder(requisitar('GET', rota('detalhe'))))

When('vinculo os polos do teste em massa', () => responder(requisitar('POST', `${raiz}vincular-em-massa/`, { body: {
	polos: contexto.polos.map((polo) => polo.uuid), edicao: contexto.edicoes[0].uuid, projecao_inscritos: 20,
} }).then((response) => {
	if (Array.isArray(response.body.criadas)) {
		response.body.criadas.forEach((item) => {
			if (contexto.polos.some((polo) => polo.uuid === item.polo) && item.uuid) {
				contexto.limpeza.push(`${raiz}${item.uuid}/`)
				contexto.definicoes.push(item)
			}
		})
	}
	return response
})))

When('altero a edicao das definicoes em massa', () => responder(requisitar('POST', `${raiz}alterar-edicao-em-massa/`, { body: {
	definicoes: contexto.definicoes.map((item) => item.uuid), edicao_destino: contexto.edicoes[1].uuid,
} })))
When('altero o tipo dos polos em massa', () => responder(requisitar('POST', `${raiz}alterar-tipo-em-massa/`, {
	body: contexto.polos.map((polo) => ({ polo_uuid: polo.uuid, edicao: contexto.edicoes[0].uuid, tipo: 'reserva' })),
})))

When('acesso definicoes de polos com {string} em {string} sem token', (metodo, nome) => {
	cy.clearCookies()
	return responder(requisitar(metodo, rota(nome), ['POST', 'PUT', 'PATCH'].includes(metodo) ? { body: {} } : {}, false))
})
When('envio um payload invalido para definicoes em {string}', (nome) => responder(requisitar('POST', rota(nome), {
	body: nome === 'alterar-tipo-em-massa' ? [{}] : {},
})))
When('envio uma projecao negativa com {string}', (metodo) => responder(requisitar(metodo, detalhe(), {
	body: metodo === 'PUT' ? { ...payload(), projecao_inscritos: -1 } : { projecao_inscritos: -1 },
})))

Then('a resposta de definicoes de polos deve ter status {int}', (status) => cy.get('@definicoesResponse', { log: false }).then((res) => validarStatus(res, status)))
Then('a listagem de definicoes deve respeitar o contrato paginado', () => cy.get('@definicoesResponse', { log: false }).its('body').then((body) => {
	expect(body).to.include.all.keys('count', 'results')
	expect(body.count).to.be.a('number').and.at.least(0)
	expect(body.results).to.be.an('array').and.have.length.at.most(2)
	body.results.forEach((item) => validarCampos(item, 'PoloComDefinicao'))
}))
Then('a listagem deve conter apenas a definicao do teste', () => cy.get('@definicoesResponse', { log: false }).its('body').then((body) => {
	expect(body).to.be.an('array').and.have.length(1)
	validarCampos(body[0], 'PoloComDefinicao')
	expect(body[0]).to.include({ polo_uuid: contexto.polos[0].uuid, edicao_uuid: contexto.edicoes[0].uuid, definicao_uuid: contexto.definicoes[0].uuid })
}))
Then('a definicao criada deve corresponder aos dados enviados', () => cy.get('@definicoesResponse', { log: false }).its('body').then((body) => {
	validarCampos(body, 'DefinicaoPolo')
	expect(body).to.include(payload())
}))
Then('o detalhe deve identificar o polo e a edicao do teste', () => cy.get('@definicoesResponse', { log: false }).its('body').then((body) => {
	validarCampos(body, 'DefinicaoPoloDetalhamento')
	expect(body.uuid).to.eq(contexto.definicoes[0].uuid)
	expect(body.polo.uuid).to.eq(contexto.polos[0].uuid)
	expect(body).to.include({ ponto_focal_nome: 'Contato de teste', ponto_focal_email: 'teste@example.com', ponto_focal_telefone: '11999999999' })
	expect(body.edicao.uuid).to.eq(contexto.edicoes[0].uuid)
}))
Then('as alteracoes da definicao devem estar persistidas', () => {
	cy.get('@definicoesResponse', { log: false }).its('body').should('include', contexto.alteracoes)
	return requisitar('GET', detalhe()).then((res) => {
		validarStatus(res, 200)
		expect(res.body).to.include(contexto.alteracoes)
	})
})
Then('a definicao excluida nao deve ser encontrada', () => {
	cy.get('@definicoesResponse', { log: false }).its('body').should('be.empty')
	return requisitar('GET', detalhe()).then((res) => {
		validarStatus(res, 400)
		expect(res.body).to.deep.eq({ detalhe: 'Definição de Polo não encontrada.' })
	})
})
Then('o historico deve conter a participacao criada', () => cy.get('@definicoesResponse', { log: false }).its('body').then((body) => {
	expect(body.results).to.be.an('array').and.have.length(1)
	validarCampos(body.results[0], 'DefinicaoPoloHistorico')
	expect(body.results[0].uuid).to.eq(contexto.definicoes[0].uuid)
	expect(body.results[0].edicao.uuid).to.eq(contexto.edicoes[0].uuid)
}))

const verificarVinculos = (edicao, tipo) => cy.wrap(contexto.definicoes, { log: false }).each((item) => {
	return requisitar('GET', `${raiz}${item.uuid}/`).then((res) => {
		validarStatus(res, 200)
		expect(res.body.polo.uuid).to.eq(item.polo)
		expect(res.body.edicao.uuid).to.eq(edicao)
		if (tipo) expect(res.body.tipo).to.eq(tipo)
	})
})
Then('os dois vinculos em massa devem estar persistidos', () => {
	cy.get('@definicoesResponse', { log: false }).its('body').then((body) => {
		expect(body.criadas).to.be.an('array').and.have.length(2)
		expect(body.ignorados).to.deep.eq([])
		expect(body.criadas.map((item) => item.polo)).to.have.members(contexto.polos.map((polo) => polo.uuid))
		body.criadas.forEach((item) => validarCampos(item, 'DefinicaoPolo'))
	})
	return verificarVinculos(contexto.edicoes[0].uuid)
})
Then('as duas definicoes devem pertencer a edicao de destino', () => verificarVinculos(contexto.edicoes[1].uuid))
Then('os dois polos devem ter o tipo atualizado na edicao', () => {
	cy.get('@definicoesResponse', { log: false }).its('body').then((body) => {
		expect(body.alterados).to.be.an('array').and.have.length(2)
		expect(body.ignorados).to.deep.eq([])
		expect(body.alterados.map((item) => item.polo_uuid)).to.have.members(contexto.polos.map((polo) => polo.uuid))
	})
	return verificarVinculos(contexto.edicoes[0].uuid, 'reserva')
})
Then('a resposta de definicoes deve informar erros de validacao', () => cy.get('@definicoesResponse', { log: false }).its('body').should('not.be.empty'))
Then('a projecao original da definicao deve ser preservada', () => {
	cy.get('@definicoesResponse', { log: false }).its('body.detalhe').should('be.a', 'string').and('not.be.empty')
	return requisitar('GET', detalhe()).then((res) => {
		validarStatus(res, 200)
		expect(res.body.projecao_inscritos).to.eq(20)
	})
})

Then('a resposta deve indicar definicao de polo nao encontrada', () => cy.get('@definicoesResponse', { log: false }).its('body').should('deep.eq', { detalhe: 'Definição de Polo não encontrada.' }))

When('acesso definicoes com {string} em {string} com token invalido', (metodo, nome) => {
  cy.clearCookies()
  return responder(requisitar(metodo, rota(nome), { headers: { Authorization: 'Bearer token-invalido' }, ...(['POST', 'PUT', 'PATCH'].includes(metodo) ? { body: {} } : {}) }, false))
})
When('filtro as definicoes exclusivas por {string}', (filtro) => {
  const polo = contexto.polos[0]
  const filtros = { dre: { dre_codigos_eol: [polo.dre_codigo_eol] }, gestao: { gestao: polo.gestao }, tipo_polo: { tipo_polo: 'pendente' }, tipo_ue: { tipo_ue: polo.tipo_ue } }
  const qs = { edicao: contexto.edicoes[0].uuid, ...filtros[filtro] }
  if (filtro !== 'tipo_polo') return responder(requisitar('GET', raiz, { qs: { ...qs, desabilita_paginacao: true } }))

  const diagnostico = { consulta: qs, vinculos: [], paginada: null, semPaginacao: null }
  const resumir = (item) => ({ polo_uuid: item.polo_uuid, definicao_uuid: item.definicao_uuid, edicao_uuid: item.edicao_uuid, tipo: item.tipo_polo_edicao })
  const salvar = () => cy.writeFile('cypress/results/conferencia-tipo-polo.json', diagnostico, { log: false })
  return cy.wrap(contexto.definicoes, { log: false }).each((item, indice) => {
    return requisitar('GET', raiz + item.uuid + '/').then((res) => {
      validarStatus(res, 200)
      diagnostico.vinculos.push({ uuid: item.uuid, tipoEnviado: payload(indice).tipo, tipoCriado: item.tipo, tipoPreparado: item.tipoPreparado || item.tipo, tipoPersistido: res.body.tipo, polo: res.body.polo?.uuid, edicao: res.body.edicao?.uuid })
    })
  }).then(() => requisitar('GET', raiz, { qs: { ...qs, page_size: 100, desabilita_paginacao: false } })).then((res) => {
    diagnostico.paginada = { status: res.status, count: res.body.count, next: res.body.next, registros: Array.isArray(res.body.results) ? res.body.results.map(resumir) : null }
    return requisitar('GET', raiz, { qs: { ...qs, desabilita_paginacao: true } })
  }).then((res) => {
    diagnostico.semPaginacao = { status: res.status, registros: Array.isArray(res.body) ? res.body.map(resumir) : null }
    return salvar().then(() => {
      diagnostico.vinculos.forEach((item, indice) => {
        expect(item.tipoPreparado, 'Tipo preparado antes do filtro no vinculo ' + indice).to.eq(item.tipoEnviado)
        expect(item.tipoPersistido, 'Tipo persistido do vinculo ' + indice).to.eq(item.tipoEnviado)
        expect(item.polo).to.eq(contexto.polos[indice].uuid)
        expect(item.edicao).to.eq(contexto.edicoes[0].uuid)
      })
      expect(diagnostico.paginada.status, 'HTTP paginado').to.eq(200)
      expect(diagnostico.semPaginacao.status, 'HTTP sem paginacao').to.eq(200)
      expect(diagnostico.paginada.registros, 'Registros paginados').to.be.an('array')
      expect(diagnostico.semPaginacao.registros, 'Registros sem paginacao').to.be.an('array')
      expect(diagnostico.semPaginacao.registros, 'Consistencia entre as duas consultas').to.have.deep.members(diagnostico.paginada.registros)
      expect(diagnostico.paginada.count, 'Quantidade filtrada com paginacao').to.eq(1)
      expect(diagnostico.paginada.registros).to.have.length(1)
      expect(diagnostico.paginada.registros[0]).to.include({ polo_uuid: polo.uuid, edicao_uuid: qs.edicao, tipo: 'pendente' })
      return res
    })
  }).as('definicoesResponse')
})
When('consulto o historico exclusivo com limite de um registro', () => responder(requisitar('GET', raiz + 'historico/', { qs: { polo: contexto.polos[0].uuid, page: 1, page_size: 1 } })))
Then('o historico paginado deve indicar um unico registro', () => cy.get('@definicoesResponse', { log: false }).then(({ body }) => {
  expect(body.count).to.eq(1)
  expect(body.next).to.eq(null)
  expect(body.previous).to.eq(null)
}))
When('acesso definicao inexistente com {string}', (metodo) => responder(requisitar(metodo, rota('detalhe'), ['PUT', 'PATCH'].includes(metodo) ? { body: {} } : {})))
