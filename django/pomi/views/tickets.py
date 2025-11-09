from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from pomi.views.navbar import get_navbar_context
from pomi.models.ticket import Ticket
import logging

logger = logging.getLogger(__name__)

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
        priority = request.POST.get('priority', 'Media').strip()
        state = request.POST.get('state', 'in_progress').strip()
        
        if not mensaje_respuesta or not codigo_ticket:
            messages.error(request, "Es necesario una respuesta")
            return redirect('pomi:tickets')
        
        # Actualizar los estados de los tickets
        ticket_obj = get_object_or_404(Ticket, codigo_ticket=codigo_ticket)
        ticket_obj.state = state
        ticket_obj.priority = priority
        ticket_obj.respuesta_anterior = ticket_obj.respuesta_actual
        ticket_obj.respuesta_actual = mensaje_respuesta
        ticket_obj.save()
        
        # Enviar respuesta por WhatsApp al estudiante
        logger.info("="*80)
        logger.info("INICIANDO ENVÍO DE WHATSAPP AL ESTUDIANTE")
        logger.info("="*80)
        
        try:
            BUILDERBOT_URL = 'https://bountiful-vitality-production.up.railway.app'
            
            # Obtener datos del administrador (usuario autenticado)
            admin_user = request.user
            # ticket_obj.student es un WhatsAppUserStudent, que tiene phone_number
            student_number = ticket_obj.student.phone_number
            
            logger.info(f"Número original del estudiante: {student_number}")
            
            # Agregar @s.whatsapp.net si no lo tiene
            if not student_number.endswith('@s.whatsapp.net'):
                student_number = f"51{student_number}@s.whatsapp.net"
            
            logger.info(f"Número formateado: {student_number}")
            
            texto = (
                f"✅ *Respuesta a tu Ticket #{ticket_obj.codigo_ticket}*\n"
                f"👨‍💼 Administrador: {admin_user.first_name} {admin_user.last_name}\n"
                f"🎫 Título: {ticket_obj.subject}\n"
                f"💬 Respuesta:\n{mensaje_respuesta}\n\n"
            )
            
            import requests as req
            
            url = f"{BUILDERBOT_URL}/v1/sendAnswer"
            payload = {
                "number": student_number,
                "message": texto,
                "urlMedia": None
            }
            
            logger.info(f"URL: {url}")
            logger.info(f"Payload: {payload}")
            logger.info("Enviando petición HTTP...")
            
            response = req.post(url, json=payload, timeout=10)
            
            logger.info(f"Respuesta HTTP Status: {response.status_code}")
            logger.info(f"Respuesta HTTP Body: {response.text}")
            logger.info(f"Respuesta HTTP Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                logger.info("✓ Mensaje enviado exitosamente")
                messages.success(request, f"Ticket {codigo_ticket} actualizado y respuesta enviada por WhatsApp.")
            else:
                logger.error(f"✗ Error en envío: status {response.status_code}")
                messages.warning(request, f"Ticket {codigo_ticket} actualizado, pero no se pudo enviar WhatsApp (status: {response.status_code}).")
                
        except Exception as e:
            logger.error(f"EXCEPCIÓN al enviar WhatsApp: {e}")
            logger.error(f"Tipo de error: {type(e).__name__}")
            import traceback
            logger.error(traceback.format_exc())
            messages.warning(request, f"Ticket {codigo_ticket} actualizado, pero hubo un error al enviar WhatsApp: {str(e)}")
        
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
import requests
import sys

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
        
        # NOTIFICAR AL ADMINISTRADOR QUE SE ESTA REGISTRANDO UN TICKET
        logger.info("="*80)
        logger.info("INICIANDO NOTIFICACIÓN AL ADMINISTRADOR")
        logger.info("="*80)
        
        try:
            BUILDERBOT_URL = 'https://bountiful-vitality-production.up.railway.app'
            FRONTEND_URL  = 'http://pomi-production.up.railway.app'
            admin_number = admin_serializer.data.get('cellphone')
            ticket_obj = result['ticket']
            
            logger.info(f"Número de admin obtenido: {admin_number}")
            logger.info(f"Ticket creado: #{ticket_obj.codigo_ticket}")
            
            if admin_number:
                # Agregar @s.whatsapp.net si no lo tiene
                if not admin_number.endswith('@s.whatsapp.net'):
                    admin_number = f"51{admin_number}@s.whatsapp.net"
                
                logger.info(f"Número formateado del admin: {admin_number}")
                    
                mensaje = (
                    f"📢 *Nuevo Ticket #{ticket_obj.codigo_ticket}*\n"
                    f"👤 Estudiante: {whatsappStudent.student.first_names} {whatsappStudent.student.full_names} ({whatsappStudent.phone_number})\n"
                    f"🎫 Título: {ticket_obj.subject}\n"
                    f"📂 Tipo: {ticket_obj.type_ticket}\n"
                    f"⚡ Prioridad: {ticket_obj.priority}\n"
                    f"📝 Descripción: {ticket_obj.description}\n\n"
                    f"👉 Atendelo aquí: {FRONTEND_URL}/tickets/"
                )
                
                url = f"{BUILDERBOT_URL}/v1/sendAdmin"
                payload = {
                    "number": admin_number,
                    "message": mensaje,
                    "urlMedia": None
                }
                
                logger.info(f"URL: {url}")
                logger.info(f"Payload: {payload}")
                logger.info("Enviando petición HTTP al admin...")
                
                response = requests.post(url, json=payload, timeout=10)
                
                logger.info(f"Respuesta HTTP Status: {response.status_code}")
                logger.info(f"Respuesta HTTP Body: {response.text}")
                logger.info(f"Respuesta HTTP Headers: {dict(response.headers)}")
                
                if response.status_code == 200:
                    logger.info(f"✓ Notificación enviada exitosamente a {admin_number}")
                else:
                    logger.error(f"✗ Error al enviar notificación: status {response.status_code}")
            else:
                logger.warning("No se encontró número de teléfono del administrador")
                
        except Exception as e:
            logger.error(f"EXCEPCIÓN al enviar WhatsApp al admin: {e}")
            logger.error(f"Tipo de error: {type(e).__name__}")
            import traceback
            logger.error(traceback.format_exc())
            
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