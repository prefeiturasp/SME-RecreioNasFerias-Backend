"""Testes unitarios do adaptador EOL."""

from __future__ import annotations

from typing import Any

from apps.integracoes.eol.adapter import EolAdapter
from apps.integracoes.eol.constants import CODIGO_CARGO_DIRETOR_ESCOLA
from apps.integracoes.eol.exceptions import EolIndisponivelError
from apps.integracoes.eol.port import (
    AlunoEol,
    DadosUnidadeEol,
    DreEol,
    InformacoesAlunoEol,
    ParticipanteRedeEol,
    TipoEscolaEol,
    UnidadeEol,
    UnidadeRecreioEol,
)


class FakeClient:
    """Client fake que simula os endpoints de escolas e de alunos."""

    def __init__(
        self,
        *,
        unidades: list[dict[str, Any]] | None = None,
        tipos_escola: list[dict[str, Any]] | None = None,
        dres: list[dict[str, Any]] | None = None,
        dados: dict[str, dict[str, Any]] | None = None,
        diretores: dict[str, str] | None = None,
        falhas_dados: set[str] | None = None,
        falhas_diretores: set[str] | None = None,
        alunos: list[dict[str, Any]] | None = None,
        informacoes: dict[str, Any] | None = None,
    ) -> None:
        """Inicializa o fake com os payloads que serão devolvidos."""
        self.unidades = unidades or []
        self.tipos_escola = tipos_escola or []
        self.dres = dres or []
        self.dados = dados or {}
        self.diretores = diretores or {}
        self.falhas_dados = falhas_dados or set()
        self.falhas_diretores = falhas_diretores or set()
        self.alunos = alunos or []
        self.informacoes = informacoes
        self.calls_obter_dados: list[str] = []
        self.calls_obter_diretor: list[tuple[str, int]] = []
        self.calls_informacoes: list[str] = []

    def listar_todas_unidades(self) -> list[dict[str, Any]]:
        """Devolve o catalogo bruto configurado."""
        return self.unidades

    def listar_tipos_escola(self) -> list[dict[str, Any]]:
        """Devolve os tipos de escola configurados."""
        return self.tipos_escola

    def listar_dres(self) -> list[dict[str, Any]]:
        """Devolve as DREs configuradas."""
        return self.dres

    def obter_dados_unidade(self, codigo_eol: str) -> dict[str, Any] | None:
        """Devolve os dados brutos ou simula indisponibilidade pontual."""
        self.calls_obter_dados.append(codigo_eol)
        if codigo_eol in self.falhas_dados:
            raise EolIndisponivelError()
        return self.dados.get(codigo_eol)

    def obter_funcionarios_por_cargo(
        self,
        codigo_eol: str,
        codigo_cargo: int,
    ) -> list[dict[str, Any]]:
        """Devolve o diretor configurado para a unidade."""
        self.calls_obter_diretor.append((codigo_eol, codigo_cargo))
        if codigo_eol in self.falhas_diretores:
            raise EolIndisponivelError()
        nome = self.diretores.get(codigo_eol)
        if not nome:
            return []
        return [{"nomeServidor": nome}]

    def listar_alunos(self, codigo_eol: str) -> list[dict[str, Any]]:
        """Devolve a lista bruta de alunos configurada."""
        return self.alunos

    def obter_informacoes_aluno(
        self,
        codigo_aluno: str,
    ) -> dict[str, Any] | None:
        """Devolve a ficha bruta ou ``None`` quando ausente."""
        self.calls_informacoes.append(codigo_aluno)
        return self.informacoes


def _unidade_bruta(codigo: str, sigla: str) -> dict[str, Any]:
    """Monta um item de catalogo bruto para os testes."""
    return {
        "codigoEscola": codigo,
        "nomeEscola": f"Unidade {codigo}",
        "siglaTipoEscola": sigla,
        "nomeDRE": "DRE Ipiranga",
        "siglaDRE": "IP",
        "codigoDRE": "10",
    }


def test_listar_tipos_escola_normaliza_catalogo() -> None:
    """Converte o catálogo bruto de tipos no contrato tipado."""
    client = FakeClient(
        tipos_escola=[
            {"codigo": "1", "descricaoSigla": " EMEF "},
            {"codigo": 2, "descricaoSigla": "EMEI"},
        ]
    )

    tipos = EolAdapter(client=client).listar_tipos_escola()

    assert tipos == (
        TipoEscolaEol(codigo=1, descricao_sigla="EMEF"),
        TipoEscolaEol(codigo=2, descricao_sigla="EMEI"),
    )


