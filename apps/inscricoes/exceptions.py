"""Exceções de negócio do domínio de inscrições."""


class InscricaoExistenteError(Exception):
    """Indica que o participante já possui inscrição na edição vigente."""
