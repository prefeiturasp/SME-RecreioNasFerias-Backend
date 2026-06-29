"""Testes do modelo de polos parceiros."""

from django.core.exceptions import ValidationError
from django.test import TestCase

from polos_parceiros.models import (
    PoloParceiro,
    STATUS_ATIVO,
    STATUS_INATIVO,
    TIPO_POLO_PARCEIRO,
)


class PoloParceiroModelTests(TestCase):
    """Garante regras de domínio e metadados do modelo ``PoloParceiro``."""

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

    def _criar_polo_valido(self, **sobrescrever: object) -> PoloParceiro:
        """Cria e persiste um polo parceiro válido para os cenários de teste.

        Args:
            **sobrescrever: Campos do modelo a substituir no payload base.

        Returns:
            PoloParceiro: Instância salva no banco com dados válidos.

        Raises:
            ValidationError: Se algum campo informado for inválido.
        """
        return PoloParceiro.objects.create(**self._dados_validos(**sobrescrever))

    def test_cria_polo_parceiro_com_campos_obrigatorios(self) -> None:
        """Garante criação com todos os campos obrigatórios preenchidos."""
        polo = self._criar_polo_valido()

        self.assertIsNotNone(polo.id)
        self.assertEqual(polo.tipo, TIPO_POLO_PARCEIRO)
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
            "Erro: já existe polo parceiro com o nome cadastrado",
        ):
            self._criar_polo_valido(nome_polo="polo centro")

    def test_nao_permite_quantidade_maxima_zero(self) -> None:
        """Garante bloqueio quando quantidade máxima de alunos for zero."""
        with self.assertRaisesMessage(
            ValidationError,
            "Erro: a quantidade máxima de alunos deve ser maior que zero",
        ):
            PoloParceiro.objects.create(
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
            PoloParceiro.objects.create(
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
            PoloParceiro.objects.create(
                **self._dados_validos(
                    nome_polo="Polo Sem OSC",
                    nome_osc="",
                ),
            )

    def test_permite_observacoes_gerais_vazias(self) -> None:
        """Garante que observações gerais seja opcional no cadastro."""
        polo = self._criar_polo_valido(observacoes_gerais="")

        self.assertEqual(polo.observacoes_gerais, "")

    def test_tipo_e_sempre_parceiro(self) -> None:
        """Garante que o tipo do polo seja sempre ``Parceiro``."""
        polo = self._criar_polo_valido()
        polo.tipo = "Outro"
        polo.save()

        polo.refresh_from_db()
        self.assertEqual(polo.tipo, TIPO_POLO_PARCEIRO)

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