def test_listar_dres_normaliza_catalogo() -> None:
    """Converte o catálogo bruto de DREs no contrato tipado."""
    client = FakeClient(
        dres=[
            {
                "codigoDRE": "108100",
                "nomeDRE": " DRE Butantã ",
                "siglaDRE": "DRE - BT",
            }
        ]
    )

    dres = EolAdapter(client=client).listar_dres()

    assert dres == (
        DreEol(
            codigo_dre="108100",
            nome_dre="DRE Butantã",
            sigla_dre="DRE - BT",
        ),
    )


def test_listar_todas_unidades_normaliza_catalogo() -> None:
    """Converte o catalogo bruto em contratos tipados."""
    client = FakeClient(
        unidades=[
            _unidade_bruta("094633", "EMEF"),
            _unidade_bruta("121000", "CEI DIRET"),
        ]
    )

    unidades = EolAdapter(client=client).listar_todas_unidades()

    assert unidades == (
        UnidadeEol(
            codigo_eol="094633",
            nome_escola="Unidade 094633",
            sigla_tipo_escola="EMEF",
            nome_dre="DRE Ipiranga",
            sigla_dre="IP",
            codigo_dre="10",
        ),
        UnidadeEol(
            codigo_eol="121000",
            nome_escola="Unidade 121000",
            sigla_tipo_escola="CEI DIRET",
            nome_dre="DRE Ipiranga",
            sigla_dre="IP",
            codigo_dre="10",
        ),
    )


def test_obter_dados_unidade_normaliza_payload() -> None:
    """Normaliza dados detalhados com CEP e endereço em campos separados."""
    client = FakeClient(
        dados={
            "094633": {
                "nome": "EMEF Professora Teste",
                "codigo": "094633",
                "siglaTipoEscola": "EMEF",
                "nomeDRE": "DRE Ipiranga",
                "siglaDRE": "IP",
                "codigoDRE": "10",
                "email": "emef@exemplo.gov.br",
                "telefone": "1122334455",
                "cep": "04206000",
                "tipoLogradouro": "Rua",
                "logradouro": "das Flores",
                "numero": "123",
                "bairro": "Ipiranga",
                "complemento": "Bloco B",
                "municipio": "São Paulo",
                "uf": "SP",
            }
        }
    )

    dados = EolAdapter(client=client).obter_dados_unidade("094633")

    assert dados == DadosUnidadeEol(
        nome="EMEF Professora Teste",
        codigo_eol="094633",
        sigla_tipo_escola="EMEF",
        nome_dre="DRE Ipiranga",
        sigla_dre="IP",
        codigo_dre="10",
        email="emef@exemplo.gov.br",
        telefone="1122334455",
        cep="04206-000",
        tipo_logradouro="Rua",
        logradouro="das Flores",
        bairro="Ipiranga",
        numero="123",
        complemento="Bloco B",
        municipio="São Paulo",
        uf="SP",
    )


def test_obter_dados_unidade_retorna_none_para_ausente() -> None:
    """Devolve ``None`` quando a unidade não possui dados detalhados."""
    client = FakeClient()

    dados = EolAdapter(client=client).obter_dados_unidade("094633")

    assert dados is None


def test_obter_nome_diretor_usa_cargo_padrao() -> None:
    """Consulta o diretor usando o código de cargo padrão."""
    client = FakeClient(diretores={"094633": "Diretor Teste"})

    nome = EolAdapter(client=client).obter_nome_diretor("094633")

    assert nome == "Diretor Teste"
    assert client.calls_obter_diretor == [
        ("094633", CODIGO_CARGO_DIRETOR_ESCOLA)
    ]


def test_obter_nome_diretor_com_cargo_personalizado() -> None:
    """Consulta o diretor usando um código de cargo informado."""
    client = FakeClient(diretores={"094633": "Diretor Teste"})

    nome = EolAdapter(client=client).obter_nome_diretor("094633", 9999)

    assert nome == "Diretor Teste"
    assert client.calls_obter_diretor == [("094633", 9999)]


def test_obter_nome_diretor_retorna_vazio_sem_funcionario() -> None:
    """Devolve string vazia quando a unidade não possui diretor."""
    client = FakeClient()

    nome = EolAdapter(client=client).obter_nome_diretor("094633")

    assert nome == ""


