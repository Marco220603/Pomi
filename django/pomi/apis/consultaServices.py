from pomi.models.feedBackGPT import FeedbackGPT
from pomi.models.whatsappUser import WhatsAppUserStudent

def guardar_historico(data):
    phone_number = data['celular']
    whatsappuser = WhatsAppUserStudent.objects.get(phone_number=phone_number)
    # Creando el nuevo registro histórico
    nuevo_registro = FeedbackGPT.objects.create(
        whatsAppStudent=whatsappuser,
        pregunta=data['pregunta'],
        respuesta=data['respuesta'],
        tiempo=data['tiempo']   
    )
    return nuevo_registro