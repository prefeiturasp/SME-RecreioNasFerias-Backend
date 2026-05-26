"""
Views HTTP para operações de usuários e autenticação.

Expõe login CoreSSO (com log de auditoria e token Bearer) e CRUD legado
de usuários de exemplo, delegando regras de negócio aos casos de uso da
camada de aplicação e adaptadores de infraestrutura.
"""

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from django.contrib.auth import get_user_model
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import serializers
from rest_framework.decorators import api_view
from application.dtos.create_user_dto import CreateUserDto
from application.dtos.login_input_dto import LoginInputDto
from application.dtos.update_user_dto import UpdateUserDto
from application.dtos.user_output_dto import UserOutputDTO
from application.exceptions import CargoNaoAutorizadoError
from application.services.usuarios_rbac import UsuariosRbac
from application.services.usuarios_validador import UsuariosValidador
from application.use_cases.create_user import CreateUserUseCase
from application.use_cases.delete_user import DeleteUserUseCase
from application.use_cases.get_user_by_id import GetUserByIdUseCase
from application.use_cases.list_users import ListUsersUseCase
from application.use_cases.login_user import LoginUserUseCase
from application.use_cases.update_user import UpdateUserUseCase
from infrastructure.repositories.cargos_permitidos_repository import (
    CargosPermitidosRepository,
)
from infrastructure.repositories.django_user_repository import DjangoUserRepository
from infrastructure.repositories.usuarios_repository import UsuariosRepository
from infrastructure.services.usuarios_service import UsuariosService
from usuarios.auth_tokens import gerar_token_acesso
from usuarios.log_login import (
    MENSAGEM_SUCESSO_LOGIN,
    extrair_codigo_e_descricao_cargo,
    registrar_log_login,
)

_JSON = {"ensure_ascii": False, "indent": 2}


@csrf_exempt
@extend_schema(
    tags=["Autenticacao"],
    request=inline_serializer(
        name="LoginRequest",
        fields={
            "login": serializers.CharField(),
            "senha": serializers.CharField(),
        },
    ),
    responses={
        200: inline_serializer(
            name="LoginResponse",
            fields={
                "rf": serializers.CharField(),
                "cpf": serializers.CharField(allow_null=True, required=False),
                "email": serializers.EmailField(allow_null=True, required=False),
                "cargos": serializers.ListField(
                    child=inline_serializer(
                        name="CargoResponse",
                        fields={
                            "codigoCargo": serializers.IntegerField(required=False),
                            "descricaoCargo": serializers.CharField(required=False),
                            "codigoUnidade": serializers.CharField(required=False),
                            "descricaoUnidade": serializers.CharField(required=False),
                            "codigoDre": serializers.CharField(required=False),
                            "contratoExterno": serializers.BooleanField(required=False),
                        },
                    )
                ),
                "nome": serializers.CharField(),
                "inexistenteEol": serializers.BooleanField(),
                "token": serializers.CharField(),
            },
        ),
        400: OpenApiResponse(description="Payload invalido ou dados invalidos"),
        401: OpenApiResponse(description="Credenciais invalidas"),
        403: OpenApiResponse(description="Cargo nao autorizado para o sistema"),
        502: OpenApiResponse(description="Falha de integracao externa"),
    },
)
@api_view(["POST"])
def login(request: HttpRequest):
    """Autentica usuário via CoreSSO e retorna dados funcionais com token Bearer.

    Args:
        request (HttpRequest): Requisição POST com JSON ``login`` e ``senha``.

    Returns:
        JsonResponse: Payload de sucesso (200), erro de validação (400/401),
            cargo não autorizado (403), integração (502) ou erro interno (500).
    """
    if request.method != "POST":
        return JsonResponse(
            {"error": "Método não permitido"},
            status=405,
            json_dumps_params=_JSON,
        )
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        registrar_log_login(
            sucesso=False,
            login_tentativa="",
            codigo_http=400,
            mensagem="Payload JSON inválido",
            request=request,
        )
        return JsonResponse(
            {"error": "Payload JSON inválido"},
            status=400,
            json_dumps_params=_JSON,
        )

    login_bruto = str(body.get("login") or "").strip()[:32]

    try:
        input_dto = LoginInputDto(login=body.get("login"), senha=body.get("senha"))
        use_case = LoginUserUseCase(
            coresso_port=UsuariosService(),
            usuarios_repository_port=UsuariosRepository(),
            usuarios_validador=UsuariosValidador(),
            usuarios_rbac=UsuariosRbac(),
            cargos_permitidos_port=CargosPermitidosRepository(),
        )
        output = use_case.execute(input_dto)
        response_body = output.to_dict()
        usuario = get_user_model().objects.get(rf=output.rf)
        response_body["token"] = gerar_token_acesso(usuario)
        codigo_c, desc_c = extrair_codigo_e_descricao_cargo(
            response_body.get("cargos")
        )
        registrar_log_login(
            sucesso=True,
            login_tentativa=response_body["rf"],
            codigo_http=200,
            mensagem=MENSAGEM_SUCESSO_LOGIN,
            request=request,
            codigo_cargo=codigo_c,
            descricao_cargo=desc_c,
        )
        return JsonResponse(response_body, status=200, json_dumps_params=_JSON)
    except CargoNaoAutorizadoError as e:
        registrar_log_login(
            sucesso=False,
            login_tentativa=login_bruto,
            codigo_http=403,
            mensagem=str(e),
            request=request,
        )
        return JsonResponse({"error": str(e)}, status=403, json_dumps_params=_JSON)
    except ValueError as e:
        status_code = 401 if str(e) == "Credenciais inválidas" else 400
        registrar_log_login(
            sucesso=False,
            login_tentativa=login_bruto,
            codigo_http=status_code,
            mensagem=str(e),
            request=request,
        )
        return JsonResponse({"error": str(e)}, status=status_code, json_dumps_params=_JSON)
    except RuntimeError as e:
        registrar_log_login(
            sucesso=False,
            login_tentativa=login_bruto,
            codigo_http=502,
            mensagem=str(e),
            request=request,
        )
        return JsonResponse({"error": str(e)}, status=502, json_dumps_params=_JSON)
    except Exception as e:
        registrar_log_login(
            sucesso=False,
            login_tentativa=login_bruto,
            codigo_http=500,
            mensagem=str(e),
            request=request,
        )
        return JsonResponse({"error": str(e)}, status=500, json_dumps_params=_JSON)


