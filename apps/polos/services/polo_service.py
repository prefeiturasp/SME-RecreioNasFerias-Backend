"""Casos de uso do domínio de polos."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q, QuerySet
from django.utils import timezone

from apps.integracoes.eol.adapter import EolAdapter
from apps.integracoes.eol.port import (
    DreEol,
    EolPort,
    TipoEscolaEol,
    UnidadeEol,
    UnidadeRecreioEol,
)
from apps.polos.constants import (
    CHAVE_POPULAR_UNIDADES_DIRETAS,
    MOTIVO_JA_EXECUTADA_HOJE,
    NOME_OSC_SEM_VINCULO,
    QUANTIDADE_MAXIMA_ALUNOS_PADRAO_DIRETA,
    TAMANHO_LOTE_POPULAR_UNIDADES_DIRETAS,
    GestaoPolo,
    StatusPolo,
    TipoPolo,
)
from apps.polos.models import ControleSincronizacaoPolos, Polo

_FUSO_POPULAR = ZoneInfo("America/Sao_Paulo")
_DRE_NAO_INFORMADA = "Não informado"
_TIPO_UE_NAO_INFORMADO = "Não informado"


@dataclass(frozen=True)
class ResultadoPopularUnidadesDiretas:
    """Resultado da população de polos de gestão direta."""

    total_consultados: int
    total_novos: int
    total_ja_existentes: int
    polos_criados: list[Polo]
    executada: bool = True
    motivo_ignorada: str | None = None
    ultima_execucao_em: datetime | None = None


def _normalizar(valor: str | None) -> str:
    """Remove espaços nas bordas, tratando valores ausentes como vazios."""
    return (valor or "").strip()


class PoloService:
    """Orquestra criação, consulta e alteração de polos."""

    def __init__(self, eol: EolPort | None = None) -> None:
        """Inicializa o serviço adiando a criação da integração EOL."""
        self._eol = eol

    @property
    def eol(self) -> EolPort:
        """Cria a integração EOL apenas quando ela é efetivamente usada."""
        if self._eol is None:
            self._eol = EolAdapter()
        return self._eol

    def listar_tipos_escola(self) -> tuple[TipoEscolaEol, ...]:
        """Lista tipos de escola normalizados pela integração EOL."""
        return self.eol.listar_tipos_escola()

    def listar_dres(self) -> tuple[DreEol, ...]:
        """Lista DREs normalizadas pela integração EOL."""
        return self.eol.listar_dres()

    def listar(
        self,
        *,
        dre_codigo_eol: str | None = None,
        tipo_ue: str | None = None,
        busca: str | None = None,
    ) -> QuerySet[Polo]:
        """Lista polos aplicando os filtros informados."""
        consulta = Polo.objects.all()

        dre_codigo_eol = _normalizar(dre_codigo_eol)
        if dre_codigo_eol:
            consulta = consulta.filter(dre_codigo_eol=dre_codigo_eol)

        tipo_ue = _normalizar(tipo_ue)
        if tipo_ue:
            consulta = consulta.filter(tipo_ue=tipo_ue)

        busca = _normalizar(busca)
        if busca:
            consulta = consulta.filter(
                Q(nome_polo__icontains=busca) | Q(nome_osc__icontains=busca)
            )

        return consulta

    def obter(self, uuid: object) -> Polo:
        """Obtém um polo pelo UUID público."""
        return Polo.objects.get(uuid=uuid)

    @transaction.atomic
    def criar(self, **dados: Any) -> Polo:
        """Cria um polo sempre pendente e ativo."""
        dados.pop("tipo", None)
        dados.pop("status", None)
        polo = Polo(
            tipo=TipoPolo.PENDENTE,
            status=StatusPolo.ATIVO,
            **dados,
        )
        polo.save()
        return polo

    @transaction.atomic
    def atualizar(self, polo: Polo, **dados: Any) -> Polo:
        """Atualiza um polo e reaplica as validações do domínio."""
        dados.pop("ativo", None)
        for campo, valor in dados.items():
            setattr(polo, campo, valor)
        polo.save()
        return polo

    @transaction.atomic
    def excluir(self, polo: Polo) -> None:
        """Exclui um polo cadastrado."""
        polo.delete()

    def popular_unidades_diretas(self) -> ResultadoPopularUnidadesDiretas:
        """Cria polos diretos a partir das unidades elegíveis da EOL.

        Consulta o catálogo, compara pelo código EOL apenas com polos de
        gestão direta e enriquece somente as unidades ainda inexistentes.
        A carga roda no máximo uma vez por dia no fuso de São Paulo.
        """
        controle = self._obter_controle_popular()
        if self._ja_populou_hoje(controle):
            return ResultadoPopularUnidadesDiretas(
                total_consultados=0,
                total_novos=0,
                total_ja_existentes=0,
                polos_criados=[],
                executada=False,
                motivo_ignorada=MOTIVO_JA_EXECUTADA_HOJE,
                ultima_execucao_em=(
                    controle.ultima_execucao_em
                    if controle is not None
                    else None
                ),
            )

        filtradas = self.eol.filtrar_unidades_recreio(
            self.eol.listar_todas_unidades()
        )
        eols_existentes = self._eols_diretos_existentes()
        novas: list[UnidadeEol] = []
        for unidade in filtradas:
            codigo = self._normalizar_codigo_eol(unidade.codigo_eol)
            if codigo and codigo not in eols_existentes:
                novas.append(unidade)
        total_consultados = len(filtradas)
        total_ja_existentes = total_consultados - len(novas)

        if not novas:
            executada_em = self._registrar_popular_executado()
            return ResultadoPopularUnidadesDiretas(
                total_consultados=total_consultados,
                total_novos=0,
                total_ja_existentes=total_ja_existentes,
                polos_criados=[],
                ultima_execucao_em=executada_em,
            )

        polos_criados: list[Polo] = []
        eols_atuais = set(eols_existentes)
        tamanho_lote = TAMANHO_LOTE_POPULAR_UNIDADES_DIRETAS
        for inicio in range(0, len(novas), tamanho_lote):
            lote = novas[inicio : inicio + tamanho_lote]
            enriquecidas = self.eol.enriquecer_unidades(lote)
            polos_criados.extend(
                self._persistir_lote(enriquecidas, eols_atuais)
            )

        executada_em = self._registrar_popular_executado()
        return ResultadoPopularUnidadesDiretas(
            total_consultados=total_consultados,
            total_novos=len(polos_criados),
            total_ja_existentes=total_ja_existentes,
            polos_criados=polos_criados,
            ultima_execucao_em=executada_em,
        )

    @staticmethod
    def _obter_controle_popular() -> ControleSincronizacaoPolos | None:
        """Busca o registro de controle da população de unidades diretas."""
        return ControleSincronizacaoPolos.objects.filter(
            chave=CHAVE_POPULAR_UNIDADES_DIRETAS,
        ).first()

    @staticmethod
    def _ja_populou_hoje(
        controle: ControleSincronizacaoPolos | None,
    ) -> bool:
        """Indica se a carga já rodou no dia corrente em São Paulo."""
        if controle is None:
            return False
        ultima = controle.ultima_execucao_em.astimezone(_FUSO_POPULAR)
        agora = timezone.now().astimezone(_FUSO_POPULAR)
        return ultima.date() == agora.date()

    @staticmethod
    def _registrar_popular_executado() -> datetime:
        """Persiste o instante da carga concluída com sucesso."""
        agora = timezone.now()
        ControleSincronizacaoPolos.objects.update_or_create(
            chave=CHAVE_POPULAR_UNIDADES_DIRETAS,
            defaults={"ultima_execucao_em": agora},
        )
        return agora

    @staticmethod
    def _normalizar_codigo_eol(codigo: object) -> str:
        """Normaliza o código EOL para comparação e persistência."""
        return str(codigo or "").strip()

    @staticmethod
    def _eols_diretos_existentes() -> set[str]:
        """Retorna os códigos EOL já salvos com gestão direta."""
        return {
            codigo
            for codigo in Polo.objects.filter(gestao=GestaoPolo.DIRETA)
            .exclude(codigo_eol="")
            .values_list("codigo_eol", flat=True)
            if codigo
        }

    @staticmethod
    def _resolver_nome_polo(nome_escola: str, codigo_eol: str) -> str:
        """Define nome único do polo, anexando o EOL em caso de colisão."""
        nome_base = (nome_escola or "").strip() or f"Unidade {codigo_eol}"
        if not Polo.objects.filter(nome_polo__iexact=nome_base).exists():
            return nome_base

        nome_com_eol = f"{nome_base} ({codigo_eol})"
        if not Polo.objects.filter(nome_polo__iexact=nome_com_eol).exists():
            return nome_com_eol

        sufixo = 2
        while True:
            candidato = f"{nome_base} ({codigo_eol}-{sufixo})"
            if not Polo.objects.filter(nome_polo__iexact=candidato).exists():
                return candidato
            sufixo += 1

    def _mapear_unidade(self, unidade: UnidadeRecreioEol) -> Polo:
        """Converte a unidade enriquecida em um polo de gestão direta."""
        codigo_eol = self._normalizar_codigo_eol(unidade.codigo_eol)
        dre_nome = (
            unidade.nome_dre.strip()
            or unidade.sigla_dre.strip()
            or _DRE_NAO_INFORMADA
        )
        return Polo(
            codigo_eol=codigo_eol,
            nome_polo=self._resolver_nome_polo(
                unidade.nome_escola,
                codigo_eol,
            ),
            nome_osc=NOME_OSC_SEM_VINCULO,
            dre_nome=dre_nome,
            dre_codigo_eol=(
                unidade.codigo_dre.strip() or _DRE_NAO_INFORMADA
            ),
            gestao=GestaoPolo.DIRETA,
            tipo=TipoPolo.PENDENTE,
            status=StatusPolo.ATIVO,
            tipo_ue=(
                unidade.sigla_tipo_escola.strip() or _TIPO_UE_NAO_INFORMADO
            ),
            quantidade_maxima_alunos=QUANTIDADE_MAXIMA_ALUNOS_PADRAO_DIRETA,
            cep=unidade.cep.strip(),
            tipo_logradouro=unidade.tipo_logradouro.strip(),
            logradouro=unidade.logradouro.strip(),
            bairro=unidade.bairro.strip(),
            numero=unidade.numero.strip(),
            complemento=unidade.complemento.strip(),
            nome_gestor=unidade.nome_diretor.strip(),
            email=unidade.email.strip(),
            telefone=unidade.telefone.strip()[:30],
        )

    def _persistir_lote(
        self,
        unidades: tuple[UnidadeRecreioEol, ...] | list[UnidadeRecreioEol],
        eols_atuais: set[str],
    ) -> list[Polo]:
        """Persiste um lote de unidades novas e atualiza os EOLs vistos."""
        polos_criados: list[Polo] = []
        with transaction.atomic():
            for unidade in unidades:
                codigo_eol = self._normalizar_codigo_eol(unidade.codigo_eol)
                if not codigo_eol or codigo_eol in eols_atuais:
                    continue
                try:
                    polo = self._mapear_unidade(unidade)
                    polo.save()
                except ValidationError:
                    continue
                polos_criados.append(polo)
                eols_atuais.add(codigo_eol)
        return polos_criados
