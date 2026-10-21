"""Choices do domínio de inscrições."""

from django.db import models


class GrupoInscricao(models.TextChoices):
    """Grupos de atendimento disponíveis para a inscrição."""

    BERCARIO_I = "BERCARIO_I", "Berçário I"
    BERCARIO_II = "BERCARIO_II", "Berçário II"
    MINI_GRUPO_I = "MINI_GRUPO_I", "Mini Grupo I"
    MINI_GRUPO_II = "MINI_GRUPO_II", "Mini Grupo II"
    QUATRO_A_14_ANOS = "QUATRO_A_14_ANOS", "4 a 14 anos"


class TipoEstudante(models.TextChoices):
    """Origem escolar do participante."""

    ESTUDANTE_DA_REDE = "ESTUDANTE_DA_REDE", "Estudante da rede"
    ESTUDANTE_EXTERNO = "ESTUDANTE_EXTERNO", "Estudante externo"


class StatusInscricao(models.TextChoices):
    """Estados do ciclo de vida da inscrição."""

    RASCUNHO = "RASCUNHO", "Rascunho"
    COMPLETA = "COMPLETA", "Completa"
    CANCELADA = "CANCELADA", "Cancelada"


class Deficiencias(models.TextChoices):
    """Tipos de deficiências que um participante pode ter."""

    ALTAS_HABILIDADES = "ALTAS_HABILIDADES", "Altas Habilidades / Superdotação"
    AUTISMO = "AUTISMO", "Autismo"
    BAIXA_VISAO = "BAIXA_VISAO_OU_VISAO_SUBNORMAL", "Baixa Visão / Visão Subnormal"
    CEGUEIRA = "CEGUEIRA", "Cegueira"
    CADEIRANTE = "CADEIRANTE", "Deficiência Física Cadeirante"
    NAO_CADEIRANTE = "NAO_CADEIRANTE", "Deficiência Física Não Cadeirante"
    DEFICIENCIA_INTELECTUAL = "DEFICIENCIA_INTELECTUAL", "Deficiência Intelectual"
    SINDROME_ASPERGER = "SINDROME_ASPERGER", "Síndrome de Asperger"
    SINDROME_RETT = "SINDROME_RETT", "Síndrome de Rett"
    SURDEZ_LEVE_OU_MODERADA = "SURDEZ_LEVE_OU_MODERADA", "Surdez Leve / Moderada"
    SURDEZ_SEVERA_OU_PROFUNDA = "SURDEZ_SEVERA_OU_PROFUNDA", "Surdez Severa / Profunda"
    SURDOCEGUEIRA = "SURDOCEGUEIRA", "Surdocegueira"
    TRANSTORNO_DESINTEGRATIVO_INFANCIA = "TRANSTORNO_DESINTEGRATIVO_INFANCIA", "Transtorno Desintegrativo da Infância"
    OUTRA = "OUTRA", "Outra"

class ProblemasSaude(models.TextChoices):
    """Tipos de problemas de saúde que um participante pode ter."""

    ANEMIA = "ANEMIA", "Anemia"
    ASMA_OU_BRONQUITE = "ASMA_OU_BRONQUITE", "Asma / Bronquite"
    DIABETES = "DIABETES", "Diabetes"
    DESNUTRICAO = "DESNUTRICAO", "Desnutrição"
    PROBLEMA_CARDIACO = "PROBLEMA_CARDIACO", " Problema Cardíaco"
    PROBLEMA_DIGESTIVO = "PROBLEMA_DIGESTIVO", "Problema Digestivo"
    PROBLEMA_NEUROLOGICO = "PROBLEMA_NEUROLOGICO", "Problema Neurológico"
    DOENCA_CELIACA = "DOENCA_CELIACA", "Doença Celíaca"
    FENILCETONURIA = "FENILCETONURIA", "Fenilcetonúria"
    OBESIDADE = "OBESIDADE", "Obesidade"
    OUTRO = "OUTRO", "Outro"