@csrf_exempt
@extend_schema_view(
    get=extend_schema(
        tags=["Usuarios"],
        responses={200: OpenApiResponse(description="Lista de usuarios")},
    ),
    post=extend_schema(
        tags=["Usuarios"],
        request=inline_serializer(
            name="CreateUsuarioRequest",
            fields={
                "nome": serializers.CharField(),
                "email": serializers.EmailField(),
            },
        ),
        responses={201: OpenApiResponse(description="Usuario criado com sucesso")},
    ),
)
@api_view(["GET", "POST"])
def users(request: HttpRequest):
    """Despacha GET (listagem) ou POST (criação) na coleção ``/api/usuarios/``.

    Args:
        request (HttpRequest): Requisição HTTP.

    Returns:
        JsonResponse: Resposta do handler correspondente ou 405.
    """
    if request.method == "POST":
        return create_user(request)
    if request.method == "GET":
        return list_users(request)
    return JsonResponse(
        {"error": "Método não permitido"},
        status=405,
        json_dumps_params=_JSON,
    )


@csrf_exempt
@extend_schema_view(
    get=extend_schema(
        tags=["Usuarios"],
        responses={200: OpenApiResponse(description="Usuario encontrado")},
    ),
    put=extend_schema(
        tags=["Usuarios"],
        request=inline_serializer(
            name="UpdateUsuarioRequest",
            fields={
                "nome": serializers.CharField(required=False),
                "email": serializers.EmailField(required=False),
            },
        ),
        responses={200: OpenApiResponse(description="Usuario atualizado")},
    ),
    delete=extend_schema(
        tags=["Usuarios"],
        responses={204: OpenApiResponse(description="Usuario removido")},
    ),
)
@api_view(["GET", "PUT", "DELETE"])
def user_by_id(request: HttpRequest, user_id):
    """Despacha GET, PUT ou DELETE em ``/api/usuarios/<uuid>/``.

    Args:
        request (HttpRequest): Requisição HTTP.
        user_id: UUID do usuário na URL.

    Returns:
        JsonResponse: Resposta do handler correspondente ou 405.
    """
    if request.method == "GET":
        return get_user_by_id(request, str(user_id))
    if request.method == "PUT":
        return update_user(request, str(user_id))
    if request.method == "DELETE":
        return delete_user(request, str(user_id))
    return JsonResponse(
        {"error": "Método não permitido"},
        status=405,
        json_dumps_params=_JSON,
    )


