from django.contrib import admin
from .models import Usuario, CargoPermitido, LogLogin

admin.site.register(Usuario)

admin.site.register(CargoPermitido)

admin.site.register(LogLogin)
