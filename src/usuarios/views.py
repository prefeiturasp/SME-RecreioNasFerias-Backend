from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from application.dtos.create_user_dto import CreateUserDto
from application.dtos.update_user_dto import UpdateUserDto
from application.dtos.user_output_dto import UserOutputDTO
from application.use_cases.create_user import CreateUserUseCase
from application.use_cases.delete_user import DeleteUserUseCase
from application.use_cases.get_user_by_id import GetUserByIdUseCase
from application.use_cases.list_users import ListUsersUseCase
from application.use_cases.update_user import UpdateUserUseCase
from infrastructure.repositories.django_user_repository import DjangoUserRepository

_JSON = {"ensure_ascii": False, "indent": 2}


@csrf_exempt
def users(request: HttpRequest):
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
def user_by_id(request: HttpRequest, user_id):
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
        return JsonResponse({"error": str(e)}, status=status_code, json_dumps_params=_JSON)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500, json_dumps_params=_JSON)


def delete_user(request: HttpRequest, user_id: str):
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
