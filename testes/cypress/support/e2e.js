require('@shelex/cypress-allure-plugin')
import './commands_api'
import './commands_ui'

Cypress.on('uncaught:exception', () => false)