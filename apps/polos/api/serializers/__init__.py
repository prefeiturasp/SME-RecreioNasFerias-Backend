"""Serializers HTTP do app `polos`."""

from apps.polos.api.serializers.dre_serializer import DreSerializer
from apps.polos.api.serializers.polo_serializer import PoloSerializer
from apps.polos.api.serializers.popular_polos_serializer import (
    PopularUnidadesDiretasSerializer,
)
from apps.polos.api.serializers.tipo_escola_serializer import (
    TipoEscolaSerializer,
)

__all__ = [
    "DreSerializer",
    "PoloSerializer",
    "PopularUnidadesDiretasSerializer",
    "TipoEscolaSerializer",
]
