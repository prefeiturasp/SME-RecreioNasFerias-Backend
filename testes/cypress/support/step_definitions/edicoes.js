const { Given, When, Then } = require('@badeball/cypress-cucumber-preprocessor')
const { autenticarNaApi } = require('./login.cjs')

const obterApiBaseUrl = () => Cypress.env('api_base_url').replace(/\/$/, '')

const criarEdicaoExclusiva = (token, finalidade) => {
	return cy
		.request({
			method: 'GET',
			url: `${obterApiBaseUrl()}/api/v1/edicoes/`,
			headers: { Authorization: `Bearer ${token}` },
		})
		.then((response) => {
			const maiorDataFim = response.body.reduce((maiorData, edicao) => {
				return edicao.data_fim > maiorData ? edicao.data_fim : maiorData
			}, '2030-01-01')
			const dataInicio = new Date(`${maiorDataFim}T00:00:00Z`)
			dataInicio.setUTCDate(dataInicio.getUTCDate() + 1)
			const dataFim = new Date(dataInicio)
			dataFim.setUTCDate(dataFim.getUTCDate() + 7)
			const formatarData = (data) => data.toISOString().slice(0, 10)

			return cy
				.request({
					method: 'POST',
					url: `${obterApiBaseUrl()}/api/v1/edicoes/`,
					headers: { Authorization: `Bearer ${token}` },
					body: {
						nome: `Edicao para ${finalidade} ${Date.now()}`,
						data_inicio: formatarData(dataInicio),
						data_fim: formatarData(dataFim),
						inscricoes_inicio: formatarData(dataInicio),
						inscricoes_fim: formatarData(dataInicio),
					},
				})
				.then((criacaoResponse) => {
					expect(criacaoResponse.status, JSON.stringify(criacaoResponse.body)).to.eq(201)
					return criacaoResponse.body
				})
		})
}

const excluirEdicaoExclusiva = (token, uuid) => {
	return cy.request({
		method: 'DELETE',
		url: `${obterApiBaseUrl()}/api/v1/edicoes/${uuid}/`,
		headers: { Authorization: `Bearer ${token}` },
		failOnStatusCode: false,
	})
}

Given('que o login institucional foi realizado para consultar edicoes', () => {
	autenticarNaApi().its('body.token').should('be.a', 'string').and('not.be.empty').as('authToken')
})

When('eu consulto a lista de edicoes', () => {
	const apiBaseUrl = obterApiBaseUrl()

	cy.get('@authToken').then((token) => {
		cy.request({
			method: 'GET',
			url: `${apiBaseUrl}/api/v1/edicoes/`,
			headers: { Authorization: `Bearer ${token}` },
			failOnStatusCode: false,
		}).as('edicoesResponse')
	})
})

When('eu consulto a lista de edicoes sem token', () => {
	const apiBaseUrl = obterApiBaseUrl()

	cy.request({
		method: 'GET',
		url: `${apiBaseUrl}/api/v1/edicoes/`,
		failOnStatusCode: false,
	}).as('edicoesErrorResponse')
})

Then('a API deve responder a lista de edicoes com status 200', () => {
	cy.get('@edicoesResponse').its('status').should('eq', 200)
})

Then('a resposta deve conter uma lista de edicoes', () => {
	cy.get('@edicoesResponse').its('body').should('be.an', 'array')
})

Then('cada edicao deve possuir os campos principais', () => {
	cy.get('@edicoesResponse')
		.its('body')
		.then((edicoes) => {
			edicoes.forEach((edicao) => {
				expect(edicao).to.have.all.keys('uuid', 'nome', 'data_inicio', 'data_fim', 'inscricoes_inicio', 'inscricoes_fim', 'quantidade_inscritos', 'quantidade_atendimento_efetivo', 'quantidade_passeios', 'quantidade_apresentacoes', 'status', 'ativo', 'criado_em', 'atualizado_em')
			})
		})
})

Then('a API deve responder a lista de edicoes com status 401', () => {
	cy.get('@edicoesErrorResponse').its('status').should('eq', 401)
})

Given('que o login institucional foi realizado para consultar uma edicao', () => {
	autenticarNaApi().its('body.token').should('be.a', 'string').and('not.be.empty').as('authToken')
})

