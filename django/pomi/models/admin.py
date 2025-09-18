from django.db import models
from django.contrib.auth.models import User

class Admin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    cellphone = models.CharField(max_length=20)
    career = models.CharField(max_length=50)
    is_superAdmin = models.BooleanField(default=False)