import './commands_api'
import './commands_ui'
import './step_definitions/login'
import './step_definitions/logout'
import './step_definitions/me'
import './step_definitions/refresh'
import './step_definitions/verify'
import './step_definitions/edicoes'
import './step_definitions/polos'
import './step_definitions/infraestrutura_health'

Cypress.on('uncaught:exception', () => false)