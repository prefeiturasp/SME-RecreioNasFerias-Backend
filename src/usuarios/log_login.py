"""
Persistência de tentativas de login para auditoria.

Funções auxiliares usadas pela view ``login`` para registrar sucesso ou
falha com IP, user-agent e metadados de cargo quando aplicável.
"""

from django.http import HttpRequest

from usuarios.models import LogLoginModel

MENSAGEM_SUCESSO_LOGIN = "Autenticação realizada com sucesso."


def extrair_codigo_e_descricao_cargo(cargos: object) -> tuple[int | None, str]:
    """Extrai ``codigoCargo`` e ``descricaoCargo`` do primeiro item de ``cargos``.

    Args:
        cargos (object): Lista de dicionários retornada no payload de login.

    Returns:
        tuple[int | None, str]: Código numérico (ou ``None``) e descrição truncada
            em 500 caracteres.
    """
    if not isinstance(cargos, list) or not cargos:
        return None, ""
    primeiro = cargos[0]
    if not isinstance(primeiro, dict):
        return None, ""
    bruto = primeiro.get("codigoCargo")
    codigo: int | None
    if bruto is None or bruto == "":
        codigo = None
    else:
        try:
            codigo = int(bruto)
        except (TypeError, ValueError):
            codigo = None
    descricao = (
        primeiro.get("descricaoCargo")
        or primeiro.get("nomeCargo")
        or ""
    )
    return codigo, str(descricao)[:500]


def _obter_endereco_ip(request: HttpRequest) -> str:
    """Obtém o IP do cliente, considerando proxy reverso (``X-Forwarded-For``).

    Args:
        request (HttpRequest): Requisição HTTP atual.

    Returns:
        str: Endereço IP truncado em 45 caracteres (IPv4/IPv6).
    """
    encaminhado = request.META.get("HTTP_X_FORWARDED_FOR")
    if encaminhado:
        return encaminhado.split(",")[0].strip()[:45]
    return (request.META.get("REMOTE_ADDR") or "")[:45]


def registrar_log_login(
    *,
    sucesso: bool,
    login_tentativa: str,
    codigo_http: int,
    mensagem: str,
    request: HttpRequest | None,
    codigo_cargo: int | None = None,
    descricao_cargo: str = "",
) -> None:
    """Registra uma tentativa de login na tabela ``usuarios_logs_login``.

    Em sucesso, use ``MENSAGEM_SUCESSO_LOGIN`` ou outra mensagem descritiva.
    Em falha, informe o motivo (ex.: exceção ou validação). O identificador
    do registro é gerado pelo banco (sequência), como no padrão Django.

    Args:
        sucesso (bool): Indica autenticação bem-sucedida.
        login_tentativa (str): RF ou login informado (truncado em 32 caracteres).
        codigo_http (int): Status HTTP retornado ao cliente.
        mensagem (str): Texto livre descrevendo o resultado.
        request (HttpRequest | None): Requisição para IP e user-agent; pode ser
            ``None`` em testes.
        codigo_cargo (int | None): Código SIGPAE em login bem-sucedido.
        descricao_cargo (str): Descrição do cargo associado ao sucesso.
    """
    endereco_ip = ""
    user_agent = ""
    if request is not None:
        endereco_ip = _obter_endereco_ip(request)
        user_agent = (request.META.get("HTTP_USER_AGENT") or "")[:4096]

    LogLoginModel.objects.create(
        sucesso=sucesso,
        login_tentativa=(login_tentativa or "")[:32],
        codigo_http=codigo_http,
        mensagem=mensagem or "",
        endereco_ip=endereco_ip,
        user_agent=user_agent,
        codigo_cargo=codigo_cargo,
        descricao_cargo=(descricao_cargo or "")[:500],
    )
