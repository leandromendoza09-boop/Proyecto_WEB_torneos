from decimal import Decimal
from django.utils import timezone
from django import forms

from .models import Academia, Categoria, Torneo


class InscripcionForm(forms.Form):
    nombre = forms.CharField(max_length=100)
    apellido = forms.CharField(max_length=100)
    dni = forms.CharField(label="DNI", max_length=20)
    fecha_nacimiento = forms.DateField(
        label="Fecha de nacimiento",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    peso = forms.DecimalField(
        label="Peso en kg",
        max_digits=6,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )
    categoria = forms.ModelChoiceField(
        label="Categoría",
        queryset=Categoria.objects.none(),
        empty_label="Seleccioná tu categoría",
    )
    academia = forms.ModelChoiceField(
        queryset=Academia.objects.order_by("nombre"),
        empty_label="Seleccioná tu academia",
    )
    profesor_a_cargo = forms.CharField(label="Profesor a cargo", max_length=150)
    correo = forms.EmailField(label="Correo electrónico")

    def __init__(self, *args, torneo, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categoria"].queryset = torneo.categorias.order_by("id")
    def clean(self):
        datos = super().clean()
        peso = datos.get("peso")
        categoria = datos.get("categoria")

        if peso is not None and categoria is not None:
            division_correcta = "hasta_70" if peso <= 70 else "mas_70"

            if categoria.division_peso != division_correcta:
                self.add_error(
                    "categoria",
                    "La categoría elegida no coincide con el peso declarado.",
                )

        return datos

class TorneoForm(forms.ModelForm):
    class Meta:
        model = Torneo
        fields = [
            "nombre",
            "descripcion",
            "fecha_evento",
            "localidad",
            "direccion",
            "apertura_inscripciones",
            "correo_contacto",
        ]
        widgets = {
            "fecha_evento": forms.DateInput(attrs={"type": "date"}),
            "apertura_inscripciones": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
            ),
        }

    def clean(self):
        datos = super().clean()
        fecha = datos.get("fecha_evento")
        apertura = datos.get("apertura_inscripciones")

        if fecha and fecha <= timezone.localdate():
            self.add_error("fecha_evento", "Elegí una fecha futura.")

        if fecha and apertura and timezone.localtime(apertura).date() >= fecha:
            self.add_error(
                "apertura_inscripciones",
                "La apertura debe ser anterior al día del torneo.",
            )

        return datos