Given('existe uma edicao cadastrada', () => {
	cy.get('@authToken').then((token) => {
		cy.request({
			method: 'GET',
			url: `${obterApiBaseUrl()}/api/v1/edicoes/`,
			headers: { Authorization: `Bearer ${token}` },
		}).then((response) => {
			expect(response.body).to.be.an('array').and.not.be.empty
			cy.wrap(response.body[0].uuid).as('edicaoUuid')
		})
	})
})

When('eu consulto a edicao pelo UUID', () => {
	cy.get('@authToken').then((token) => {
		cy.get('@edicaoUuid').then((uuid) => {
			cy.request({
				method: 'GET',
				url: `${obterApiBaseUrl()}/api/v1/edicoes/${uuid}/`,
				headers: { Authorization: `Bearer ${token}` },
				failOnStatusCode: false,
			}).as('edicaoResponse')
		})
	})
})

When('eu consulto uma edicao pelo UUID sem token', () => {
	cy.request({
		method: 'GET',
		url: `${obterApiBaseUrl()}/api/v1/edicoes/00000000-0000-0000-0000-000000000000/`,
		failOnStatusCode: false,
	}).as('edicaoErrorResponse')
})

Then('a API deve responder ao detalhe da edicao com status 200', () => {
	cy.get('@edicaoResponse').its('status').should('eq', 200)
})

Then('a resposta deve conter os dados principais da edicao', () => {
	cy.get('@edicaoResponse').its('body').should('include.all.keys', ['uuid', 'nome', 'data_inicio', 'data_fim', 'inscricoes_inicio', 'inscricoes_fim', 'status', 'ativo'])
})

Then('a API deve responder ao detalhe da edicao com status 401', () => {
	cy.get('@edicaoErrorResponse').its('status').should('eq', 401)
})

Given('que o login institucional foi realizado para criar edicao', () => {
	autenticarNaApi().its('body.token').should('be.a', 'string').and('not.be.empty').as('authToken')
})

When('eu envio os dados de uma nova edicao', () => {
	cy.get('@authToken').then((token) => {
		cy.request({
			method: 'GET',
			url: `${obterApiBaseUrl()}/api/v1/edicoes/`,
			headers: { Authorization: `Bearer ${token}` },
		}).then((response) => {
			const datasConfiguradas = [Cypress.env('edicao_data_inicio'), Cypress.env('edicao_data_fim'), Cypress.env('edicao_inscricoes_inicio'), Cypress.env('edicao_inscricoes_fim')].filter(Boolean)
			const maiorDataFim = response.body.reduce((maiorData, edicao) => {
				return edicao.data_fim > maiorData ? edicao.data_fim : maiorData
			}, '2030-01-01')
			const dataBase = new Date(`${maiorDataFim}T00:00:00Z`)
			dataBase.setUTCDate(dataBase.getUTCDate() + 1)
			const dataInicio = datasConfiguradas[0] || dataBase.toISOString().slice(0, 10)
			const dataFim =
				datasConfiguradas[1] ||
				(() => {
					const data = new Date(`${dataInicio}T00:00:00Z`)
					data.setUTCDate(data.getUTCDate() + 30)
					return data.toISOString().slice(0, 10)
				})()
			const inscricoesInicio =
				datasConfiguradas[2] ||
				(() => {
					const data = new Date(`${dataInicio}T00:00:00Z`)
					data.setUTCDate(data.getUTCDate() - 14)
					return data.toISOString().slice(0, 10)
				})()
			const inscricoesFim =
				datasConfiguradas[3] ||
				(() => {
					const data = new Date(`${dataInicio}T00:00:00Z`)
					data.setUTCDate(data.getUTCDate() - 1)
					return data.toISOString().slice(0, 10)
				})()
			const payload = {
				nome: `Edicao automatizada ${Date.now()}`,
				data_inicio: dataInicio,
				data_fim: dataFim,
				inscricoes_inicio: inscricoesInicio,
				inscricoes_fim: inscricoesFim,
			}

			cy.request({
				method: 'POST',
				url: `${obterApiBaseUrl()}/api/v1/edicoes/`,
				headers: { Authorization: `Bearer ${token}` },
				body: payload,
				failOnStatusCode: false,
			}).as('criacaoEdicaoResponse')
		})
	})
})