def test_filtrar_unidades_recreio_por_sigla() -> None:
    """Mantém apenas as unidades com tipo de UE elegível."""
    unidades = (
        UnidadeEol(
            codigo_eol="1",
            nome_escola="EMEF",
            sigla_tipo_escola="EMEF",
            nome_dre="DRE",
            sigla_dre="DR",
            codigo_dre="1",
        ),
        UnidadeEol(
            codigo_eol="2",
            nome_escola="Outro",
            sigla_tipo_escola="OUTRO",
            nome_dre="DRE",
            sigla_dre="DR",
            codigo_dre="1",
        ),
        UnidadeEol(
            codigo_eol="3",
            nome_escola="CEI DIRET",
            sigla_tipo_escola="CEI DIRET",
            nome_dre="DRE",
            sigla_dre="DR",
            codigo_dre="1",
        ),
    )

    filtradas = EolAdapter(client=FakeClient()).filtrar_unidades_recreio(
        unidades
    )

    assert [u.codigo_eol for u in filtradas] == ["1", "3"]


def test_enriquecer_unidades_agrega_dados_e_diretor() -> None:
    """Enriquece unidades com dados detalhados e nome do diretor."""
    client = FakeClient(
        dados={
            "094633": {
                "nome": "EMEF Professora Teste",
                "email": "emef@exemplo.gov.br",
                "telefone": "1122334455",
                "cep": "04206000",
                "tipoLogradouro": "Rua",
                "logradouro": "das Flores",
                "numero": "123",
                "bairro": "Ipiranga",
            }
        },
        diretores={"094633": "Diretor Teste"},
    )
    unidades = (
        UnidadeEol(
            codigo_eol="094633",
            nome_escola="Unidade 094633",
            sigla_tipo_escola="EMEF",
            nome_dre="DRE Ipiranga",
            sigla_dre="IP",
            codigo_dre="10",
        ),
    )

    enriquecidas = EolAdapter(client=client).enriquecer_unidades(unidades)

    assert enriquecidas == (
        UnidadeRecreioEol(
            codigo_eol="094633",
            nome_escola="EMEF Professora Teste",
            sigla_tipo_escola="EMEF",
            nome_dre="DRE Ipiranga",
            sigla_dre="IP",
            codigo_dre="10",
            email="emef@exemplo.gov.br",
            telefone="1122334455",
            cep="04206-000",
            tipo_logradouro="Rua",
            logradouro="das Flores",
            bairro="Ipiranga",
            numero="123",
            complemento="",
            nome_diretor="Diretor Teste",
        ),
    )


def test_enriquecer_unidades_tolera_falha_parcial() -> None:
    """Mantém os dados básicos quando o enriquecimento falha pontualmente."""
    client = FakeClient(
        dados={"094633": {"nome": "EMEF Teste"}},
        diretores={"094633": "Diretor Teste"},
        falhas_dados={"121000"},
    )
    unidades = (
        UnidadeEol(
            codigo_eol="094633",
            nome_escola="Unidade 094633",
            sigla_tipo_escola="EMEF",
            nome_dre="DRE Ipiranga",
            sigla_dre="IP",
            codigo_dre="10",
        ),
        UnidadeEol(
            codigo_eol="121000",
            nome_escola="Unidade 121000",
            sigla_tipo_escola="CEI DIRET",
            nome_dre="DRE Ipiranga",
            sigla_dre="IP",
            codigo_dre="10",
        ),
    )

    enriquecidas = EolAdapter(client=client).enriquecer_unidades(unidades)

    por_eol = {u.codigo_eol: u for u in enriquecidas}
    assert por_eol["094633"].nome_escola == "EMEF Teste"
    assert por_eol["094633"].nome_diretor == "Diretor Teste"
    assert por_eol["121000"].nome_escola == "Unidade 121000"
    assert por_eol["121000"].nome_diretor == ""


def test_enriquecer_unidade_tolera_falha_na_consulta_do_diretor() -> None:
    """Mantém dados da unidade quando a consulta do diretor falha."""
    client = FakeClient(
        dados={"094633": {"nome": "EMEF Teste"}},
        falhas_diretores={"094633"},
    )
    unidade = UnidadeEol(
        codigo_eol="094633",
        nome_escola="Unidade 094633",
        sigla_tipo_escola="EMEF",
        nome_dre="DRE",
        sigla_dre="DR",
        codigo_dre="1",
    )

    enriquecida = EolAdapter(client=client).enriquecer_unidades((unidade,))

    assert enriquecida[0].nome_escola == "EMEF Teste"
    assert enriquecida[0].nome_diretor == ""


