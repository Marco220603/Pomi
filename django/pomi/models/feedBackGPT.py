from django.db import models
from .whatsappUser import WhatsAppUserStudent
from datetime import datetime

class FeedbackGPT(models.Model):
    whatsAppStudent = models.ForeignKey(WhatsAppUserStudent, on_delete=models.CASCADE)
    code_conversación = models.CharField(max_length=20, unique=True, blank=False)
    pregunta = models.CharField(max_length=300, blank=False)
    respuesta = models.CharField(max_length=400, blank=False)
    tiempo = models.CharField(blank=False, max_length=10)
    
    def save(self, *args, **kwargs):
        if not self.pk and not self.code_conversación:
            super().save(*args, **kwargs)
            self.code_conversación = f"RPTA00{self.pk:02d}{datetime.now().year}"
            return super().save(update_fields=["code_conversación"])
        return super().save(*args, **kwargs)