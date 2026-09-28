"""Factories compartilhadas dos testes dos domínios da aplicação."""

from datetime import date

import factory

from apps.core.models import CargoPermitido, Usuario
from apps.definicoes_polos.models import DefinicaoPolo
from apps.edicoes.models import Edicao
from apps.polos.models import Polo
from apps.inscricoes.constants import GrupoInscricao, TipoEstudante
from apps.inscricoes.models import Inscricao


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


class DefinicaoPoloFactory(factory.django.DjangoModelFactory):
    """Cria participações válidas entre polos e edições."""

    class Meta:
        """Configuração da factory de definições de polos."""

        model = DefinicaoPolo

    polo = factory.SubFactory(PoloFactory)
    edicao = factory.SubFactory(EdicaoFactory)
    projecao_inscritos = 250
    ponto_focal_nome = "Ponto Focal de Teste"
    ponto_focal_telefone = "11900000000"
    ponto_focal_email = factory.Sequence(
        lambda n: f"ponto-focal{n}@teste.example"
    )


class InscricaoFactory(factory.django.DjangoModelFactory):
    """Cria inscrições básicas, inicialmente sem polo elegível."""

    class Meta:
        """Configuração da factory de inscrições."""

        model = Inscricao

    edicao = None
    polo = None
    tipo_estudante = TipoEstudante.ESTUDANTE_EXTERNO
    grupo = GrupoInscricao.QUATRO_A_14_ANOS
    codigo_eol = ""
    cpf = factory.Sequence(lambda n: f"111111111{n:02d}")
    nome_participante = factory.Sequence(lambda n: f"Participante {n}")
    data_nascimento = date(2015, 5, 19)
    responsavel_nome = "Responsável de Teste"
    responsavel_nome_social = ""
    cep = "01001000"
    tipo_logradouro = "Rua"
    logradouro = "Logradouro de Teste"
    numero = "100"
    complemento = ""
    bairro = "Bairro de Teste"
    cidade = "São Paulo"
    telefone_contato_1 = "11911111111"
    telefone_contato_2 = ""
    email = factory.Sequence(lambda n: f"responsavel{n}@teste.example")
    dre_codigo_eol = ""
    dre_nome = ""
