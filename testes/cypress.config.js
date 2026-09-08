import { defineConfig } from 'cypress'
import allureWriter from '@shelex/cypress-allure-plugin/writer.js'
import { cloudPlugin } from 'cypress-cloud/plugin'
import dotenv from 'dotenv'

import createBundler from '@bahmutov/cypress-esbuild-preprocessor'
import { addCucumberPreprocessorPlugin } from '@badeball/cypress-cucumber-preprocessor'
import { createEsbuildPlugin } from '@badeball/cypress-cucumber-preprocessor/esbuild'

dotenv.config()

export default defineConfig({
  e2e: {
    watchForFileChanges: true,
    baseUrl:
      process.env.CYPRESS_BASE_URL ||
      process.env.BASE_URL ||
      'https://qa-recreionasferias.sme.prefeitura.sp.gov.br',
    supportFile: 'cypress/support/e2e.js',

    viewportWidth: 1920,
    viewportHeight: 1080,
    video: false,
    env: {
      TAGS: 'not @ignore',
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

    retries: {
      runMode: 2,
      openMode: 0,
    },
    screenshotOnRunFailure: true,
    chromeWebSecurity: false,
    experimentalRunAllSpecs: true,
    failOnStatusCode: false,

    specPattern: 'cypress/e2e/**/*.feature',

    defaultCommandTimeout: 60000,
    requestTimeout: 60000,
    execTimeout: 60000,
    pageLoadTimeout: 60000,
    waitForAnimations: true,
    animationDistanceThreshold: 5,

    async setupNodeEvents(on, config) {
      await addCucumberPreprocessorPlugin(on, config)

      on(
        'file:preprocessor',
        createBundler({
          plugins: [createEsbuildPlugin(config)],
        })
      )

      // =====================
      // Allure
      // =====================
      allureWriter(on, config)

      // =====================
      // Cypress Cloud
      // =====================
      const enhancedConfig = await cloudPlugin(on, config)

      return enhancedConfig
    },
  },
})
