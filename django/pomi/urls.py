from django.urls import path
from .views.login import sign_in
from .views.dashboard import home
from .views.usuarios import (
    manage_student, 
    VerifyStudentAPI, 
    export_students_csv,
    download_template,
    process_bulk_file,
    confirm_bulk_load
)
from .views.tickets import RegisterTicket, attend_tickets
from .views.consulta import ChatWebhookView
from .views.openia import gpt_response

app_name = 'pomi'

urlpatterns = [
  path('', sign_in, name="signin"),
  path('login/', sign_in, name="signin"),
  path('dashboard/', home, name="dashboard"),
  path('alumnos/', manage_student, name="alumnos"),
  path('alumnos/export-csv/', export_students_csv, name="alumnos_csv"),
  path('alumnos/template/', download_template, name="download_template"),
  path('alumnos/process-bulk/', process_bulk_file, name="process_bulk_file"),
  path('alumnos/confirm-bulk/', confirm_bulk_load, name="confirm_bulk_load"),
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