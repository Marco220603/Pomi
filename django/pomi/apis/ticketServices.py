from pomi.models.ticket import Ticket
from pomi.models.admin import Admin

def createTicket(whatsappStudent, dataTicket):
    #1. Obtener la prioridad
    titulo = dataTicket.get("titulo")
    priority = asignPriority(titulo)
    
    #2. Obtener al Encargado de Atender el Ticket
    admin = assignStaff()
    
    #3. Crecion del Ticket
    ticket = Ticket.objects.create(
        student=whatsappStudent,
        atendido_por = admin,
        subject = titulo,
        description=dataTicket.get("descripcion"),
        type_ticket=dataTicket.get("tipo"),
        priority=priority
    )
    print(ticket)
    return {
        'state': 'Ticket creado satisfactoriamente',
        'ticket': ticket
    }
    
    
def asignPriority(titulo):
    """
    Definir Prioridad
    """
    prioridades = {
        "No puedo contactar a mi asesor especializado": "Alta",
        "No puedo contactar a mi coautor": "Alta",
        "Ingreso erróneo de código del alumno": "Media",
        "Error en el nombre del partner": "Media",
        "Error en el nombre del asesor especializado": "Baja",
        "No adjunté el documento firmado y aprobado por el asesor especializado": "Alta"
    }
    return prioridades.get(titulo)

def assignStaff():
    #1. Obtener todos los Staff
    admins = Admin.objects.all()
    #2. Diccionario para guardar la cantidad de Tickets
    admin_ticket_count = {}
    for admin in admins:
        # 2.1 Contar tickets pendientes asignados a este admin
        count = Ticket.objects.filter(atendido_por=admin, state="pending").count()
        admin_ticket_count[admin] = count
    #3. Buscar al admin con menos tickets pendientes
    admin_disponible = min(admin_ticket_count, key=admin_ticket_count.get, default=None)
    return admin_disponible