When('eu envio um payload invalido para criar edicao', () => {
	cy.get('@authToken').then((token) => {
		cy.request({
			method: 'POST',
			url: `${obterApiBaseUrl()}/api/v1/edicoes/`,
			headers: { Authorization: `Bearer ${token}` },
			body: {},
			failOnStatusCode: false,
		}).as('criacaoEdicaoErrorResponse')
	})
})

Then('a API deve responder a criacao de edicao com status 201', () => {
	cy.get('@criacaoEdicaoResponse').then((response) => {
		expect(response.status, JSON.stringify(response.body)).to.eq(201)
	})
})

Then('a resposta deve conter os dados da edicao criada', () => {
	cy.get('@criacaoEdicaoResponse').its('body').should('include.all.keys', ['uuid', 'nome', 'data_inicio', 'data_fim', 'inscricoes_inicio', 'inscricoes_fim', 'status', 'ativo'])
})

Then('a API deve responder a criacao de edicao com status 400', () => {
	cy.get('@criacaoEdicaoErrorResponse').its('status').should('eq', 400)
})

Given('que o login institucional foi realizado para atualizar edicao', () => {
	autenticarNaApi().its('body.token').should('be.a', 'string').and('not.be.empty').as('authToken')
})

Given('existe uma edicao para atualizar', () => {
	cy.get('@authToken').then((token) => {
		criarEdicaoExclusiva(token, 'atualizacao completa').as('edicaoAtual')
	})
})

When('eu atualizo os dados da edicao', () => {
	cy.get('@authToken').then((token) => {
		cy.get('@edicaoAtual').then((edicao) => {
			cy.request({
				method: 'PUT',
				url: `${obterApiBaseUrl()}/api/v1/edicoes/${edicao.uuid}/`,
				headers: { Authorization: `Bearer ${token}` },
				body: {
					nome: `${edicao.nome} - atualizado ${Date.now()}`,
					data_inicio: edicao.data_inicio,
					data_fim: edicao.data_fim,
					inscricoes_inicio: edicao.inscricoes_inicio,
					inscricoes_fim: edicao.inscricoes_fim,
				},
				failOnStatusCode: false,
			}).as('atualizacaoEdicaoResponse')
		})
	})
})

When('eu envio um payload invalido para atualizar edicao', () => {
	cy.get('@authToken').then((token) => {
		cy.get('@edicaoAtual').then((edicao) => {
			cy.request({
				method: 'PUT',
				url: `${obterApiBaseUrl()}/api/v1/edicoes/${edicao.uuid}/`,
				headers: { Authorization: `Bearer ${token}` },
				body: {},
				failOnStatusCode: false,
			}).as('atualizacaoEdicaoErrorResponse')
		})
	})
})

Then('a API deve responder a atualizacao de edicao com status 200', () => {
	cy.get('@atualizacaoEdicaoResponse').then((response) => {
		expect(response.status, JSON.stringify(response.body)).to.eq(200)
	})
})

Then('a resposta deve conter os dados atualizados da edicao', () => {
	cy.get('@atualizacaoEdicaoResponse').its('body').should('include.all.keys', ['uuid', 'nome', 'data_inicio', 'data_fim', 'inscricoes_inicio', 'inscricoes_fim', 'status', 'ativo'])
	cy.get('@authToken').then((token) => {
		cy.get('@edicaoAtual').then((edicao) => {
			excluirEdicaoExclusiva(token, edicao.uuid).its('status').should('eq', 204)
		})
	})
})

Then('a API deve responder a atualizacao de edicao com status 400', () => {
	cy.get('@atualizacaoEdicaoErrorResponse').its('status').should('eq', 400)
	cy.get('@authToken').then((token) => {
		cy.get('@edicaoAtual').then((edicao) => {
			excluirEdicaoExclusiva(token, edicao.uuid).its('status').should('eq', 204)
		})
	})
})

Given('que o login institucional foi realizado para atualizar edicao parcialmente', () => {
	autenticarNaApi().its('body.token').should('be.a', 'string').and('not.be.empty').as('authToken')
})

Given('existe uma edicao para atualizar parcialmente', () => {
	cy.get('@authToken').then((token) => {
		criarEdicaoExclusiva(token, 'atualizacao parcial').as('edicaoParcial')
	})
})

