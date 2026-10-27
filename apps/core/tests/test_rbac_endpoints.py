"""Testes da matriz RBAC aplicada aos endpoints de domínio ativos."""

import pytest
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.definicoes_polos.api.views.definicao_polo_viewset import (
    DefinicaoPoloViewSet,
)
from apps.edicoes.api.views.edicao_viewset import EdicaoViewSet
from apps.inscricoes.api.views.inscricao_viewset import InscricaoViewSet
from apps.polos.api.views.polo_viewset import PoloViewSet

pytestmark = pytest.mark.django_db

ADMINISTRADOR_DICEU = frozenset(
    {"ADMINISTRADOR_COCEU", "GESTOR_DICEU"}
)
ADMINISTRADOR = frozenset({"ADMINISTRADOR_COCEU"})
VISUALIZACAO_POLOS = frozenset(
    {
        "ADMINISTRADOR_COCEU",
        "GESTOR_DICEU",
        "GESTOR_CODAE",
        "GESTOR_ASCOM",
        "GESTOR_POLO",
    }
)
CONSULTA_DRES = VISUALIZACAO_POLOS | {"USUARIO_UE"}
VISUALIZACAO_EDICOES = frozenset(
    {
        "ADMINISTRADOR_COCEU",
        "GESTOR_DICEU",
        "GESTOR_CODAE",
        "GESTOR_ASCOM",
        "GESTOR_COGED",
        "GESTOR_POLO",
    }
)
GESTAO_DEFINICOES = frozenset(
    {"ADMINISTRADOR_COCEU", "GESTOR_DICEU", "GESTOR_POLO"}
)
VISUALIZACAO_INSCRICOES = frozenset(
    {
        "ADMINISTRADOR_COCEU",
        "GESTOR_DICEU",
        "GESTOR_CODAE",
        "GESTOR_POLO",
        "USUARIO_UE",
    }
)
GESTAO_INSCRICOES = frozenset(
    {"ADMINISTRADOR_COCEU", "USUARIO_UE"}
)

