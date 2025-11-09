from rest_framework import serializers
from pomi.models.ticket import Ticket
from pomi.models.whatsappUser import WhatsAppUserStudent

class TicketSerializer(serializers.ModelSerializer):
    # Campos que llegan del cliente:
    titulo = serializers.CharField(write_only=True)
    descripcion = serializers.CharField(write_only=True)
    celular = serializers.CharField(write_only=True)
    tipo = serializers.CharField(write_only=True)
    
    class Meta:
        model = Ticket
        # Incluimos los reales + los de conveniencia
        fields = [
            "id", "codigo_ticket", "subject", "description", "type_ticket",
            "state", "priority", "created_at",
            "titulo", "descripcion", "celular", "tipo",
        ]
        read_only_fields = ["id", "codigo_ticket", "subject", "description", "type_ticket", "state", "created_at"]
    
    # Validacion para nuestra API
    def validate(self, data):
        titulo = data.get('titulo')
        descripcion = data.get('descripcion')
        celular = data.get('celular')
        tipo = data.get('tipo')
        
        if not titulo and not descripcion and not celular and not tipo:
            raise serializers.ValidationError({'error': 'Los campos "titulo", "descripcion", "celular", "tipo"'})
        whatsappStudent = None
        # Usamos filter().first() para manejar casos con múltiples registros
        # Obtenemos el más reciente basado en last_date_update
        whatsappStudent = WhatsAppUserStudent.objects.filter(phone_number=celular).order_by('-last_date_update').first()
        if not whatsappStudent:
            raise serializers.ValidationError({'error': 'No se ha podido registrar el ticket, diferente número'})
        data['whatsappStudent'] = whatsappStudent
        return data

class getTicket(serializers.Serializer):
    codigo_ticket = serializers.CharField(required=True)
    def validate(self, data):
        code = data.get('codigo_ticket')
        ticket = None
        if not code:
            raise serializers.ValidationError({'status': 'El codigo tiene que ser obligatorio', 'ticket': ticket})
        try:
            ticket = Ticket.objects.get(codigo_ticket=code)
        except Ticket.DoesNotExist:
            raise serializers.ValidationError({'status': 'No se ha podido encontrar el codigo', 'ticket': None})
        data['ticket'] = ticket
        return data
        