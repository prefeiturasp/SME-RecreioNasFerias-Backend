from django.test import TestCase

from application.dtos.login_output_dto import LoginOutputDto


class LoginOutputDtoTests(TestCase):
    """Testes do DTO de saida de login."""

    def test_deve_converter_para_dict(self):
        dto = LoginOutputDto(
            rf="8080640",
            cpf="22712612876",
            email="vania.montefusco@sme.prefeitura.sp.gov.br",
            cargos=[
                {
                    "codigoCargo": 2640,
                    "descricaoCargo": "ASSISTENTE TECNICO DE EDUCACAO I",
                    "codigoUnidade": "121000",
                    "descricaoUnidade": "COORDENADORIA DOS CENTROS EDUCACIONAIS UNIFICADOS - COCEU",
                    "codigoDre": "121000",
                    "contratoExterno": False,
                }
            ],
            nome="VANIA FERREIRA DA SILVA CANEKI",
            inexistente_eol=False,
        )

        self.assertEqual(
            dto.to_dict(),
            {
                "rf": "8080640",
                "cpf": "22712612876",
                "email": "vania.montefusco@sme.prefeitura.sp.gov.br",
                "cargos": [
                    {
                        "codigoCargo": 2640,
                        "descricaoCargo": "ASSISTENTE TECNICO DE EDUCACAO I",
                        "codigoUnidade": "121000",
                        "descricaoUnidade": "COORDENADORIA DOS CENTROS EDUCACIONAIS UNIFICADOS - COCEU",
                        "codigoDre": "121000",
                        "contratoExterno": False,
                    }
                ],
                "nome": "VANIA FERREIRA DA SILVA CANEKI",
                "inexistenteEol": False,
            },
        )
