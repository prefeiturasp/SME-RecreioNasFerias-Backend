"""Adaptador da integração com o CoreSSO.

Implementa o contrato consumido pelo `core` e centraliza delegação
para o client HTTP do provedor institucional.
"""

from __future__ import annotations

from typing import Any, Protocol

from apps.integracoes.coresso.client import CoressoClient
from apps.integracoes.coresso.exceptions import CoressoContratoError
from apps.integracoes.coresso.port import (
    CargoCoresso,
    CoressoIdentity,
    CoressoPort,
    UnidadeCoresso,
)


class CoressoAuthClient(Protocol):
    """Protocolo mínimo do client usado pelo adaptador."""

    def autenticar(self, rf: str, senha: str) -> dict[str, Any]:
        """Executa autenticação e devolve o payload bruto do CoreSSO."""


class CoressoAdapter(CoressoPort):
    """Mantem a superficie publica da integracao enquanto ela evolui."""

    def __init__(self, client: CoressoAuthClient | None = None) -> None:
        """Inicializa o adaptador com o client HTTP.

        Args:
            client: Client HTTP concreto a ser usado pelo adaptador. Quando
                omitido, utiliza a implementação padrão do projeto.
        """
        self.client = client or CoressoClient()

    def autenticar(self, rf: str, senha: str) -> CoressoIdentity:
        """Executa autenticacao institucional e normaliza o payload retornado.

        Args:
            rf: Registro funcional enviado pelo usuário.
            senha: Senha institucional enviada pelo usuário.

        Returns:
            Identidade normalizada retornada pelo provedor institucional.

        Raises:
            CoressoContratoError: Quando a resposta nao seguir o contrato
                esperado.
        """
        payload = self.client.autenticar(rf, senha)
        return self._normalizar_identidade(payload)

    def _normalizar_identidade(
        self, payload: dict[str, Any]
    ) -> CoressoIdentity:
        """Converte o payload bruto do CoreSSO em contrato interno tipado."""
        codigo_rf = self._texto_obrigatorio(
            payload.get("codigoRf"), "codigoRf"
        )
        nome = self._texto_obrigatorio(payload.get("nome"), "nome")

        cargos = self._normalizar_cargos(payload.get("cargos"), "cargos")
        cargos_sobrepostos = self._normalizar_cargos(
            payload.get("cargosSobrePosto"),
            "cargosSobrePosto",
        )
        cargos_efetivos = cargos_sobrepostos or cargos

        return CoressoIdentity(
            usuario_id_externo=self._texto_opcional(payload.get("usuarioId")),
            rf=codigo_rf,
            nome=nome,
            email=self._texto_opcional(payload.get("email")),
            cpf=self._texto_opcional(payload.get("numeroDocumento")),
            cargos=cargos,
            cargos_sobrepostos=cargos_sobrepostos,
            cargos_efetivos=cargos_efetivos,
            perfis=self._normalizar_perfis(payload.get("perfis")),
            unidades_lotacao=self._normalizar_unidades(
                payload.get("unidadesLotacao"),
                "unidadesLotacao",
            ),
            unidade_exercicio=self._normalizar_unidade(
                payload.get("unidadeExercicio"),
                "unidadeExercicio",
            ),
            payload_bruto=payload,
        )

    @staticmethod
    def _texto_obrigatorio(valor: object, campo: str) -> str:
        """Extrai texto obrigatório de um campo do payload."""
        if not isinstance(valor, str) or not valor.strip():
            raise CoressoContratoError(f"Campo {campo} ausente ou invalido.")
        return valor.strip()

    @staticmethod
    def _texto_opcional(valor: object) -> str | None:
        """Extrai texto opcional de um campo do payload."""
        if isinstance(valor, str) and valor.strip():
            return valor.strip()
        return None

    @staticmethod
    def _normalizar_perfis(valor: object) -> tuple[str, ...]:
        """Normaliza a lista de perfis retornada pelo CoreSSO."""
        if valor is None:
            return ()
        if not isinstance(valor, list):
            raise CoressoContratoError("Campo perfis ausente ou invalido.")

        perfis: list[str] = []
        for item in valor:
            if isinstance(item, str) and item.strip():
                perfis.append(item.strip())
        return tuple(perfis)

    def _normalizar_cargos(
        self,
        valor: object,
        campo: str,
    ) -> tuple[CargoCoresso, ...]:
        """Normaliza uma lista de cargos do payload do CoreSSO."""
        if valor is None:
            return ()
        if not isinstance(valor, list):
            raise CoressoContratoError(f"Campo {campo} ausente ou invalido.")

        cargos_normalizados: list[CargoCoresso] = []
        for item in valor:
            if not isinstance(item, dict):
                raise CoressoContratoError(
                    f"Item invalido encontrado em {campo}."
                )
            cargos_normalizados.append(
                CargoCoresso(
                    codigo_cargo=self._inteiro_opcional(item.get("codigo")),
                    descricao_cargo=self._texto_opcional(item.get("nome"))
                    or "",
                )
            )
        return tuple(cargos_normalizados)

    def _normalizar_unidades(
        self,
        valor: object,
        campo: str,
    ) -> tuple[UnidadeCoresso, ...]:
        """Normaliza a lista de unidades do payload do CoreSSO."""
        if valor is None:
            return ()
        if not isinstance(valor, list):
            raise CoressoContratoError(f"Campo {campo} ausente ou invalido.")

        unidades: list[UnidadeCoresso] = []
        for item in valor:
            if not isinstance(item, dict):
                raise CoressoContratoError(
                    f"Item invalido encontrado em {campo}."
                )
            unidades.append(
                UnidadeCoresso(
                    codigo=self._texto_opcional(item.get("codigo")) or "",
                    nome_unidade=self._texto_opcional(item.get("nomeUnidade"))
                    or "",
                )
            )
        return tuple(unidades)

    def _normalizar_unidade(
        self,
        valor: object,
        campo: str,
    ) -> UnidadeCoresso | None:
        """Normaliza um objeto de unidade unica do payload do CoreSSO."""
        if valor is None:
            return None
        if not isinstance(valor, dict):
            raise CoressoContratoError(f"Campo {campo} ausente ou invalido.")

        return UnidadeCoresso(
            codigo=self._texto_opcional(valor.get("codigo")) or "",
            nome_unidade=self._texto_opcional(valor.get("nomeUnidade")) or "",
        )

    @staticmethod
    def _inteiro_opcional(valor: object) -> int | None:
        """Converte um valor numérico textual para inteiro quando possível."""
        if valor is None or valor == "":
            return None
        if isinstance(valor, bool):
            return None
        if isinstance(valor, int):
            return valor
        if isinstance(valor, str):
            try:
                return int(valor)
            except ValueError:
                return None
        return None
