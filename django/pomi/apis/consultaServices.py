from pomi.models.feedBackGPT import FeedbackGPT
from pomi.models.whatsappUser import WhatsAppUserStudent
from pomi.models.stundent import Student
from django.core.exceptions import ObjectDoesNotExist

def guardar_historico(data):
    phone_number = data['celular']
    
    try:
        # Intentar obtener el usuario existente
        whatsappuser = WhatsAppUserStudent.objects.get(phone_number=phone_number)
        print(f"✅ Usuario encontrado: {whatsappuser}")
    except ObjectDoesNotExist:
        print(f"⚠️ Usuario con teléfono {phone_number} no existe, creando uno nuevo...")
        
        # Crear un estudiante temporal si no existe
        try:
            # Intentar obtener un estudiante existente con el sender_id como código
            student = Student.objects.get(code_upc=data.get('sender_id', f'temp_{phone_number}'))
        except ObjectDoesNotExist:
            # Crear un estudiante temporal
            student = Student.objects.create(
                code_upc=data.get('sender_id', f'temp_{phone_number}'),
                first_names="Usuario",
                full_names="Temporal",
                career="Sin especificar",
                is_active=True
            )
            print(f"✅ Estudiante temporal creado: {student}")
        
        # Crear el usuario de WhatsApp
        whatsappuser = WhatsAppUserStudent.objects.create(
            student=student,
            phone_number=phone_number
        )
        print(f"✅ Usuario WhatsApp creado: {whatsappuser}")
    
    # Creando el nuevo registro histórico
    nuevo_registro = FeedbackGPT.objects.create(
        whatsAppStudent=whatsappuser,
        pregunta=data['pregunta'],
        respuesta=data['respuesta'],
        tiempo=data['tiempo']   
    )
    return nuevo_registro