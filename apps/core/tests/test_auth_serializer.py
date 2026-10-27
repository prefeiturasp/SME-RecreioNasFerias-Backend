"""Testes do contrato de resposta dos serializers de autenticação."""

from types import SimpleNamespace

from apps.core.api.serializers import MeResponseSerializer


def test_me_response_sem_cargo_retorna_lista_de_cargos_vazia() -> None:
    """Representa usuário sem cargo local com uma lista vazia de cargos."""
    usuario = SimpleNamespace(
        rf="0000001",
        username="0000001",
        nome_completo="Pessoa de Teste",
        email="",
        cpf="",
        cargo_permitido=None,
    )

    response = MeResponseSerializer.from_user(usuario)

    assert response.data == {
        "rf": "0000001",
        "nome": "Pessoa de Teste",
        "email": None,
        "cpf": None,
        "cargos": [],
        "perfis": [],
        "permissoes": [],
    }
