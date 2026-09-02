const { defineConfig } = require('cypress')
require('dotenv').config()

module.exports = defineConfig({
	e2e: {
		setupNodeEvents(on, config) {
			require('./cypress/plugin/index.js')(on, config)
			return config
		},
		baseUrl:
			process.env.CYPRESS_BASE_URL ||
			process.env.BASE_URL ||
			'https://qa-recreionasferias.sme.prefeitura.sp.gov.br',
		env: {
			api_base_url:
				process.env.API_BASE_URL ||
				process.env.VITE_SME_CDEP_API ||
				process.env.BASE_URL ||
				'https://qa-recreionasferias.sme.prefeitura.sp.gov.br',
			api_usuario: process.env.API_USUARIO,
			api_senha: process.env.API_SENHA,
			edicao_data_inicio: process.env.EDICAO_DATA_INICIO,
			edicao_data_fim: process.env.EDICAO_DATA_FIM,
			edicao_inscricoes_inicio: process.env.EDICAO_INSCRICOES_INICIO,
			edicao_inscricoes_fim: process.env.EDICAO_INSCRICOES_FIM,
		},
		video: false,
		timeout: 60000,
		retries: 0,
		screenshotOnRunFailure: true,
		chromeWebSecurity: false,
		specPattern: 'cypress/e2e/**/*.{feature,cy.{js,jsx,ts,tsx}}',
	},
})