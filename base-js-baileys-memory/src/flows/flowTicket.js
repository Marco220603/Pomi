import { EVENTS } from "@builderbot/bot";
import { addKeyword } from "@builderbot/bot";
import fs from 'fs'
import path from 'path'
import dotenv from 'dotenv'
import { fileURLToPath } from 'url'
import { dirname } from 'path'
import axios from "axios"
import { menu } from './flowMenu.js'
import { 
  builderBotTyping,     // ← Para uso simple en flows
  withTyping,           // ← Para APIs/procesos largos
  //realisticTyping,      // ← Para mensajes largos
  //showTyping,           // ← Control básico
  //stopTyping,           // ← Detener animación
  //typingUntilResolve,   // ← Esperar promesas
  //typingManager,        // ← Control avanzado
  //delay                 // ← Función delay personalizada
} from './../behavior/typing.js';

// Manejo de __dirname en ESModules
const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

// Leer los archivos TXT
const ticket_TIPO = fs.readFileSync(path.join(__dirname, '../template/tickets/Ticket_TIPO.txt'), 'utf-8')
const ticket_DESC = fs.readFileSync(path.join(__dirname, '../template/tickets/Ticket_DESC.txt'), 'utf-8')

dotenv.config()
const createTicketUrl = process.env['create-ticket']

export const flowTicket_TIPO = addKeyword(EVENTS.ACTION)
.addAnswer(ticket_TIPO, {capture:true},
  async(ctx, ctxFn) => {
    const input = ctx.body.toLocaleLowerCase()
    if(!["1","2","3","4","5","6","7"].includes(input)){
      return ctxFn.fallBack('Respuesta no válida, por favor ingrese un número entre el *1 al 7*')
    }
    if(input == '7') return ctxFn.gotoFlow(menu)
    const titulo = {1: 'No puedo contactar a mi asesor especializado', 2: 'No puedo contactar a mi coautor', 3: 'Ingreso erróneo de código del alumno', 4:'Error en el nombre del partner', 5: 'Error en el nombre del asesor especializado', 6:'No adjunté el documento firmado y aprobado por el asesor especializado'}

    const tipos = {
        1: 'Problemas de comunicación',
        2: 'Problemas de comunicación',
        3: 'Errores en el formulario',
        4: 'Errores en el formulario',
        5: 'Errores en el formulario',
        6: 'Documentación incompleta'
    }
    await ctxFn.state.update({titulo: titulo[input]})
    await ctxFn.state.update({tipo: tipos[input]})
    await ctxFn.state.update({celular: ctx.from.slice(-9)})
  }
).addAction(
  async(ctx, ctxFn) => {
    await builderBotTyping(ctx, ctxFn.provider, 1500)
    await ctxFn.flowDynamic(`Haz seleccionado el tipo: ${ctxFn.state.get('titulo')}`)
    await builderBotTyping(ctx, ctxFn.provider, 1500)
    return ctxFn.gotoFlow(flowTicket_DESC)
  }
)

export const generarTicket = addKeyword(EVENTS.ACTION)
.addAction({capture: false , delay: 100},
  async(ctx, ctxFn) => {
    // Mostrar animación 'Escribiendo'
    await builderBotTyping(ctx, ctxFn.provider, 1500)
    await ctxFn.flowDynamic('Ingresando a la generación de Tickets')
    // Mostrar animación 'Escribiendo'
    await builderBotTyping(ctx, ctxFn.provider, 1500)
    return ctxFn.gotoFlow(flowTicket_TIPO)
  }
)

export const flowTicket_DESC = addKeyword(EVENTS.ACTION)
.addAnswer(ticket_DESC, {capture: true}, 
  async(ctx, ctxFn) => {
    const input = ctx.body.trim()
    if(input == '1'){
      await builderBotTyping(ctx, ctxFn.provider, 1500)
      return ctxFn.gotoFlow(flowTicket_TIPO)
    }
    if(input == '2'){
      await builderBotTyping(ctx, ctxFn.provider, 1500)
      return ctxFn.gotoFlow(menu)
    }
    if(input.length <= 12){
      await builderBotTyping(ctx, ctxFn.provider, 1500)
      return ctxFn.fallBack('La descripción es muy corta, por favor ingrese unsa descripción más larga.')
    }
    await ctxFn.state.update({desc: input})
    await builderBotTyping(ctx, ctxFn.provider, 1500)
    return ctxFn.gotoFlow(flowTicket_ENVIO)
  }
)

export const flowTicket_ENVIO = addKeyword(EVENTS.ACTION)
.addAnswer('¿Desea confirmar el envío? 📩 Responda *"Sí"* ✅ o *"No"* ❌. Si responde "No", será redirigido al *MENÚ PRINCIPAL* 🔄', {capture: true}, 
  async(ctx, ctxFn) => {
    const input = ctx.body.toLocaleLowerCase()
    if(input == 'no'){
      await builderBotTyping(ctx, ctxFn.provider, 1500)
      return ctxFn.gotoFlow(menu)
    }
    try{
      const newTicket = {
        titulo: ctxFn.state.get('titulo'),
        descripcion: ctxFn.state.get('desc'),
        celular: ctxFn.state.get('celular'),
        tipo: ctxFn.state.get('tipo')
      }

      await withTyping(ctx, ctxFn.provider, async()=>{
        const response = await axios.post(createTicketUrl, newTicket)
        //console.log(response)
        await ctxFn.state.update({ticket_rpta: 'correcto'})
        await ctxFn.state.update({datos: response.data})
      })
    } catch(e){
      console.log(`Error en el servidor: ${e}`)
      await ctxFn.state.update({ticket_rpta: 'incorrecto'})
    }
  }
).addAction(
  async(ctx, ctxFn) => {
    const rpta_ticket = ctxFn.state.get('ticket_rpta')
    if(rpta_ticket === 'correcto'){
      await builderBotTyping(ctx, ctxFn.provider, 1500)
      await ctxFn.flowDynamic('Ticket generado correctamente')
      const ticket_datos = ctxFn.state.get('datos')
      const ticket_codigo = ticket_datos.data.codigo_ticket
      await ctxFn.flowDynamic(`Código del ticket: ${ticket_codigo}`)
      await builderBotTyping(ctx, ctxFn.provider, 1500)
      const nombrePersona = `${ticket_datos.data.persona_encargada.user.first_name} ${ticket_datos.data.persona_encargada.user.last_name}`
      await ctxFn.flowDynamic(`Persona encargada de atenderte: ${nombrePersona}`)
      await builderBotTyping(ctx, ctxFn.provider, 1500)
      await ctxFn.flowDynamic('Redirigiendo al menú principal')
      return ctxFn.gotoFlow(menu)
    }
  }
)