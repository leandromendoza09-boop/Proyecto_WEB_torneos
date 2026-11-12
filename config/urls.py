"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from torneos.views import (
    consultar_inscripcion,
    detalle_torneo,
    gestionar_torneo,
    lista_torneos,
    panel_organizador,
    cancelar_inscripcion,
    crear_torneo,
    editar_inscripcion,
)
from django.contrib.auth.views import LoginView, LogoutView


urlpatterns = [
    path('admin/', admin.site.urls),
    path("", lista_torneos, name="lista_torneos"),
    path("torneos/<int:torneo_id>/", detalle_torneo, name="detalle_torneo"),
    path("inscripciones/<uuid:codigo_consulta>/", consultar_inscripcion, name="consultar_inscripcion"),
    path(
        "organizador/ingresar/",
        LoginView.as_view(
            template_name="torneos/ingreso_organizador.html",
            next_page="panel_organizador",
        ),
        name="ingreso_organizador",
    ),
    path("organizador/", panel_organizador, name="panel_organizador"),
    path(
        "organizador/torneos/<int:torneo_id>/",
        gestionar_torneo,
        name="gestionar_torneo",
    ),
    path(
        "organizador/inscripciones/<int:inscripcion_id>/cancelar/",
        cancelar_inscripcion,
        name="cancelar_inscripcion",
    ),
    path("organizador/torneos/crear/", crear_torneo, name="crear_torneo"),
    path(
        "organizador/inscripciones/<int:inscripcion_id>/editar/",
        editar_inscripcion,
        name="editar_inscripcion",
    ),   
    path(
        "organizador/salir/",
        LogoutView.as_view(next_page="lista_torneos"),
        name="salir_organizador",
    ),
]
