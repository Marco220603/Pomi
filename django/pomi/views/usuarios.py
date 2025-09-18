from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth.decorators import login_required
from pomi.models.stundent import Student
from pomi.models.whatsappUser import WhatsAppUserStudent
from django.contrib import messages
from pomi.views.navbar import get_navbar_context
from pomi.models.ticket import Ticket

@login_required
def manage_student(request):
    """
    CRUD compacto:
    - GET   -> lista alumnos
    - POST  -> create / update / delete (campo hidden 'action')
    """
    if request.method == 'POST':
        action = request.POST.get('action', 'create')
        code_upc = request.POST.get('code_upc', '').strip()

        if action == 'delete':
            obj = get_object_or_404(Student, code_upc=code_upc)
            obj.delete()
            messages.success(request, f"Alumno {code_upc} eliminado.")
            return redirect('pomi:alumnos')

        # datos comunes create/update
        first_names = request.POST.get('first_names', '').strip()
        full_names  = request.POST.get('full_names', '').strip()
        career      = request.POST.get('career', '').strip()
        is_active   = request.POST.get('is_active') in ['on', 'true', 'True', '1']

        if not code_upc or not first_names or not full_names:
            messages.error(request, "Código UPC, Nombres y Apellidos son obligatorios.")
            return redirect('pomi:alumnos')

        if action == 'update':
            obj = get_object_or_404(Student, code_upc=code_upc)
            obj.first_names = first_names
            obj.full_names  = full_names
            obj.career      = career
            obj.is_active   = is_active
            obj.save()
            messages.success(request, f"Alumno {code_upc} actualizado.")
        else:
            Student.objects.create(
                code_upc=code_upc,
                first_names=first_names,
                full_names=full_names,
                career=career,
                is_active=is_active,
            )
            messages.success(request, f"Alumno {code_upc} creado.")

        return redirect('pomi:alumnos')

    # GET
    alumnos = Student.objects.all().order_by('-created_at') if hasattr(Student, 'created_at') else Student.objects.all().order_by('code_upc')
    ctx = get_navbar_context(request, current_page='students')
    ctx.update({
        'page_title': 'Alumnos',
        'page_subtitle': 'Gestión de estudiantes',
        'alumnos': alumnos,
    })
    return render(request, 'alumnos/manage.html', ctx)

# APIs
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from pomi.apis.studentSerializer import VerifyStudentSerializer
from pomi.apis.studentServices import update_or_create_WhatsAppUser

class VerifyStudentAPI(APIView):
    
    """
    API para verificar si un estudiante existe por su código
    y asociar/actualizar su número de WhatsApp
    """
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = VerifyStudentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener datos validados
        student = serializer.validated_data['student']
        phone = serializer.validated_data['phone']
        
        # Crear o actualizar WhatsAppUser
        try:
            result = update_or_create_WhatsAppUser(student, phone)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Preparar respuesta
        response_data = {
            'success': True,
            'message': f'Estudiante verificado y WhatsApp {result["state"]}',
            'data': {
                'code': student.code_upc,
                'names': student.first_names,
                'last_names': student.full_names,
                'whatsapp_status': result["state"],
                'activo': student.is_active
            }
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
       