def test_enriquecer_unidades_usa_fallback_para_falha_inesperada(
    monkeypatch,
) -> None:
    """Mantém dados básicos quando o enriquecimento lança erro."""
    unidade = UnidadeEol(
        codigo_eol="094633",
        nome_escola="Unidade 094633",
        sigla_tipo_escola="EMEF",
        nome_dre="DRE",
        sigla_dre="DR",
        codigo_dre="1",
    )
    adapter = EolAdapter(client=FakeClient())

    def _falhar(_unidade: UnidadeEol) -> UnidadeRecreioEol:
        raise RuntimeError("falha inesperada")

    monkeypatch.setattr(adapter, "_enriquecer_unidade", _falhar)

    enriquecida = adapter.enriquecer_unidades((unidade,))

    assert enriquecida[0].codigo_eol == "094633"
    assert enriquecida[0].nome_escola == "Unidade 094633"
    assert enriquecida[0].email == ""


def test_enriquecer_unidades_ordena_por_nome_e_codigo() -> None:
    """Ordena as unidades enriquecidas por nome de escola e código EOL."""
    client = FakeClient()
    unidades = (
        UnidadeEol(
            codigo_eol="2",
            nome_escola="Bravo",
            sigla_tipo_escola="EMEF",
            nome_dre="DRE",
            sigla_dre="DR",
            codigo_dre="1",
        ),
        UnidadeEol(
            codigo_eol="1",
            nome_escola="Alfa",
            sigla_tipo_escola="EMEF",
            nome_dre="DRE",
            sigla_dre="DR",
            codigo_dre="1",
        ),
    )

    enriquecidas = EolAdapter(client=client).enriquecer_unidades(unidades)

    assert [u.codigo_eol for u in enriquecidas] == ["1", "2"]


def test_enriquecer_unidades_retorna_vazio_sem_unidades() -> None:
    """Devolve tupla vazia quando não há unidades para enriquecer."""
    enriquecidas = EolAdapter(client=FakeClient()).enriquecer_unidades(())

    assert enriquecidas == ()


def test_listar_unidades_diretas_recreio_integra_fluxo() -> None:
    """Integra filtro por tipo de UE, limite e enriquecimento."""
    client = FakeClient(
        unidades=[
            _unidade_bruta("094633", "EMEF"),
            _unidade_bruta("121000", "CEI DIRET"),
            _unidade_bruta("300000", "OUTRO"),
        ],
        diretores={"094633": "Diretor A", "121000": "Diretor B"},
    )

    unidades = EolAdapter(client=client).listar_unidades_diretas_recreio()

    assert [u.codigo_eol for u in unidades] == ["094633", "121000"]
    assert unidades[0].nome_diretor == "Diretor A"
    assert unidades[1].nome_diretor == "Diretor B"


def test_listar_unidades_diretas_recreio_aplica_limite() -> None:
    """Limita a quantidade de unidades antes do enriquecimento."""
    client = FakeClient(
        unidades=[
            _unidade_bruta("094633", "EMEF"),
            _unidade_bruta("121000", "CEI DIRET"),
        ]
    )

    unidades = EolAdapter(client=client).listar_unidades_diretas_recreio(
        limite=1
    )

    assert [u.codigo_eol for u in unidades] == ["094633"]


def _aluno_bruto() -> dict[str, Any]:
    """Monta o aluno bruto usado na consulta do participante."""
    return {
        "codigoAluno": 1234567,
        "tipoTurno": 1,
        "anoLetivo": 2026,
        "nomeAluno": "Aluna de Teste",
        "nomeSocialAluno": "Aluna",
        "codigoSituacaoMatricula": 1,
        "situacaoMatricula": "Ativo",
        "dataSituacao": "2026-02-01",
        "dataNascimento": "2015-03-10",
        "numeroAlunoChamada": "12",
        "codigoTurma": 99,
        "nomeResponsavel": "Maria Responsavel",
        "tipoResponsavel": "Mae",
        "celularResponsavel": "11999999999",
        "dataAtualizacaoContato": "2026-01-15",
        "codigoTipoTurma": 3,
        "turmaNome": "1A",
        "etapaEnsino": "EFI",
        "cicloEnsino": "C1",
        "descEtapaEnsino": "Ensino Fundamental",
        "descCicloEnsino": "Ciclo 1",
        "dataAtualizacaoTabela": "2026-02-01",
    }


