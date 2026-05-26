"""
Camada de aplicação do backend SME Recreio nas Férias.

Orquestra casos de uso, DTOs de entrada/saída, validações e serviços
de apoio (RBAC, validador de login). Não depende de Django diretamente;
a persistência e integrações externas são acessadas via portas do domínio
implementadas na camada de infraestrutura.
"""
