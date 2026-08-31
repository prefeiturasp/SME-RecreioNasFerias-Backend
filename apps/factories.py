"""Factories compartilhadas dos testes dos domínios da aplicação."""

from datetime import date

import factory

from apps.core.models import CargoPermitido, Usuario
from apps.edicoes.models import Edicao
from apps.polos.models import Polo


class CargoPermitidoFactory(factory.django.DjangoModelFactory):
    """Cria cargos permitidos para testes de autenticação e permissões."""

    class Meta:
        """Configuração da factory de cargos."""

        model = CargoPermitido

    codigo_cargo = factory.Sequence(lambda n: 9000 + n)
    descricao_cargo = factory.LazyAttribute(
        lambda cargo: f"Cargo de teste {cargo.codigo_cargo}"
    )


class UsuarioFactory(factory.django.DjangoModelFactory):
    """Cria usuários locais para autenticar chamadas da API."""

    class Meta:
        """Configuração da factory de usuários."""

        model = Usuario

    username = factory.Sequence(lambda n: f"usuario-teste-{n}")
    rf = factory.Sequence(lambda n: f"RF{n:07d}")
    nome_completo = "Usuário de Teste"
    email = factory.Sequence(lambda n: f"usuario{n}@teste.example")
    is_active = True


class EdicaoFactory(factory.django.DjangoModelFactory):
    """Cria edições planejadas com períodos válidos e isolados."""

    class Meta:
        """Configuração da factory de edições."""

        model = Edicao

    nome = factory.Sequence(lambda n: f"Edição de Teste {n}")
    data_inicio = date(2099, 1, 1)
    data_fim = date(2099, 1, 31)
    inscricoes_inicio = date(2098, 12, 1)
    inscricoes_fim = date(2099, 1, 31)


class PoloFactory(factory.django.DjangoModelFactory):
    """Cria polos válidos e isolados para os testes."""

    class Meta:
        """Configuração da factory de polos."""

        model = Polo

    codigo_eol = factory.Sequence(lambda n: f"{n + 100000:06d}")
    nome_polo = factory.Sequence(lambda n: f"Polo de Teste {n}")
    nome_osc = factory.LazyAttribute(lambda polo: f"OSC {polo.nome_polo}")
    dre_nome = "Diretoria Regional de Educação de Teste"
    dre_codigo_eol = factory.Sequence(lambda n: f"{n + 200000:06d}")
    tipo_ue = "EMEF"
    quantidade_maxima_alunos = 250
    cep = "01001000"
    tipo_logradouro = "Rua"
    logradouro = "Logradouro de Teste"
    bairro = "Bairro de Teste"
    numero = "100"
    nome_gestor = "Gestor de Teste"
    email = factory.Sequence(lambda n: f"gestor{n}@teste.example")
    telefone = "1130000000"