def _informacoes_brutas() -> dict[str, Any]:
    """Monta a ficha bruta com o endereço de exemplo da tarefa."""
    return {
        "nomeMae": "Maria Mae",
        "sexo": "F",
        "grupoEtnico": "Nao declarado",
        "nacionalidade": "Brasileira",
        "ehImigrante": False,
        "nis": "23703487417",
        "cns": None,
        "endereco": {
            "id": 28647483,
            "nro": "72",
            "complemento": None,
            "bairro": "VILA SANTA CRUZ ZONA LESTE",
            "cep": 8411010,
            "nomeMunicipio": "SAO PAULO",
            "siglaUF": "SP",
            "tipologradouro": "Rua",
            "logradouro": "DA PASSAGEM FUNDA",
        },
    }


def _participante_esperado() -> ParticipanteRedeEol:
    """Monta o participante já unido e normalizado."""
    return ParticipanteRedeEol(
        codigo_aluno=1234567,
        tipo_turno=1,
        ano_letivo=2026,
        nome_aluno="Aluna de Teste",
        nome_social_aluno="Aluna",
        codigo_situacao_matricula=1,
        situacao_matricula="Ativo",
        data_situacao="2026-02-01",
        data_nascimento="2015-03-10",
        numero_aluno_chamada="12",
        codigo_turma=99,
        nome_responsavel="Maria Responsavel",
        tipo_responsavel="Mae",
        celular_responsavel="11999999999",
        data_atualizacao_contato="2026-01-15",
        codigo_tipo_turma=3,
        turma_nome="1A",
        etapa_ensino="EFI",
        ciclo_ensino="C1",
        desc_etapa_ensino="Ensino Fundamental",
        desc_ciclo_ensino="Ciclo 1",
        data_atualizacao_tabela="2026-02-01",
        nome_mae="Maria Mae",
        sexo="F",
        grupo_etnico="Nao declarado",
        nacionalidade="Brasileira",
        eh_imigrante=False,
        nis="23703487417",
        cns="",
        numero="72",
        complemento="",
        bairro="VILA SANTA CRUZ ZONA LESTE",
        cep="08411-010",
        cidade="SAO PAULO",
        uf="SP",
        tipo_logradouro="Rua",
        logradouro="DA PASSAGEM FUNDA",
    )


def test_listar_alunos_normaliza_payload() -> None:
    """Converte o aluno bruto em ``AlunoEol``."""
    client = FakeClient(alunos=[_aluno_bruto()])

    alunos = EolAdapter(client=client).listar_alunos("1234567")

    assert alunos == (
        AlunoEol(
            codigo_aluno=1234567,
            tipo_turno=1,
            ano_letivo=2026,
            nome_aluno="Aluna de Teste",
            nome_social_aluno="Aluna",
            codigo_situacao_matricula=1,
            situacao_matricula="Ativo",
            data_situacao="2026-02-01",
            data_nascimento="2015-03-10",
            numero_aluno_chamada="12",
            codigo_turma=99,
            nome_responsavel="Maria Responsavel",
            tipo_responsavel="Mae",
            celular_responsavel="11999999999",
            data_atualizacao_contato="2026-01-15",
            codigo_tipo_turma=3,
            turma_nome="1A",
            etapa_ensino="EFI",
            ciclo_ensino="C1",
            desc_etapa_ensino="Ensino Fundamental",
            desc_ciclo_ensino="Ciclo 1",
            data_atualizacao_tabela="2026-02-01",
        ),
    )


def test_listar_alunos_trata_inteiro_ausente_ou_bool() -> None:
    """Inteiro ausente ou bool vira zero."""
    client = FakeClient(
        alunos=[
            {
                "codigoAluno": None,
                "tipoTurno": True,
                "anoLetivo": 2026,
            }
        ]
    )

    aluno = EolAdapter(client=client).listar_alunos("1234567")[0]

    assert aluno.codigo_aluno == 0
    assert aluno.tipo_turno == 0
    assert aluno.ano_letivo == 2026
    assert aluno.nome_aluno == ""
    assert aluno.data_nascimento == ""


