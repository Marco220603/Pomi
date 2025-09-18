import { EVENTS } from "@builderbot/bot";
import { addKeyword } from "@builderbot/bot";
import axios from "axios";
import dotenv from 'dotenv'
import { menu } from './flowMenu.js'

dotenv.config()
const consultRasaURL = process.env['rasa-consult']

export const flowConsulta = addKeyword(EVENTS.ACTION)
.addAnswer('Porfavor ingrse tu consulta', {capture:true},
  async(ctx, ctxFn) => {
    if(!ctx.body || ctx.body.trim().length < 1){
      return ctxFn.fallBack('Consulta demasiado corta. Intenta escribir una pregunta completa')
    }
    try {
      const response = await axios.post(consultRasaURL, {
        "sender": ctxFn.state.get('sender'),
        "from_number": ctx.from.slice(-9),
        "text": ctx.body
      })

      console.log(response)
      const respuestaDjango = response.data
      const respuestaRasa = respuestaDjango.response
      await ctxFn.state.update({respuestaRasa: respuestaRasa})
    } catch (error) {
      console.log(`Error: ${error}`)
      await ctxFn.state.update({respuestaRasa: 'error'})
    }
  }
)
.addAction(
  async(ctx, ctxFn) => {
    const respuesta = ctxFn.state.get('respuestaRasa')
    if (respuesta == 'error') return ctxFn.flowDynamic('❌ Ocurrió un error al procesar tu consulta. Inténtalo más tarde.')
    await ctxFn.flowDynamic(`${respuesta}`)
  }
)
.addAnswer('¿Desea hacer otra consulta?(Responde *si* o *no*)', {capture:true},
  async(ctx, ctxFn) => {
    const input = ctx.body.trim().toLowerCase()
    if(!["si","no"].includes(input)){
      return ctxFn.fallBack('Responde con "si" o "no" por favor.')
    }
    if(input == "si") return ctxFn.gotoFlow(flowConsulta)
    if(input == "no") return ctxFn.gotoFlow(menu)
  }
)