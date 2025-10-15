from django.urls import path
from .views.login import sign_in
from .views.dashboard import home
from .views.usuarios import manage_student, VerifyStudentAPI
from .views.tickets import RegisterTicket, attend_tickets
from .views.consulta import ChatWebhookView
from .views.openia import gpt_response

app_name = 'pomi'

urlpatterns = [
  path('', sign_in, name="signin"),
  path('login/', sign_in, name="signin"),
  path('dashboard/', home, name="dashboard"),
  path('alumnos/', manage_student, name="alumnos"),
  path('tickets/', attend_tickets, name="tickets"),
  
  # --- APIs ---
  # - Students
  path('api/verify-student/', VerifyStudentAPI.as_view(), name="verify-student-api"),
  
  # - Tickets
  path('api/create-ticket/', RegisterTicket.as_view(), name="create-ticket-api"),
  
  # - Consulta
  path('api/consulta-rasa/', ChatWebhookView.as_view(), name="consulta-rasa-api"),
  path('api/gpt_response/', gpt_response, name="gpt_response"),
] 