from django.db import models
from .stundent import Student

class WhatsAppUserStudent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, unique=False)
    last_date_update = models.DateTimeField(auto_now=True)
# Texto Prueba