import re
from typing import Any, Dict, List
from apps.inscricoes.constants import (
    GrupoInscricao,
    TipoEstudante,
    StatusInscricao,
)


class ValoresChoices:
    def __init__(self):
        self.snake_case_regex = re.compile(r"(?<!^)(?=[A-Z])")

    def to_snake_case(self, name: str) -> str:
        """Converte nomes CamelCase para snake_case."""
        return self.snake_case_regex.sub("_", name).lower()

    def format_choice(self, choice: Any) -> Dict[str, str]:
        """Formata um choice para dicionário com value e label."""
        return {"value": choice.value, "label": choice.label}

    def get_values_inscricoes_choices(self) -> Dict[str, List[Dict[str, str]]]:
        """Retorna um dicionário com os valores de todas os choices do domínio de inscrições.

        Returns:
            Dict mapeando nomes de choice classes (snake_case) para listas de dicionários
            contendo 'value' e 'label' de cada opção.
        """
        choices_classes = [GrupoInscricao, TipoEstudante, StatusInscricao]

        return {
            self.to_snake_case(cls.__name__): [
                self.format_choice(choice) for choice in cls
            ]
            for cls in choices_classes
        }
