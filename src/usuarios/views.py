from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from application.dtos.create_user_dto import CreateUserDto
from application.dtos.user_output_dto import UserOutputDTO
from application.use_cases.create_user import CreateUserUseCase
from application.use_cases.list_users import ListUsersUseCase
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
