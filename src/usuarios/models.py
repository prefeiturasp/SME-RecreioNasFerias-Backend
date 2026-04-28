from django.db import models


class UserModel(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    nome = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    class Meta:
        db_table = "usuarios"
