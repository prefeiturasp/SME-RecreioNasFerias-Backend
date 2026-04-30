from django.urls import path
from .views import users

urlpatterns = [path("usuarios/", users)]
