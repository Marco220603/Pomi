import { addKeyword, EVENTS } from '@builderbot/bot'
import fs from 'fs'
import dotenv from 'dotenv'
import path from 'path'
import { fileURLToPath } from 'url'
import axios from 'axios'

// Animación de Typing
import { 
    //builderBotTyping,     // ← Para uso simple en flows
    withTyping,           // ← Para APIs/procesos largos
    //realisticTyping,      // ← Para mensajes largos
    //showTyping,           // ← Control básico
    //stopTyping,           // ← Detener animación
    //typingUntilResolve,   // ← Esperar promesas
    //typingManager,        // ← Control avanzado
    //delay                 // ← Función delay personalizada
} from './../behavior/typing.js';

// Flujos
import { menu } from './flowMenu.js'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const messageWelcome = fs.readFileSync(
  path.join(__dirname, '../template/Login/inicio.txt'),
  'utf-8'
)
dotenv.config()
const verifyStudentUrl = process.env['verify-student']

//flujo de Bienvenida 
export const mensajeBienvenida = addKeyword(EVENTS.WELCOME)
.addAnswer(messageWelcome, {delay: 500, capture: true}, 
  async (ctx, ctxFn) => {
    const codigo_upc = ctx.body.trim().toLowerCase()
    const phone_upc = ctx.from.slice(-9)
    const validador = validateCode(codigo_upc)
    if(!validador){return ctxFn.fallBack('❌ Código no válido. Ingresa un código correcto (Ej: U202012345): ')}
    try{
      await withTyping(ctx, ctxFn.provider, async () => {
        const response = await axios.post(verifyStudentUrl, {
          "code": codigo_upc,
          "phone": phone_upc
        })
        console.log(response.data)
        await ctxFn.state.update({datos: response.data})
        await ctxFn.state.update({celular: phone_upc})
        await ctxFn.state.update({sender: codigo_upc})
      })
      await ctxFn.gotoFlow(validarUsuario)
    } catch(error){
      console.log(`Error: ${error}`)
      await ctxFn.flowDynamic('Lo siento, tenemos problemas de conexión, intente más tarde')
    }
  } 
)

export const validarUsuario = addKeyword(EVENTS.ACTION)
.addAction(
  async (ctx, ctxFn) => {
    const usuarios_datos = ctxFn.state.get('datos')
    if(!usuarios_datos.success){return ctxFn.flowDynamic('Lo sentimos, el código del estudiante brindado no se encuentra registrado para este semestre. Si piensa que es un error contacte con Soporte, gracias.')}
    if(!usuarios_datos.data.activo){return ctxFn.flowDynamic('Lo sentimos, el código de estudiante no esta activo para este semestre. Si piensa que es un error contacte con Soporte, gracias.')}
    await ctxFn.flowDynamic('✅ ¡Código validado correctamente! 🎓')
    return ctxFn.gotoFlow(menu)
  }
)

// Validador: U + 9 dígitos
function validateCode(codigo) {
  const norm = String(codigo)
    .normalize('NFKD')
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, '') // quita espacios, guiones, etc.
  return /^U[A-Z0-9]{9}$/.test(norm)
}