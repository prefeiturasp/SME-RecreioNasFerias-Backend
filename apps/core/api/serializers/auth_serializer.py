"""Serializers do fluxo de autenticação do app `core`.

Concentra o contrato HTTP do login institucional mantendo o formato legado
esperado pela futura integração do projeto.
"""

from rest_framework import serializers


class LoginRequestSerializer(serializers.Serializer):
    """Valida o payload esperado pelo contrato legado de login.

    Attributes:
        login: Identificador institucional enviado pelo cliente.
        senha: Senha informada no fluxo de autenticação.
    """

    login = serializers.CharField(max_length=20)
    senha = serializers.CharField(max_length=128, trim_whitespace=False)


class LoginResponseSerializer(serializers.Serializer):
    """Representa o contrato de sucesso do login institucional.

    Attributes:
        usuarioId: Identificador do usuário autenticado no sistema.
        status: Código numérico de retorno do fluxo legado.
        nome: Nome completo do usuário autenticado.
        codigoRf: Registro funcional retornado pela autenticação.
    """

    usuarioId = serializers.CharField()  # noqa: N815
    status = serializers.IntegerField()
    nome = serializers.CharField()
    codigoRf = serializers.CharField()  # noqa: N815


class AuthMessageSerializer(serializers.Serializer):
    """Representa a resposta placeholder dos endpoints de autenticação.

    Attributes:
        detalhe: Mensagem textual devolvida pelo fluxo enquanto a
            autenticacao institucional nao estiver disponivel.
    """

    detalhe = serializers.CharField()
