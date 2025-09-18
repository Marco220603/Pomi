from django.contrib import admin
from pomi.models.admin import Admin
from pomi.models.stundent import Student
from pomi.models.ticket import Ticket
from pomi.models.whatsappUser import WhatsAppUserStudent
from pomi.models.feedBackGPT import FeedbackGPT

# Register your models here.
admin.site.register(Admin)
admin.site.register(Student)
admin.site.register(Ticket)
admin.site.register(WhatsAppUserStudent)
admin.site.register(FeedbackGPT)