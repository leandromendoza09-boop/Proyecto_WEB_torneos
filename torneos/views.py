from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from .models import Torneo, Inscripcion, Organizador
from .forms import InscripcionForm, TorneoForm
from django.core.exceptions import ValidationError
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator


# Le pedimos a django que nos devuelva todos los torneos ordenados por fecha y nombre

def lista_torneos(request):
    torneos = Torneo.objects.order_by("fecha_evento", "nombre")

    return render(
        request,
        "torneos/lista_torneos.html",
        {"torneos": torneos},
    )
def detalle_torneo(request, torneo_id):
    torneo = get_object_or_404(Torneo, pk=torneo_id)
    formulario = InscripcionForm(
        request.POST if request.method == "POST" else None,
        torneo=torneo,
    )
    

    if request.method == "POST" and formulario.is_valid():
        inscripcion = Inscripcion(**formulario.cleaned_data)

        try:
            inscripcion.full_clean()
        except ValidationError as error:
            for campo, mensajes in error.message_dict.items():
                destino = campo if campo in formulario.fields else None
                formulario.add_error(destino, mensajes)
        else:
            inscripcion.save()
            return redirect(
                "consultar_inscripcion",
                codigo_consulta=inscripcion.codigo_consulta,
            )
    inscriptos_confirmados = Inscripcion.objects.filter(
        categoria__torneo=torneo,
        estado="confirmada",
    ).select_related("categoria", "academia").order_by(
        "categoria_id", "fecha_inscripcion", "pk"
    )
    return render(
        request,
        "torneos/detalle_torneo.html",
        {
            "torneo": torneo,
            "formulario": formulario,
            "inscriptos_confirmados": inscriptos_confirmados,
        },
    )
def consultar_inscripcion(request, codigo_consulta):
    inscripcion = get_object_or_404(
        Inscripcion,
        codigo_consulta=codigo_consulta,
    )
    return render(
        request,
        "torneos/consultar_inscripcion.html",
        {"inscripcion": inscripcion},
    )
@login_required(login_url="ingreso_organizador")
def panel_organizador(request):
    organizador = Organizador.objects.filter(
        usuario=request.user,
        validada=True,
    ).first()

    torneos = Torneo.objects.none()
    if organizador is not None:
        torneos = Torneo.objects.filter(
            academia=organizador.academia,
        ).order_by("fecha_evento", "nombre")

    return render(
        request,
        "torneos/panel_organizador.html",
        {"organizador": organizador, "torneos": torneos},
    )
@login_required(login_url="ingreso_organizador")
def gestionar_torneo(request, torneo_id):
    organizador = Organizador.objects.filter(
        usuario=request.user,
        validada=True,
    ).first()

    if organizador is None:
        return HttpResponseForbidden("Tu cuenta no está validada.")

    torneo = get_object_or_404(
        Torneo,
        pk=torneo_id,
        academia=organizador.academia,
    )
    if request.method == "POST":
        Torneo.objects.filter(
            pk=torneo.pk,
            inscripciones_cerradas=False,
        ).update(
            inscripciones_cerradas=True,
            fecha_cierre_real=timezone.now(),
        )
        return redirect("gestionar_torneo", torneo_id=torneo.pk)
    inscripciones = Inscripcion.objects.filter(
        categoria__torneo=torneo,
    ).order_by("fecha_inscripcion", "pk")

    paginador = Paginator(inscripciones, 10)
    inscripciones = paginador.get_page(request.GET.get("pagina"))

    return render(
        request,
        "torneos/gestionar_torneo.html",
        {"torneo": torneo, "inscripciones": inscripciones},
    )
@login_required(login_url="ingreso_organizador")
@require_POST
def cancelar_inscripcion(request, inscripcion_id):
    organizador = Organizador.objects.filter(
        usuario=request.user,
        validada=True,
    ).first()

    if organizador is None:
        return HttpResponseForbidden("Tu cuenta no está validada.")

    inscripcion = get_object_or_404(
        Inscripcion,
        pk=inscripcion_id,
        categoria__torneo__academia=organizador.academia,
    )
    torneo = inscripcion.categoria.torneo

    if torneo.inscripciones_cerradas:
        return HttpResponseForbidden("Las inscripciones ya están cerradas.")

    inscripcion.estado = "cancelada"
    inscripcion.save(update_fields=["estado"])
    return redirect("gestionar_torneo", torneo_id=torneo.pk)
@login_required(login_url="ingreso_organizador")
def crear_torneo(request):
    organizador = Organizador.objects.filter(
        usuario=request.user,
        validada=True,
    ).first()

    if organizador is None:
        return HttpResponseForbidden("Tu cuenta no está validada.")

    if request.method == "POST":
        formulario = TorneoForm(request.POST)
        if formulario.is_valid():
            torneo = formulario.save(commit=False)
            torneo.academia = organizador.academia
            torneo.save()
            return redirect("panel_organizador")
    else:
        formulario = TorneoForm(
            initial={"correo_contacto": request.user.email},
        )

    return render(
        request,
        "torneos/crear_torneo.html",
        {"formulario": formulario},
    )
@login_required(login_url="ingreso_organizador")
def editar_inscripcion(request, inscripcion_id):
    organizador = Organizador.objects.filter(
        usuario=request.user,
        validada=True,
    ).first()

    if organizador is None:
        return HttpResponseForbidden("Tu cuenta no está validada.")

    inscripcion = get_object_or_404(
        Inscripcion,
        pk=inscripcion_id,
        categoria__torneo__academia=organizador.academia,
    )
    torneo = inscripcion.categoria.torneo

    if torneo.inscripciones_cerradas or inscripcion.estado != "confirmada":
        return HttpResponseForbidden("Esta inscripción ya no se puede editar.")

    if request.method == "POST":
        formulario = InscripcionForm(request.POST, torneo=torneo)
        if formulario.is_valid():
            for campo, valor in formulario.cleaned_data.items():
                setattr(inscripcion, campo, valor)

            try:
                inscripcion.full_clean()
            except ValidationError as error:
                for campo, mensajes in error.message_dict.items():
                    destino = campo if campo in formulario.fields else None
                    formulario.add_error(destino, mensajes)
            else:
                inscripcion.save()
                return redirect("gestionar_torneo", torneo_id=torneo.pk)
    else:
        formulario = InscripcionForm(torneo=torneo)
        formulario.initial = {
            campo: getattr(inscripcion, campo)
            for campo in formulario.fields
        }

    return render(
        request,
        "torneos/editar_inscripcion.html",
        {"formulario": formulario, "torneo": torneo},
    )