CASOS_ACESSO = [
    pytest.param(
        PoloViewSet,
        "list",
        "GET",
        VISUALIZACAO_POLOS,
        id="polos-listar",
    ),
    pytest.param(
        PoloViewSet,
        "retrieve",
        "GET",
        VISUALIZACAO_POLOS,
        id="polos-detalhar",
    ),
    pytest.param(
        PoloViewSet,
        "create",
        "POST",
        ADMINISTRADOR_DICEU,
        id="polos-criar",
    ),
    pytest.param(
        PoloViewSet,
        "update",
        "PUT",
        ADMINISTRADOR_DICEU,
        id="polos-editar",
    ),
    pytest.param(
        PoloViewSet,
        "partial_update",
        "PATCH",
        ADMINISTRADOR_DICEU,
        id="polos-editar-parcialmente",
    ),
    pytest.param(
        PoloViewSet,
        "destroy",
        "DELETE",
        ADMINISTRADOR_DICEU,
        id="polos-excluir",
    ),
    pytest.param(
        PoloViewSet,
        "dres",
        "GET",
        CONSULTA_DRES,
        id="polos-consultar-dres",
    ),
    pytest.param(
        PoloViewSet,
        "obter_dados_da_unidade_pelo_codigo_eol",
        "GET",
        VISUALIZACAO_POLOS,
        id="polos-consultar-unidade-eol",
    ),
    pytest.param(
        PoloViewSet,
        "tipos_escola",
        "GET",
        VISUALIZACAO_POLOS,
        id="polos-consultar-tipos-escola",
    ),
    pytest.param(
        PoloViewSet,
        "popular",
        "POST",
        ADMINISTRADOR_DICEU,
        id="polos-popular",
    ),
    pytest.param(
        EdicaoViewSet,
        "list",
        "GET",
        VISUALIZACAO_EDICOES,
        id="edicoes-listar",
    ),
    pytest.param(
        EdicaoViewSet,
        "retrieve",
        "GET",
        VISUALIZACAO_EDICOES,
        id="edicoes-detalhar",
    ),
    pytest.param(
        EdicaoViewSet,
        "create",
        "POST",
        ADMINISTRADOR,
        id="edicoes-criar",
    ),
    pytest.param(
        EdicaoViewSet,
        "update",
        "PUT",
        ADMINISTRADOR,
        id="edicoes-editar",
    ),
    pytest.param(
        EdicaoViewSet,
        "partial_update",
        "PATCH",
        ADMINISTRADOR,
        id="edicoes-editar-parcialmente",
    ),
    pytest.param(
        EdicaoViewSet,
        "destroy",
        "DELETE",
        ADMINISTRADOR,
        id="edicoes-excluir",
    ),
    pytest.param(
        DefinicaoPoloViewSet,
        "list",
        "GET",
        GESTAO_DEFINICOES,
        id="definicoes-listar",
    ),
    pytest.param(
        DefinicaoPoloViewSet,
        "retrieve",
        "GET",
        GESTAO_DEFINICOES,
        id="definicoes-detalhar",
    ),
    pytest.param(
        DefinicaoPoloViewSet,
        "historico",
        "GET",
        GESTAO_DEFINICOES,
        id="definicoes-historico",
    ),
    pytest.param(
        DefinicaoPoloViewSet,
        "create",
        "POST",
        GESTAO_DEFINICOES,
        id="definicoes-criar",
    ),
    pytest.param(
        DefinicaoPoloViewSet,
        "update",
        "PUT",
        GESTAO_DEFINICOES,
        id="definicoes-editar",
    ),
    pytest.param(
        DefinicaoPoloViewSet,
        "partial_update",
        "PATCH",
        GESTAO_DEFINICOES,
        id="definicoes-editar-parcialmente",
    ),
    pytest.param(
        DefinicaoPoloViewSet,
        "destroy",
        "DELETE",
        GESTAO_DEFINICOES,
        id="definicoes-excluir",
    ),
    pytest.param(
        DefinicaoPoloViewSet,
        "vincular_em_massa",
        "POST",
        GESTAO_DEFINICOES,
        id="definicoes-vincular-em-massa",
    ),
    pytest.param(
        DefinicaoPoloViewSet,
        "alterar_tipo_em_massa",
        "POST",
        GESTAO_DEFINICOES,
        id="definicoes-alterar-tipo-em-massa",
    ),
    pytest.param(
        DefinicaoPoloViewSet,
        "alterar_edicao_em_massa",
        "POST",
        GESTAO_DEFINICOES,
        id="definicoes-alterar-edicao-em-massa",
    ),
    pytest.param(
        InscricaoViewSet,
        "list",
        "GET",
        VISUALIZACAO_INSCRICOES,
        id="inscricoes-listar",
    ),
    pytest.param(
        InscricaoViewSet,
        "retrieve",
        "GET",
        VISUALIZACAO_INSCRICOES,
        id="inscricoes-detalhar",
    ),
    pytest.param(
        InscricaoViewSet,
        "create",
        "POST",
        GESTAO_INSCRICOES,
        id="inscricoes-criar",
    ),
    pytest.param(
        InscricaoViewSet,
        "update",
        "PUT",
        GESTAO_INSCRICOES,
        id="inscricoes-editar",
    ),
    pytest.param(
        InscricaoViewSet,
        "partial_update",
        "PATCH",
        GESTAO_INSCRICOES,
        id="inscricoes-editar-parcialmente",
    ),
    pytest.param(
        InscricaoViewSet,
        "destroy",
        "DELETE",
        ADMINISTRADOR,
        id="inscricoes-excluir",
    ),
    pytest.param(
        InscricaoViewSet,
        "cancelar",
        "POST",
        GESTAO_INSCRICOES,
        id="inscricoes-cancelar",
    ),
    pytest.param(
        InscricaoViewSet,
        "reativar",
        "POST",
        GESTAO_INSCRICOES,
        id="inscricoes-reativar",
    ),
    pytest.param(
        InscricaoViewSet,
        "polos_elegiveis",
        "GET",
        VISUALIZACAO_INSCRICOES,
        id="inscricoes-polos-elegiveis",
    ),
    pytest.param(
        InscricaoViewSet,
        "polos_oficiais",
        "GET",
        VISUALIZACAO_INSCRICOES,
        id="inscricoes-polos-oficiais",
    ),
    pytest.param(
        InscricaoViewSet,
        "participante_eol",
        "GET",
        VISUALIZACAO_INSCRICOES,
        id="inscricoes-consultar-participante-eol",
    ),
    pytest.param(
        InscricaoViewSet,
        "participante_cpf",
        "GET",
        VISUALIZACAO_INSCRICOES,
        id="inscricoes-consultar-participante-cpf",
    ),
    pytest.param(
        InscricaoViewSet,
        "valores_choices",
        "GET",
        VISUALIZACAO_INSCRICOES,
        id="inscricoes-valores-choices",
    ),
]

