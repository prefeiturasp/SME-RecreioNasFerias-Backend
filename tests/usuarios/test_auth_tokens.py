from django.contrib.auth import get_user_model
from django.test import TestCase

from usuarios.auth_tokens import gerar_token_acesso, resolver_usuario_por_token

Usuario = get_user_model()


class AuthTokensTests(TestCase):
    def test_token_resolve_usuario_ativo(self):
        usuario = Usuario.objects.create(
            rf="9988776",
            email="9988776@test.local",
            is_active=True,
        )
        usuario.set_unusable_password()
        usuario.save()

        token = gerar_token_acesso(usuario)
        resolvido = resolver_usuario_por_token(token)

        self.assertIsNotNone(resolvido)
        self.assertEqual(resolvido.pk, usuario.pk)
        self.assertEqual(resolvido.rf, "9988776")

    def test_token_invalido_retorna_none(self):
        self.assertIsNone(resolver_usuario_por_token("token-invalido"))