def test_listar_alunos_formata_data_de_nascimento() -> None:
    """Data com horário da SME vira ``AAAA-MM-DD``."""
    client = FakeClient(alunos=[{"dataNascimento": "2013-10-16T00:00:00"}])

    aluno = EolAdapter(client=client).listar_alunos("1234567")[0]

    assert aluno.data_nascimento == "2013-10-16"


def test_obter_informacoes_aluno_normaliza_endereco() -> None:
    """Achata o endereço e formata o CEP numérico."""
    client = FakeClient(informacoes=_informacoes_brutas())

    ficha = EolAdapter(client=client).obter_informacoes_aluno("1234567")

    assert ficha == InformacoesAlunoEol(
        nome_mae="Maria Mae",
        sexo="F",
        grupo_etnico="Nao declarado",
        nacionalidade="Brasileira",
        eh_imigrante=False,
        nis="23703487417",
        cns="",
        numero="72",
        complemento="",
        bairro="VILA SANTA CRUZ ZONA LESTE",
        cep="08411-010",
        cidade="SAO PAULO",
        uf="SP",
        tipo_logradouro="Rua",
        logradouro="DA PASSAGEM FUNDA",
    )


def test_obter_informacoes_aluno_trata_endereco_ausente() -> None:
    """Endereço nulo e flag que não é bool viram vazio e falso."""
    client = FakeClient(
        informacoes={"endereco": None, "ehImigrante": None, "cns": None}
    )

    ficha = EolAdapter(client=client).obter_informacoes_aluno("1234567")

    assert ficha == InformacoesAlunoEol(
        nome_mae="",
        sexo="",
        grupo_etnico="",
        nacionalidade="",
        eh_imigrante=False,
        nis="",
        cns="",
        numero="",
        complemento="",
        bairro="",
        cep="",
        cidade="",
        uf="",
        tipo_logradouro="",
        logradouro="",
    )


def test_obter_informacoes_aluno_retorna_none_para_ausente() -> None:
    """Devolve ``None`` quando a ficha não existe."""
    client = FakeClient()

    ficha = EolAdapter(client=client).obter_informacoes_aluno("1234567")

    assert ficha is None


def test_consultar_participante_devolve_none_sem_chamar_ficha() -> None:
    """Lista vazia devolve ``None`` e não consulta a ficha."""
    client = FakeClient(alunos=[])

    participante = EolAdapter(client=client).consultar_participante("1234567")

    assert participante is None
    assert client.calls_informacoes == []


def test_consultar_participante_une_aluno_e_ficha() -> None:
    """Os dois payloads viram um participante com CEP formatado."""
    client = FakeClient(
        alunos=[_aluno_bruto()],
        informacoes=_informacoes_brutas(),
    )

    participante = EolAdapter(client=client).consultar_participante("1234567")

    assert participante == _participante_esperado()
    assert client.calls_informacoes == ["1234567"]


def test_consultar_participante_mantem_aluno_quando_ficha_ausente() -> None:
    """Ficha 404 preserva o aluno e deixa o endereço vazio."""
    client = FakeClient(alunos=[_aluno_bruto()])

    participante = EolAdapter(client=client).consultar_participante("1234567")

    assert participante == ParticipanteRedeEol(
        codigo_aluno=1234567,
        tipo_turno=1,
        ano_letivo=2026,
        nome_aluno="Aluna de Teste",
        nome_social_aluno="Aluna",
        codigo_situacao_matricula=1,
        situacao_matricula="Ativo",
        data_situacao="2026-02-01",
        data_nascimento="2015-03-10",
        numero_aluno_chamada="12",
        codigo_turma=99,
        nome_responsavel="Maria Responsavel",
        tipo_responsavel="Mae",
        celular_responsavel="11999999999",
        data_atualizacao_contato="2026-01-15",
        codigo_tipo_turma=3,
        turma_nome="1A",
        etapa_ensino="EFI",
        ciclo_ensino="C1",
        desc_etapa_ensino="Ensino Fundamental",
        desc_ciclo_ensino="Ciclo 1",
        data_atualizacao_tabela="2026-02-01",
        nome_mae="",
        sexo="",
        grupo_etnico="",
        nacionalidade="",
        eh_imigrante=False,
        nis="",
        cns="",
        numero="",
        complemento="",
        bairro="",
        cep="",
        cidade="",
        uf="",
        tipo_logradouro="",
        logradouro="",
    )
    assert client.calls_informacoes == ["1234567"]
