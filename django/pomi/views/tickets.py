from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from pomi.views.navbar import get_navbar_context
from pomi.models.ticket import Ticket

@login_required
def attend_tickets(request):
    """
    Listar todos los ticketa y atenderlos
    """
    if request.method == 'POST':
        action = request.POST.get('action', 'atender')
        codigo_ticket = request.POST.get('codigo_ticket', '').strip()
        
        # Datos
        mensaje_respuesta = request.POST.get('rpta_ticket', '').strip()
        if not mensaje_respuesta or not codigo_ticket :
            messages.error(request, "Es necesario una respuesta")
            return redirect('pomi:tickets')
        
        # Actualizar los estados de los tickets
        ticket_obj = get_object_or_404(Ticket, codigo_ticket=codigo_ticket)
        ticket_obj.state = "in_progress"
        ticket_obj.respuesta_anterior = ticket_obj.respuesta_actual
        ticket_obj.respuesta_actual = mensaje_respuesta
        ticket_obj.save()
        messages.success(request, f"Alumno {codigo_ticket} actualizado.")
        return redirect('pomi:tickets')
    # Lista los Tickets y atenderlos 
    else:
        all_tickets = Ticket.objects.all().order_by('created_at') if hasattr(Ticket, 'created_at') else Ticket.objects.all().order_by('codigo_ticket')
        ticket_count = Ticket.objects.filter(state='pending').count()  # Solo pendientes
        ctx = get_navbar_context(request, current_page="tickets")
        ctx.update({
            'page_title': 'Tickets',
            'page_subtitle': 'Gestión de Tickets',
            'alumnos': all_tickets,
            'ticket_count': ticket_count
        })
        return render(request, 'tickets/tickets_attend.html', ctx)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from pomi.apis.ticketSerializer import TicketSerializer, getTicket
from pomi.apis.ticketServices import createTicket
from pomi.apis.usuariosSerializers import AdminSerializer

class RegisterTicket(APIView):
    """
    API para que los alumnos puedan registrar los Tickets
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        print(request.data)
        serializer = TicketSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        #Obtener datos validados
        whatsappStudent = serializer.validated_data['whatsappStudent']
        descripcion = serializer.validated_data['descripcion']
        tipo = serializer.validated_data['tipo']
        titulo = serializer.validated_data['titulo']
        
        # Crear el Ticket:
        try:
            result = createTicket(whatsappStudent, {
                'descripcion': descripcion,
                'titulo':titulo,
                'tipo': tipo
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        #Prepara respuesta
        admin_serializer = AdminSerializer(result['ticket'].atendido_por)
        response_data = {
            'success': True,
            'message': f'El ticket fue creado correctamente',
            'data': {
                'codigo_ticket': result['ticket'].codigo_ticket,
                'persona_encargada': admin_serializer.data
            }
        }
        return Response(response_data, status=status.HTTP_200_OK)

class getTicketAPI(APIView):
    """
    API para buscar un ticket por el codigo
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = getTicket(data=request.data)
        if not serializer.is_valid():
            return Response({'status': 'error', 'error_detalle': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        #Obtener data validada
        ticket = serializer.validated_data['ticket']
        response = {
            'status': 'correcto',
            'ticket': {
                'codigo_ticket': ticket.codigo_ticket,
                'descripcion': ticket.descripcion,
                'estado': ticket.state,
                # agrega más campos si lo necesitas
            }
        }
        return Response(response, status=status.HTTP_200_OK)