from django.db import models

# Create your models 
class Student(models.Model):
  code_upc = models.CharField(max_length=10, unique=True) # ejm: u20201f583 u202111c52
  first_names = models.CharField(max_length=100) # ejm: Marco Andre
  full_names = models.CharField(max_length=100) # ejm: Ponce Boza
  career = models.CharField(max_length=50) # ejm: Ingenieria de Sistemas de Informacion
  is_active = models.BooleanField(default=False) # ejm: True