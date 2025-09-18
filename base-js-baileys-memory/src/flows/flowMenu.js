import { EVENTS } from "@builderbot/bot";
import { addKeyword } from "@builderbot/bot";
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { generarTicket } from './flowTicket.js'
import { flowConsulta } from './flowConsulta.js'
// import { flowGestionTickets } from './flowGestionTickets.js'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const messageMenu = fs.readFileSync(
  path.join(__dirname, '../template/menu/menu.txt'),
  'utf-8'
)

export const menu = addKeyword(EVENTS.ACTION)
.addAnswer(messageMenu, {capture: true, delay:100},
  async(ctx, ctxFn) => {
    const opcion = ctx.body.trim()
    if(!["1", "2", "3", "4"].includes(opcion)){
      return ctxFn.fallBack('Respuesta no válida, por favor ingresar un número del *1 al 4*.')
    }
    switch(opcion){
      case "1":
        return ctxFn.gotoFlow(flowConsulta) // Hacer una consulta
      case "2":
        return ctxFn.gotoFlow(generarTicket) // Generar un ticket
      case "3":
        return ctxFn.flowDynamic('Pruebas')
        // return ctxFn.gotoFlow(flowGestionTickets) // Gestionar Tickets: Buscar por codigo de ticket
      case "4":
        return ctxFn.gotoFlow()
    }
  }
)