def create_user(request: HttpRequest):
    """Cria usuário via caso de uso e retorna JSON 201.

    Args:
        request (HttpRequest): POST com ``nome`` e ``email`` no corpo JSON.

    Returns:
        JsonResponse: Dados do usuário criado ou erro 500.
    """
    if request.method != "POST":
        return JsonResponse(
            {"error": "Método não permitido"},
            status=405,
            json_dumps_params=_JSON,
        )

    try:
        body = json.loads(request.body)
        input_dto = CreateUserDto(nome=body.get("nome"), email=body.get("email"))
        use_case = CreateUserUseCase(DjangoUserRepository())
        output: UserOutputDTO = use_case.execute(input_dto)
        return JsonResponse(output.to_dict(), status=201, json_dumps_params=_JSON)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500, json_dumps_params=_JSON)


def list_users(request: HttpRequest):
    """Lista todos os usuários do repositório legado.

    Args:
        request (HttpRequest): Requisição GET.

    Returns:
        JsonResponse: Array JSON de usuários ou erro 500.
    """
    if request.method != "GET":
        return JsonResponse(
            {"error": "Método não permitido"},
            status=405,
            json_dumps_params=_JSON,
        )

    try:
        use_case = ListUsersUseCase(DjangoUserRepository())
        output = use_case.execute()
        return JsonResponse(
            [user.to_dict() for user in output],
            safe=False,
            status=200,
            json_dumps_params=_JSON,
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500, json_dumps_params=_JSON)


def get_user_by_id(request: HttpRequest, user_id: str):
    """Retorna um usuário pelo identificador UUID.

    Args:
        request (HttpRequest): Requisição GET.
        user_id (str): UUID do usuário.

    Returns:
        JsonResponse: Usuário (200), não encontrado (404) ou erro 500.
    """
    if request.method != "GET":
        return JsonResponse(
            {"error": "Método não permitido"},
            status=405,
            json_dumps_params=_JSON,
        )
    try:
        use_case = GetUserByIdUseCase(DjangoUserRepository())
        output = use_case.execute(user_id)
        return JsonResponse(output.to_dict(), status=200, json_dumps_params=_JSON)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=404, json_dumps_params=_JSON)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500, json_dumps_params=_JSON)


def update_user(request: HttpRequest, user_id: str):
    """Atualiza parcialmente nome e/ou e-mail de um usuário.

    Args:
        request (HttpRequest): PUT com campos opcionais no JSON.
        user_id (str): UUID do usuário.

    Returns:
        JsonResponse: Usuário atualizado (200), 404/400 ou erro 500.
    """
    if request.method != "PUT":
        return JsonResponse(
            {"error": "Método não permitido"},
            status=405,
            json_dumps_params=_JSON,
        )
    try:
        body = json.loads(request.body)
        input_dto = UpdateUserDto(nome=body.get("nome"), email=body.get("email"))
        use_case = UpdateUserUseCase(DjangoUserRepository())
        output = use_case.execute(user_id, input_dto)
        return JsonResponse(output.to_dict(), status=200, json_dumps_params=_JSON)
    except ValueError as e:
        status_code = 404 if str(e) == "Usuário não encontrado" else 400
        return JsonResponse(
            {"error": str(e)}, status=status_code, json_dumps_params=_JSON
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500, json_dumps_params=_JSON)


def delete_user(request: HttpRequest, user_id: str):
    """Remove usuário pelo identificador UUID.

    Args:
        request (HttpRequest): Requisição DELETE.
        user_id (str): UUID do usuário.

    Returns:
        JsonResponse: Corpo vazio (204), não encontrado (404) ou erro 500.
    """
    if request.method != "DELETE":
        return JsonResponse(
            {"error": "Método não permitido"},
            status=405,
            json_dumps_params=_JSON,
        )
    try:
        use_case = DeleteUserUseCase(DjangoUserRepository())
        use_case.execute(user_id)
        return JsonResponse({}, status=204, json_dumps_params=_JSON)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=404, json_dumps_params=_JSON)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500, json_dumps_params=_JSON)