CASOS_ACOES_CUSTOMIZADAS = [
    pytest.param(
        PoloViewSet,
        "dres",
        "GET",
        "visualizar_dres",
        "visualizar_polos",
        id="polos-dres-permissao-propria",
    ),
    pytest.param(
        PoloViewSet,
        "obter_dados_da_unidade_pelo_codigo_eol",
        "GET",
        "visualizar_polos",
        "criar_polos",
        id="polos-unidade-eol",
    ),
    pytest.param(
        PoloViewSet,
        "tipos_escola",
        "GET",
        "visualizar_polos",
        "criar_polos",
        id="polos-tipos-escola",
    ),
    pytest.param(
        PoloViewSet,
        "popular",
        "POST",
        "criar_polos",
        "editar_polos",
        id="polos-popular",
    ),
    pytest.param(
        DefinicaoPoloViewSet,
        "historico",
        "GET",
        "visualizar_definicoes_polos",
        "criar_definicoes_polos",
        id="definicoes-historico",
    ),
    pytest.param(
        DefinicaoPoloViewSet,
        "vincular_em_massa",
        "POST",
        "criar_definicoes_polos",
        "editar_definicoes_polos",
        id="definicoes-vincular-em-massa",
    ),
    pytest.param(
        DefinicaoPoloViewSet,
        "alterar_tipo_em_massa",
        "POST",
        "editar_definicoes_polos",
        "criar_definicoes_polos",
        id="definicoes-alterar-tipo-em-massa",
    ),
    pytest.param(
        DefinicaoPoloViewSet,
        "alterar_edicao_em_massa",
        "POST",
        "editar_definicoes_polos",
        "criar_definicoes_polos",
        id="definicoes-alterar-edicao-em-massa",
    ),
    pytest.param(
        InscricaoViewSet,
        "cancelar",
        "POST",
        "editar_inscricoes_participantes",
        "criar_inscricoes_participantes",
        id="inscricoes-cancelar-exige-edicao",
    ),
    pytest.param(
        InscricaoViewSet,
        "reativar",
        "POST",
        "editar_inscricoes_participantes",
        "criar_inscricoes_participantes",
        id="inscricoes-reativar-exige-edicao",
    ),
    pytest.param(
        InscricaoViewSet,
        "polos_elegiveis",
        "GET",
        "visualizar_inscricoes_participantes",
        "criar_inscricoes_participantes",
        id="inscricoes-polos-elegiveis",
    ),
    pytest.param(
        InscricaoViewSet,
        "polos_oficiais",
        "GET",
        "visualizar_inscricoes_participantes",
        "criar_inscricoes_participantes",
        id="inscricoes-polos-oficiais",
    ),
    pytest.param(
        InscricaoViewSet,
        "participante_eol",
        "GET",
        "visualizar_inscricoes_participantes",
        "criar_inscricoes_participantes",
        id="inscricoes-participante-eol",
    ),
    pytest.param(
        InscricaoViewSet,
        "participante_cpf",
        "GET",
        "visualizar_inscricoes_participantes",
        "criar_inscricoes_participantes",
        id="inscricoes-participante-cpf",
    ),
    pytest.param(
        InscricaoViewSet,
        "valores_choices",
        "GET",
        "visualizar_inscricoes_participantes",
        "criar_inscricoes_participantes",
        id="inscricoes-valores-choices",
    ),
]


@pytest.mark.parametrize(
    ("viewset_class", "acao", "metodo", "perfis_autorizados"),
    CASOS_ACESSO,
)
def test_viewsets_aplicam_matriz_de_acesso_por_perfil(
    viewset_class: type,
    acao: str,
    metodo: str,
    perfis_autorizados: frozenset[str],
    perfis_rbac: tuple[str, ...],
    criar_usuario_rbac,
) -> None:
    """Permite ou nega cada ação conforme o grupo RBAC atribuído."""
    for perfil in perfis_rbac:
        usuario = criar_usuario_rbac(perfis=(perfil,))

        request_bruta = APIRequestFactory().generic(
            metodo,
            "/api/v1/recurso-de-teste/",
        )
        force_authenticate(request_bruta, user=usuario)

        viewset = viewset_class()
        viewset.action_map = {metodo.lower(): acao}
        request = viewset.initialize_request(request_bruta)
        viewset.request = request

        if perfil in perfis_autorizados:
            viewset.check_permissions(request)
        else:
            with pytest.raises(PermissionDenied):
                viewset.check_permissions(request)


@pytest.mark.parametrize(
    (
        "viewset_class",
        "acao",
        "metodo",
        "permissao_correta",
        "permissao_errada",
    ),
    CASOS_ACOES_CUSTOMIZADAS,
)
def test_acoes_customizadas_aceitam_apenas_a_permissao_individual_mapeada(
    viewset_class: type,
    acao: str,
    metodo: str,
    permissao_correta: str,
    permissao_errada: str,
    criar_usuario_rbac,
) -> None:
    """Valida ações customizadas com permissões individuais mapeadas."""
    for codename, deve_permitir in (
        (permissao_correta, True),
        (permissao_errada, False),
    ):
        usuario = criar_usuario_rbac(permissoes=(codename,))
        request_bruta = APIRequestFactory().generic(
            metodo,
            "/api/v1/recurso-de-teste/",
        )
        force_authenticate(request_bruta, user=usuario)

        viewset = viewset_class()
        viewset.action_map = {metodo.lower(): acao}
        request = viewset.initialize_request(request_bruta)
        viewset.request = request

        if deve_permitir:
            viewset.check_permissions(request)
        else:
            with pytest.raises(PermissionDenied):
                viewset.check_permissions(request)
