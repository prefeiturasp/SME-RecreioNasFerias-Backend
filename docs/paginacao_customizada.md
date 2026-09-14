# Paginação Customizada - Guia de Uso

## Visão Geral

A classe `PaginacaoCustomizada` foi criada para ser reutilizada em todas as Views e ViewSets do projeto. Ela oferece:

- ✅ Configuração dinâmica de quantidade de registros por página
- ✅ Opção de desabilitar paginação para retornar todos os registros
- ✅ Funcionamento em ViewSets (ModelViewSet, ViewSet)
- ✅ Funcionamento em @actions dentro de Views
- ✅ Parametrização via query parameters

---

## Localização

```
apps/core/utils/paginacao_customizada.py
```

---

## Como Usar

### 1️⃣ Em ViewSets (Forma Mais Simples)

```python
from apps.core.utils.paginacao_customizada import PaginacaoCustomizada
from rest_framework import viewsets

class MeuViewSet(viewsets.ModelViewSet):
    queryset = MinhaClasse.objects.all()
    serializer_class = MeuSerializer
    pagination_class = PaginacaoCustomizada
```

**Requisições:**

```bash
# Listar com paginação padrão (10 registros por página)
GET /api/meu-endpoint/?page=1

# Listar com 20 registros por página
GET /api/meu-endpoint/?page=1&page_size=20

# Listar todos os registros sem paginação
GET /api/meu-endpoint/?desabilita_paginacao=true
```

---

### 2️⃣ Em @Actions Customizadas

```python
from apps.core.utils.paginacao_customizada import PaginacaoCustomizada
from rest_framework.decorators import action
from rest_framework.response import Response

class MeuViewSet(viewsets.ModelViewSet):
    
    @action(detail=False, methods=['get'])
    def meu_endpoint_customizado(self, request):
        """Exemplo de uso em @action."""
        # Obter dados
        queryset = MinhaClasse.objects.all()
        
        # Verificar se desabilita paginação
        desabilita_paginacao = request.query_params.get(
            "desabilita_paginacao", "false"
        ).lower() == "true"
        
        # Instanciar paginação
        paginacao = PaginacaoCustomizada(
            page_size=10,  # Opcional: padrão é 10
            desabilita_paginacao=desabilita_paginacao
        )
        
        # Paginar queryset
        resultado = paginacao.paginate_queryset(
            queryset, request, view=self
        )
        
        # Serializar dados
        serializer = MeuSerializer(resultado, many=True)
        
        # Retornar resposta
        if desabilita_paginacao:
            return Response(serializer.data)
        
        return paginacao.get_paginated_response(serializer.data)
```

---

### 3️⃣ Com Configurações Customizadas

```python
# Página com 50 registros
paginacao = PaginacaoCustomizada(page_size=50)

# Página com todos os registros (sem paginação)
paginacao = PaginacaoCustomizada(desabilita_paginacao=True)

# Página com 30 registros e sem paginação (desabilita_paginacao tem prioridade)
paginacao = PaginacaoCustomizada(page_size=30, desabilita_paginacao=True)
```

---

## Exemplos de Requisições

### Exemplo 1: Paginação Padrão

```bash
curl -X GET "http://localhost:8000/api/meus-dados/?page=1"
```

**Resposta:**
```json
{
    "count": 100,
    "next": "http://localhost:8000/api/meus-dados/?page=2",
    "previous": null,
    "results": [
        { "id": 1, "nome": "Item 1" },
        { "id": 2, "nome": "Item 2" },
        ...
    ]
}
```

---

### Exemplo 2: Sem Paginação

```bash
curl -X GET "http://localhost:8000/api/meus-dados/?desabilita_paginacao=true"
```

**Resposta:**
```json
[
    { "id": 1, "nome": "Item 1" },
    { "id": 2, "nome": "Item 2" },
    ...
    { "id": 100, "nome": "Item 100" }
]
```

---

### Exemplo 3: Página Customizada

```bash
curl -X GET "http://localhost:8000/api/meus-dados/?page=2&page_size=25"
```

**Resposta:**
```json
{
    "count": 100,
    "next": "http://localhost:8000/api/meus-dados/?page=3&page_size=25",
    "previous": "http://localhost:8000/api/meus-dados/?page=1&page_size=25",
    "results": [
        { "id": 26, "nome": "Item 26" },
        { "id": 27, "nome": "Item 27" },
        ...
    ]
}
```

---

## Parâmetros de Query

| Parâmetro | Tipo | Descrição | Padrão |
|-----------|------|-----------|--------|
| `page` | INT | Número da página | 1 |
| `page_size` | INT | Registros por página | 10 |
| `desabilita_paginacao` | BOOL | Retorna todos sem paginação | false |

---

## Implementações Atuais

✅ **Já Implementado em:**
- `apps/definicoes_polos/api/views/definicao_polo_viewset.py` - Paginação em ViewSet e @action `historico`

---

## Boas Práticas

1. **Sempre use em ViewSets:** Para reduzir duplicação de código
2. **Valide os dados:** Sempre valide o filtro de `desabilita_paginacao`
3. **Documente os endpoints:** Indique no schema OpenAPI quando há paginação
4. **Considere performance:** Para grandes volumes, evite desabilitar paginação
5. **Teste os limites:** Verifique `max_page_size = 1000` se necessário aumentar

---

## Dúvidas Frequentes

**P: Posso mudar o page_size em tempo de execução?**
R: Sim! Via query parameter `page_size` ou ao instanciar a classe com `page_size=X`.

**P: O que acontece se eu usar `page_size` + `desabilita_paginacao=true`?**
R: A paginação é desabilitada completamente e `page_size` é ignorado.

**P: Funciona com queryset complexos?**
R: Sim! Funciona com qualquer QuerySet do Django, após aplicar filtros.

---

## Referências

- [Django REST Framework - Pagination](https://www.django-rest-framework.org/api-guide/pagination/)
- [Django - QuerySets](https://docs.djangoproject.com/en/stable/ref/models/querysets/)
