from django.test import TestCase

from common.models import ModeloAtualizavel, ModeloBase


class ModeloBaseTests(TestCase):
    def test_modelo_base_e_abstrato(self):
        self.assertTrue(ModeloBase._meta.abstract)

    def test_modelo_base_define_timestamps(self):
        field_names = {f.name for f in ModeloBase._meta.get_fields()}
        self.assertIn("criado_em", field_names)
        self.assertIn("atualizado_em", field_names)

    def test_modelo_atualizavel_e_abstrato(self):
        self.assertTrue(ModeloAtualizavel._meta.abstract)

    def test_modelo_atualizavel_so_atualizado_em(self):
        field_names = {f.name for f in ModeloAtualizavel._meta.get_fields()}
        self.assertIn("atualizado_em", field_names)
        self.assertNotIn("criado_em", field_names)
