from django.db import models
from django.conf import settings
import uuid
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone



class Academia(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    referente_principal = models.CharField(max_length=150)
    correo_institucional = models.EmailField(blank=True)
    telefono_institucional = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return self.nombre# Create your models here.

class Organizador(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
    )
    academia = models.OneToOneField(
        Academia,
        on_delete=models.PROTECT,
    )
    dni = models.CharField(max_length=20, unique=True)
    fecha_nacimiento = models.DateField(
    help_text="Ingresá la fecha en formato mes/día/año (MM/DD/AAAA). "
              "Ejemplo: 12/25/2000 para el 25 de diciembre de 2000."
)
    validada = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.usuario.username} - {self.academia.nombre}"
    
class Torneo(models.Model):
    academia = models.ForeignKey(
        Academia,
        on_delete=models.PROTECT,
    )
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField()
    fecha_evento = models.DateField()
    localidad = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200)
    apertura_inscripciones = models.DateTimeField()
    inscripciones_cerradas = models.BooleanField(default=False)
    fecha_cierre_real = models.DateTimeField(
        null=True,
        blank=True,
    )
    correo_contacto = models.EmailField()

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        es_nuevo = self._state.adding
        super().save(*args, **kwargs)

        if es_nuevo:
            for cinturon, _ in Categoria.CINTURONES:
                for division, _ in Categoria.DIVISIONES_PESO:
                    Categoria.objects.create(
                        torneo=self,
                        cinturon=cinturon,
                        division_peso=division,
                    )

class Categoria(models.Model):
    CINTURONES = [
        ("blanco", "Blanco"),
        ("azul", "Azul"),
        ("morado", "Morado"),
        ("marron", "Marrón"),
        ("negro", "Negro"),
    ]

    DIVISIONES_PESO = [
        ("hasta_70", "Hasta 70 kg"),
        ("mas_70", "Más de 70 kg"),
    ]

    torneo = models.ForeignKey(
        Torneo,
        on_delete=models.CASCADE,
        related_name="categorias",
    )
    cinturon = models.CharField(
        max_length=10,
        choices=CINTURONES,
    )
    division_peso = models.CharField(
        max_length=10,
        choices=DIVISIONES_PESO,
    )
    cupo_maximo = models.PositiveIntegerField(default=16)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["torneo", "cinturon", "division_peso"],
                name="categoria_unica_por_torneo",
            ),
        ]

    def __str__(self):
        return (
            f"{self.torneo.nombre} - "
            f"{self.get_cinturon_display()} - "
            f"{self.get_division_peso_display()}"
        )

class Inscripcion(models.Model):
    ESTADOS = [
        ("confirmada", "Confirmada"),
        ("cancelada", "Cancelada"),
    ]

    codigo_consulta = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="inscripciones",
    )
    academia = models.ForeignKey(
        Academia,
        on_delete=models.PROTECT,
        related_name="inscripciones",
    )
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(max_length=20)
    fecha_nacimiento = models.DateField()
    peso = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    profesor_a_cargo = models.CharField(max_length=150)
    correo = models.EmailField()
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=10,
        choices=ESTADOS,
        default="confirmada",
    )

    def __str__(self):
        return f"{self.apellido}, {self.nombre} - {self.categoria}"
    
    def clean(self):
        super().clean()

        if not self.fecha_nacimiento or not self.categoria_id:
            return
        
        torneo = self.categoria.torneo

        if self._state.adding:
            if torneo.inscripciones_cerradas:
                raise ValidationError(
                    "Las inscripciones de este torneo están cerradas."
                )

            if timezone.now() < torneo.apertura_inscripciones:
                raise ValidationError(
                    "Las inscripciones de este torneo todavía no abrieron."
                )

            if timezone.localdate() >= torneo.fecha_evento:
                raise ValidationError(
                    "Ya no se permiten inscripciones para este evento."
                )
        

        fecha_evento = self.categoria.torneo.fecha_evento
        nacimiento = self.fecha_nacimiento

        edad = fecha_evento.year - nacimiento.year

        if (fecha_evento.month, fecha_evento.day) < (
            nacimiento.month,
            nacimiento.day,
        ):
            edad -= 1

        if edad < 18 or edad > 30:
            raise ValidationError({
                "fecha_nacimiento": (
                    "El competidor debe tener entre 18 y 30 años "
                    "inclusive el día del torneo."
                )
            })
                
        if self.estado == "confirmada":
            duplicada = Inscripcion.objects.filter(
                dni=self.dni,
                categoria__torneo=self.categoria.torneo,
                estado="confirmada",
            ).exclude(pk=self.pk).exists()

            if duplicada:
                raise ValidationError({
                    "dni": (
                        "Ya existe una inscripción confirmada "
                        "con este DNI en el torneo."
                    )
                })
            
            cantidad = Inscripcion.objects.filter(
                categoria=self.categoria,
                estado="confirmada",
            ).exclude(pk=self.pk).count()

            if cantidad >= self.categoria.cupo_maximo:
                raise ValidationError({
                    "categoria": (
                        "La categoría ya tiene el cupo completo."
                    )
                })