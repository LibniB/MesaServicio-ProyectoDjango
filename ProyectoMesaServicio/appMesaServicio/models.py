from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
tipoOficinaAmbiente = [
    ('Administrativo','Administrativo'),
    ('Formacion','Formacion')
]

tipoUsuario = [
    ('Administrativo','Administrativo'),
    ('Instructor','Instructor')
]

estadoCaso = [
    ('Solicitado','Solicitado'),
    ('En Proceso','En Proceso'),
    ('Finalizada','Finalizada')
]

class OficinaAmbiente(models.Model):
    ofiTipo = models.CharField(max_length=15,choices=tipoOficinaAmbiente,
                              db_comment="tipo de oficina")
    
    ofiNombre = models.CharField(max_length=50, unique=True,
                                 db_comment="nombre de la oficina o ambiente")
    
    fechaHoraCreacion = models.DateTimeField(auto_now_add=True,
                                            db_comment="fecha y hora del registro")
    
    fechaHoraActualizacion = models.DateTimeField(auto_now_add=True,
                                                  db_comment="fecha y hora ultima actualizacion")
    
    def __str__(self) -> str:
        return self.ofiNombre
    
class User (AbstractUser):
    userTipo = models.CharField(max_length=15, choices = tipoUsuario,
                                db_comment="Tipo de usuario")
    
    userFoto = models.ImageField(upload_to=f"fotos/", null=True, blank=True,
                                 db_comment="Foto del usuario")
    
    fechaHoraCreacion = models.DateTimeField(auto_now_add=True,
                                            db_comment="fecha y hora del registro")
    
    fechaHoraActualizacion = models.DateTimeField(auto_now_add=True,
                                                  db_comment="fecha y hora ultima actualizacion")
    
    def __str__(self) -> str:
        return f"{self.username}"
    
class Solicitud(models.Model):
    solUsuario= models.ForeignKey(User,on_delete=models.PROTECT,
                                  db_comment="Hace referencia al empleado que hace la solicitud")
    
    solDescripcion = models.TextField(max_length=1000,
                                      db_comment="Texto que describe la solicitud del empleado")
    
    solOficinaAmbiente = models.ForeignKey(OficinaAmbiente, on_delete=models.PROTECT,
                                           db_comment="hace referencia a la oficina o ambiente donde se encuentra el equipo de la solicitud")
    
    fechaHoraCreacion = models.DateTimeField(auto_now_add=True,
                                            db_comment="fecha y hora de la solicitud")
    
    fechaHoraActualizacion = models.DateTimeField(auto_now_add=True,
                                            db_comment="fecha y hora de ultima actualizacion")
    
    def __str__(self) -> str:
        return self.solDescripcion
    
class Caso(models.Model):
    casSolicitud = models.ForeignKey(Solicitud,on_delete=models.PROTECT,
                                     db_comment="Hace referencia a la solicitud que genero el caso")
    
    casCodigo = models.CharField(max_length=10,unique=True,
                                 db_comment="Codigo unico del caso")
    
    casUsuario = models.ForeignKey(User,on_delete=models.PROTECT,
                                   db_comment="Empleado de soporte tecnico asignado al caso")
    
    casEstado = models.CharField(max_length=20, choices=estadoCaso)
    
    fechaHoraActualizacion = models.DateTimeField(auto_now_add=True,
                                            db_comment="fecha y hora de ultima actualizacion")
    

    