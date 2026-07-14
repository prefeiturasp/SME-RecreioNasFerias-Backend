"""Testes do modelo de polos parceiros."""

from django.core.exceptions import ValidationError
from django.test import TestCase

from polos.models import (
    GESTAO_DIRETA,
    GESTAO_PARCEIRA,
    Polo,
    STATUS_ATIVO,
    STATUS_INATIVO,
    TIPO_POLO_OFICIAL,
    TIPO_POLO_PENDENTE,
)


class PoloModelTests(TestCase):
    """Garante regras de domínio e metadados do modelo ``Polo``."""

    def _dados_validos(self, **sobrescrever: object) -> dict[str, object]:
        """Montar payload válido para criação de polo parceiro nos testes.

        Args:
            **sobrescrever: Campos do modelo a substituir no payload base.

        Returns:
            dict[str, object]: Dicionário pronto para ``objects.create``.
        """
        dados: dict[str, object] = {
            "nome_osc": "OSC Parceira Exemplo",
            "nome_polo": "Polo Centro",
            "dre": "DRE Butantã",
            "tipo_ue": "EMEF",
            "quantidade_maxima_alunos": 50,
            "cep": "05508-000",
            "endereco": "Rua Exemplo, 100",
            "nome_gestor": "Maria Silva",
            "email_polo": "polo@osc.org.br",
            "telefone_polo": "(11) 99999-9999",
        }
        dados.update(sobrescrever)
        return dados

    def _criar_polo_valido(self, **sobrescrever: object) -> Polo:
        """Cria e persiste um polo parceiro válido para os cenários de teste.

        Args:
            **sobrescrever: Campos do modelo a substituir no payload base.

        Returns:
            Polo: Instância salva no banco com dados válidos.

        Raises:
            ValidationError: Se algum campo informado for inválido.
        """
        return Polo.objects.create(**self._dados_validos(**sobrescrever))

    def test_cria_polo_com_campos_obrigatorios(self) -> None:
        """Garante criação com todos os campos obrigatórios preenchidos."""
        polo = self._criar_polo_valido()

        self.assertIsNotNone(polo.id)
        self.assertEqual(polo.tipo, TIPO_POLO_PENDENTE)
        self.assertEqual(polo.gestao, GESTAO_PARCEIRA)
        self.assertEqual(polo.nome_polo, "Polo Centro")
        self.assertEqual(polo.status, STATUS_ATIVO)

    def test_str_retorna_nome_do_polo(self) -> None:
        """Garante representação textual amigável do modelo."""
        polo = self._criar_polo_valido()

        self.assertEqual(str(polo), "Polo Centro")

    def test_nao_permite_nome_polo_repetido(self) -> None:
        """Garante bloqueio de cadastro com nome de polo já existente."""
        self._criar_polo_valido()

        with self.assertRaisesMessage(
            ValidationError,
            "Erro: já existe polo com o nome cadastrado",
        ):
            self._criar_polo_valido(nome_polo="polo centro")

    def test_nao_permite_quantidade_maxima_zero(self) -> None:
        """Garante bloqueio quando quantidade máxima de alunos for zero."""
        with self.assertRaisesMessage(
            ValidationError,
            "Erro: a quantidade máxima de alunos deve ser maior que zero",
        ):
            Polo.objects.create(
                **self._dados_validos(
                    nome_polo="Polo Quantidade Zero",
                    quantidade_maxima_alunos=0,
                ),
            )

    def test_nao_permite_email_invalido(self) -> None:
        """Garante bloqueio quando o e-mail do polo for inválido."""
        with self.assertRaisesMessage(
            ValidationError,
            "Erro: informe um e-mail válido para o polo",
        ):
            Polo.objects.create(
                **self._dados_validos(
                    nome_polo="Polo Email Inválido",
                    email_polo="email-invalido",
                ),
            )

    def test_nao_permite_campo_obrigatorio_vazio(self) -> None:
        """Garante bloqueio quando um campo obrigatório estiver vazio."""
        with self.assertRaisesMessage(
            ValidationError,
            "Erro: o campo nome da OSC é obrigatório",
        ):
            Polo.objects.create(
                **self._dados_validos(
                    nome_polo="Polo Sem OSC",
                    nome_osc="",
                ),
            )

    def test_permite_observacoes_gerais_vazias(self) -> None:
        """Garante que observações gerais seja opcional no cadastro."""
        polo = self._criar_polo_valido(observacoes_gerais="")

        self.assertEqual(polo.observacoes_gerais, "")

    def test_tipo_padrao_e_pendente(self) -> None:
        """Garante que novos polos sejam persistidos com tipo Pendente."""
        polo = self._criar_polo_valido()

        self.assertEqual(polo.tipo, TIPO_POLO_PENDENTE)

    def test_permite_alterar_tipo_para_opcoes_validas(self) -> None:
        """Garante persistência das opções oficiais de tipo de polo."""
        polo = self._criar_polo_valido()
        polo.tipo = TIPO_POLO_OFICIAL
        polo.save()

        polo.refresh_from_db()
        self.assertEqual(polo.tipo, TIPO_POLO_OFICIAL)

    def test_nao_permite_tipo_invalido(self) -> None:
        """Garante bloqueio de tipo fora das opções permitidas."""
        polo = self._criar_polo_valido()
        polo.tipo = "Sede"

        with self.assertRaisesMessage(
            ValidationError,
            "Erro: o tipo deve ser Pendente, Polo oficial ou Polo reserva",
        ):
            polo.save()

    def test_status_padrao_e_ativo_na_criacao(self) -> None:
        """Garante que novos polos sejam persistidos com status ativo."""
        polo = self._criar_polo_valido(nome_polo="Polo Status Padrão")

        self.assertEqual(polo.status, STATUS_ATIVO)

    def test_nao_permite_status_invalido_na_atualizacao(self) -> None:
        """Garante bloqueio de persistência com status fora dos valores permitidos."""
        polo = self._criar_polo_valido(nome_polo="Polo Status Inválido")
        polo.status = "suspenso"

        with self.assertRaisesMessage(
            ValidationError,
            "Erro: o status deve ser ativo ou inativo",
        ):
            polo.save()

    def test_permite_alternar_status_entre_ativo_e_inativo(self) -> None:
        """Garante alternância válida do status em polos existentes."""
        polo = self._criar_polo_valido(nome_polo="Polo Alternância Status")
        polo.status = STATUS_INATIVO
        polo.save()

        polo.refresh_from_db()
        self.assertEqual(polo.status, STATUS_INATIVO)

        polo.status = STATUS_ATIVO
        polo.save()

        polo.refresh_from_db()
        self.assertEqual(polo.status, STATUS_ATIVO)

    def test_gestao_padrao_e_parceira_na_criacao(self) -> None:
        """Garante que novos polos manuais sejam persistidos com gestão Parceira."""
        polo = self._criar_polo_valido(nome_polo="Polo Gestão Padrão")

        self.assertEqual(polo.gestao, GESTAO_PARCEIRA)

    def test_permite_gestao_direta(self) -> None:
        """Garante persistência de polos com gestão Direta (integração)."""
        polo = self._criar_polo_valido(
            nome_polo="Polo Gestão Direta",
            gestao=GESTAO_DIRETA,
            codigo_eol="019999",
        )

        self.assertEqual(polo.gestao, GESTAO_DIRETA)
        self.assertEqual(polo.codigo_eol, "019999")
        self.assertEqual(polo.tipo, TIPO_POLO_PENDENTE)

    def test_direta_exige_codigo_eol(self) -> None:
        """Garante bloqueio de gestão Direta sem código EOL."""
        with self.assertRaisesMessage(
            ValidationError,
            "Erro: o código EOL é obrigatório para polos de gestão Direta",
        ):
            Polo.objects.create(
                **self._dados_validos(
                    nome_polo="Polo Direta Sem EOL",
                    gestao=GESTAO_DIRETA,
                    codigo_eol="",
                ),
            )

    def test_parceira_exige_campos_complementares(self) -> None:
        """Garante obrigatoriedade dos campos específicos de gestão Parceira."""
        with self.assertRaisesMessage(
            ValidationError,
            "Erro: o campo CEP é obrigatório",
        ):
            Polo.objects.create(
                **self._dados_validos(
                    nome_polo="Polo Parceira Sem CEP",
                    cep="",
                ),
            )

    def test_nao_permite_gestao_invalida(self) -> None:
        """Garante bloqueio de persistência com gestão fora dos valores permitidos."""
        with self.assertRaisesMessage(
            ValidationError,
            "Erro: a gestão deve ser Parceira ou Direta",
        ):
            Polo.objects.create(
                **self._dados_validos(
                    nome_polo="Polo Gestão Inválida",
                    gestao="Indireta",
                ),
            )
