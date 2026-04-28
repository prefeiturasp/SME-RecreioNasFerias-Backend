from django.urls import path
from .views import create_user

urlpatterns = [path("usuarios/", create_user)]
