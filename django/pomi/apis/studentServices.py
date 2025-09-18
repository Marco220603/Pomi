from pomi.models.whatsappUser import WhatsAppUserStudent

# Metodo para actualizar o registrar un WhatsApp Student, ya debe haber previa validación
def update_or_create_WhatsAppUser(student, phone_number):
    whatsapp_user, creado = WhatsAppUserStudent.objects.get_or_create(
        student = student,
        defaults={'phone_number': phone_number}
    )
    if not creado:
        whatsapp_user.phone_number = phone_number
        whatsapp_user.save()
    return {
        'state': 'created' if creado else 'actualizado'
    }