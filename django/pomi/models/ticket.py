from django.db import models
from .whatsappUser import WhatsAppUserStudent
from django.utils import timezone
from .admin import Admin
from datetime import datetime


class Ticket(models.Model):
    
    ESTADO_CHOICES = [
        ('pending', 'Pendiente'),
        ('in_progress', 'En Progreso'),
        ('resolved', 'Resuelto'),
        ('closed', 'Cerrado')
    ]
    
    TIPO_CHOICES = [
        ('Problemas de comunicación', 'Problemas de comunicación'),
        ('Errores en el formulario', 'Errores en el formulario'),
        ('Documentación incompleta', 'Documentación incompleta')
    ]
    
    PRIORIDAD_CHOICES = [
        ('Baja', 'Baja'),
        ('Media', 'Media'),
        ('Alta', 'Alta')
    ]
    
    #Relaciones
    student = models.ForeignKey(WhatsAppUserStudent, on_delete=models.CASCADE) # Relacion con el modelo Student
    atendido_por = models.ForeignKey(Admin, null=True, blank=True, on_delete=models.SET_NULL)
    
    # Tickets
    codigo_ticket = models.CharField(max_length=20, unique=True)
    subject = models.CharField(max_length=100) # ejm: Problema con un documento
    description = models.TextField() # ejm: No puedo abrir el documento
    type_ticket =  models.CharField(max_length=50, choices=TIPO_CHOICES,default='other')
    state = models.CharField(max_length=20, choices=ESTADO_CHOICES,default='pending')
    priority = models.CharField(max_length=20, choices=PRIORIDAD_CHOICES,default='Baja')
    respuesta_actual = models.TextField(blank=True, null=True)
    respuesta_anterior = models.TextField(blank=True, null=True)
    
    #Fechas
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.pk and not self.codigo_ticket:
            super().save(*args, **kwargs)
            self.codigo_ticket = f"T00{self.pk:02d}{datetime.now().year}"
            return super().save(update_fields=["codigo_ticket"])
        return super().save(*args, **kwargs)