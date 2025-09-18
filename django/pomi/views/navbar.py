# views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count
from pomi.models.ticket import Ticket
# Simulando modelos - reemplaza por tus modelos reales
# from .models import Ticket, Feedback, Notification

def get_navbar_context(request, current_page=None):
    """
    Función helper para obtener el contexto común del navbar
    """
    context = {
        'current_page': current_page,
        'user': request.user,
        
        # Contadores dinámicos - ajusta según tus modelos
        'ticket_count': Ticket.objects.filter(state='pending').count(),
        'feedback_count': 3,  # Feedback.objects.filter(is_read=False).count()
        'notification_count': 6,  # Notification.objects.filter(user=request.user, is_read=False).count()
        
        # URLs del navbar - ajusta según tu urls.py
        'urls': {
            'dashboard': 'dashboard:home',
            'tickets': 'dashboard:tickets', 
            'students': 'dashboard:students',
            'feedback': 'dashboard:feedback',
            'reports': 'dashboard:reports',
            'logout': 'auth:logout',
        }
    }
    return context