When('eu atualizo parcialmente os dados da edicao', () => {
	cy.get('@authToken').then((token) => {
		cy.get('@edicaoParcial').then((edicao) => {
			cy.request({
				method: 'PATCH',
				url: `${obterApiBaseUrl()}/api/v1/edicoes/${edicao.uuid}/`,
				headers: { Authorization: `Bearer ${token}` },
				body: { nome: `${edicao.nome} - parcial ${Date.now()}` },
				failOnStatusCode: false,
			}).as('atualizacaoParcialResponse')
		})
	})
})

When('eu envio um payload invalido para atualizar edicao parcialmente', () => {
	cy.get('@authToken').then((token) => {
		cy.get('@edicaoParcial').then((edicao) => {
			cy.request({
				method: 'PATCH',
				url: `${obterApiBaseUrl()}/api/v1/edicoes/${edicao.uuid}/`,
				headers: { Authorization: `Bearer ${token}` },
				body: { nome: '' },
				failOnStatusCode: false,
			}).as('atualizacaoParcialErrorResponse')
		})
	})
})

Then('a API deve responder a atualizacao parcial com status 200', () => {
	cy.get('@atualizacaoParcialResponse').then((response) => {
		expect(response.status, JSON.stringify(response.body)).to.eq(200)
	})
})

Then('a resposta deve conter os dados da edicao atualizada parcialmente', () => {
	cy.get('@atualizacaoParcialResponse').its('body').should('include.all.keys', ['uuid', 'nome', 'data_inicio', 'data_fim', 'inscricoes_inicio', 'inscricoes_fim', 'status', 'ativo'])
	cy.get('@authToken').then((token) => {
		cy.get('@edicaoParcial').then((edicao) => {
			excluirEdicaoExclusiva(token, edicao.uuid).its('status').should('eq', 204)
		})
	})
})

Then('a API deve responder a atualizacao parcial com status 400', () => {
	cy.get('@atualizacaoParcialErrorResponse').its('status').should('eq', 400)
	cy.get('@authToken').then((token) => {
		cy.get('@edicaoParcial').then((edicao) => {
			excluirEdicaoExclusiva(token, edicao.uuid).its('status').should('eq', 204)
		})
	})
})

Given('que o login institucional foi realizado para excluir edicao', () => {
	autenticarNaApi().its('body.token').should('be.a', 'string').and('not.be.empty').as('authToken')
})

Given('uma edicao exclusiva foi criada para exclusao', () => {
	cy.get('@authToken').then((token) => {
		cy.request({
			method: 'GET',
			url: `${obterApiBaseUrl()}/api/v1/edicoes/`,
			headers: { Authorization: `Bearer ${token}` },
		}).then((response) => {
			const maiorDataFim = response.body.reduce((maiorData, edicao) => {
				return edicao.data_fim > maiorData ? edicao.data_fim : maiorData
			}, '2030-01-01')
			const dataInicio = new Date(`${maiorDataFim}T00:00:00Z`)
			dataInicio.setUTCDate(dataInicio.getUTCDate() + 1)
			const dataFim = new Date(dataInicio)
			dataFim.setUTCDate(dataFim.getUTCDate() + 7)
			const formatarData = (data) => data.toISOString().slice(0, 10)
			const payload = {
				nome: `Edicao para exclusao ${Date.now()}`,
				data_inicio: formatarData(dataInicio),
				data_fim: formatarData(dataFim),
				inscricoes_inicio: formatarData(dataInicio),
				inscricoes_fim: formatarData(dataInicio),
			}

			cy.request({
				method: 'POST',
				url: `${obterApiBaseUrl()}/api/v1/edicoes/`,
				headers: { Authorization: `Bearer ${token}` },
				body: payload,
			})
				.its('body.uuid')
				.as('edicaoExclusaoUuid')
		})
	})
})

When('eu excluo a edicao pelo UUID', () => {
	cy.get('@authToken').then((token) => {
		cy.get('@edicaoExclusaoUuid').then((uuid) => {
			cy.request({
				method: 'DELETE',
				url: `${obterApiBaseUrl()}/api/v1/edicoes/${uuid}/`,
				headers: { Authorization: `Bearer ${token}` },
				failOnStatusCode: false,
			}).as('exclusaoEdicaoResponse')
		})
	})
})

Then('a API deve responder a exclusao de edicao com status 204', () => {
	cy.get('@exclusaoEdicaoResponse').its('status').should('eq', 204)
	cy.get('@exclusaoEdicaoResponse').its('body').should('be.empty')
})
