"""
Sincronização de unidades diretas da SME Integração na tabela ``polos``.

Busca unidades elegíveis ao Recreio nas Férias, compara com os polos de gestão
Direta já persistidos (por código EOL) e grava apenas as unidades novas.
Persiste em lotes para não perder progresso em falhas pontuais da integração.

A sincronização automática roda no máximo uma vez por dia (fuso de São Paulo),
salvo quando ``forcar=True``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from infrastructure.services.escolas_integracao_service import EscolasIntegracaoService
from polos.models import (
    CHAVE_SINCRONIZACAO_UNIDADES_DIRETAS,
    GESTAO_DIRETA,
    NOME_EDICAO_SEM_VINCULO,
    QUANTIDADE_MAXIMA_ALUNOS_PADRAO_DIRETA,
    STATUS_ATIVO,
    TIPO_POLO_PENDENTE,
    ControleSincronizacaoPolos,
    Polo,
)

_TAMANHO_LOTE_SINCRONIZACAO = 40
_FUSO_SINCRONIZACAO = ZoneInfo("America/Sao_Paulo")
MOTIVO_JA_EXECUTADA_HOJE = "ja_executada_hoje"


@dataclass(frozen=True)
class ResultadoSincronizacaoUnidadesDiretas:
    """Resultado da sincronização de unidades diretas.

    Attributes:
        total_consultados: Unidades retornadas/filtradas na integração.
        total_novos: Quantidade de polos efetivamente criados.
        total_ja_existentes: Unidades da integração já presentes no banco.
        polos_criados: Instâncias persistidas nesta execução.
        executada: Indica se a sync consultou a SME nesta chamada.
        motivo_ignorada: Motivo quando a sync foi pulada por frequência.
        ultima_execucao_em: Instante da última sync registrada (se houver).
    """

    total_consultados: int
    total_novos: int
    total_ja_existentes: int
    polos_criados: list[Polo]
    executada: bool = True
    motivo_ignorada: str | None = None
    ultima_execucao_em: datetime | None = None


def _agora_sincronizacao() -> datetime:
    """Retorna o instante atual no fuso usado para o limite diário."""
    return timezone.now().astimezone(_FUSO_SINCRONIZACAO)


def _obter_controle_sincronizacao() -> ControleSincronizacaoPolos | None:
    """Busca o registro de controle da sync de unidades diretas."""
    return ControleSincronizacaoPolos.objects.filter(
        chave=CHAVE_SINCRONIZACAO_UNIDADES_DIRETAS,
    ).first()


def _ja_sincronizou_hoje(controle: ControleSincronizacaoPolos | None) -> bool:
    """Indica se já houve sync bem-sucedida no dia corrente (SP)."""
    if controle is None:
        return False
    ultima = controle.ultima_execucao_em.astimezone(_FUSO_SINCRONIZACAO)
    return ultima.date() == _agora_sincronizacao().date()


def _registrar_sincronizacao_executada() -> datetime:
    """Persiste (ou atualiza) o instante da sync concluída com sucesso."""
    agora = timezone.now()
    ControleSincronizacaoPolos.objects.update_or_create(
        chave=CHAVE_SINCRONIZACAO_UNIDADES_DIRETAS,
        defaults={"ultima_execucao_em": agora},
    )
    return agora


def _normalizar_codigo_eol(codigo: object) -> str:
    """Normaliza código EOL para comparação e persistência."""
    return str(codigo or "").strip()


def _eols_diretos_existentes() -> set[str]:
    """Retorna os códigos EOL já salvos com gestão Direta."""
    return {
        codigo
        for codigo in Polo.objects.filter(gestao=GESTAO_DIRETA)
        .exclude(codigo_eol__isnull=True)
        .exclude(codigo_eol="")
        .values_list("codigo_eol", flat=True)
        if codigo
    }


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


def _mapear_unidade_para_polo(unidade: dict[str, Any]) -> Polo:
    """Converte payload enriquecido da integração em instância ``Polo``."""
    codigo_eol = _normalizar_codigo_eol(unidade.get("codigoEol"))
    nome_escola = str(unidade.get("nomeEscola") or "").strip()
    telefone = str(unidade.get("telefone") or "").strip()[:20]
    dre = str(unidade.get("nomeDre") or unidade.get("siglaDre") or "").strip()
    tipo_ue = str(unidade.get("siglaTipoEscola") or "").strip()

    return Polo(
        tipo=TIPO_POLO_PENDENTE,
        gestao=GESTAO_DIRETA,
        codigo_eol=codigo_eol,
        nome_osc="",
        nome_polo=_resolver_nome_polo(nome_escola, codigo_eol),
        dre=dre or "Não informado",
        tipo_ue=tipo_ue or "Não informado",
        quantidade_maxima_alunos=QUANTIDADE_MAXIMA_ALUNOS_PADRAO_DIRETA,
        cep=str(unidade.get("cep") or "").strip(),
        endereco=str(unidade.get("endereco") or "").strip(),
        nome_gestor=str(unidade.get("nomeDiretor") or "").strip(),
        email_polo=str(unidade.get("email") or "").strip(),
        telefone_polo=telefone,
        status=STATUS_ATIVO,
        nome_edicao=NOME_EDICAO_SEM_VINCULO,
        observacoes_gerais="",
    )


def _persistir_lote(
    unidades_enriquecidas: list[dict[str, Any]],
    eols_atuais: set[str],
) -> list[Polo]:
    """Persiste um lote de unidades novas e atualiza o conjunto de EOLs."""
    polos_criados: list[Polo] = []
    with transaction.atomic():
        for unidade in unidades_enriquecidas:
            codigo_eol = _normalizar_codigo_eol(unidade.get("codigoEol"))
            if not codigo_eol or codigo_eol in eols_atuais:
                continue
            try:
                polo = _mapear_unidade_para_polo(unidade)
                polo.save()
            except ValidationError:
                continue
            polos_criados.append(polo)
            eols_atuais.add(codigo_eol)
    return polos_criados


def sincronizar_unidades_diretas(
    *,
    servico: EscolasIntegracaoService | None = None,
    limite: int | None = None,
    forcar: bool = False,
) -> ResultadoSincronizacaoUnidadesDiretas:
    """Sincroniza unidades diretas novas na tabela ``polos``.

    Fluxo:
        1. Se já rodou hoje (e ``forcar`` é falso), retorna sem consultar a SME.
        2. Lista unidades elegíveis na SME Integração (filtradas).
        3. Compara com polos ``gestao=Direta`` pelo ``codigo_eol``.
        4. Enriquece e persiste em lotes apenas unidades ainda inexistentes.
        5. Registra a execução bem-sucedida para o limite diário.

    Args:
        servico: Cliente da integração; cria um novo se omitido.
        limite: Limite opcional de unidades filtradas antes do diff (testes).
        forcar: Quando ``True``, ignora o limite de uma execução por dia.

    Returns:
        ResultadoSincronizacaoUnidadesDiretas: Totais e polos criados.
    """
    controle = _obter_controle_sincronizacao()
    if not forcar and _ja_sincronizou_hoje(controle):
        return ResultadoSincronizacaoUnidadesDiretas(
            total_consultados=0,
            total_novos=0,
            total_ja_existentes=0,
            polos_criados=[],
            executada=False,
            motivo_ignorada=MOTIVO_JA_EXECUTADA_HOJE,
            ultima_execucao_em=(
                controle.ultima_execucao_em if controle is not None else None
            ),
        )

    cliente = servico or EscolasIntegracaoService()
    unidades_filtradas = cliente.filtrar_unidades_recreio(
        cliente.listar_todas_unidades(),
    )
    if limite is not None:
        unidades_filtradas = unidades_filtradas[: max(0, limite)]

    total_consultados = len(unidades_filtradas)
    eols_existentes = _eols_diretos_existentes()

    unidades_novas_basicas = [
        unidade
        for unidade in unidades_filtradas
        if (
            (_eol := _normalizar_codigo_eol(unidade.get("codigoEscola")))
            and _eol not in eols_existentes
        )
    ]
    total_ja_existentes = total_consultados - len(unidades_novas_basicas)

    if not unidades_novas_basicas:
        executada_em = _registrar_sincronizacao_executada()
        return ResultadoSincronizacaoUnidadesDiretas(
            total_consultados=total_consultados,
            total_novos=0,
            total_ja_existentes=total_ja_existentes,
            polos_criados=[],
            executada=True,
            motivo_ignorada=None,
            ultima_execucao_em=executada_em,
        )

    polos_criados: list[Polo] = []
    eols_atuais = set(eols_existentes)

    for inicio in range(0, len(unidades_novas_basicas), _TAMANHO_LOTE_SINCRONIZACAO):
        lote = unidades_novas_basicas[inicio : inicio + _TAMANHO_LOTE_SINCRONIZACAO]
        unidades_enriquecidas = cliente.enriquecer_unidades(lote)
        polos_criados.extend(_persistir_lote(unidades_enriquecidas, eols_atuais))

    executada_em = _registrar_sincronizacao_executada()
    return ResultadoSincronizacaoUnidadesDiretas(
        total_consultados=total_consultados,
        total_novos=len(polos_criados),
        total_ja_existentes=total_ja_existentes,
        polos_criados=polos_criados,
        executada=True,
        motivo_ignorada=None,
        ultima_execucao_em=executada_em,
    )
