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
const verifyStudentUrl = process.env.VERIFY_STUDENT_URL
if (!verifyStudentUrl) {
  console.error('FATAL: VERIFY_STUDENT_URL no está definida en .env')
}

//flujo de Bienvenida 
export const mensajeBienvenida = addKeyword(EVENTS.WELCOME)
  .addAnswer(messageWelcome, { delay: 500, capture: true }, 
    async (ctx, ctxFn) => {
      const codigo_upc = ctx.body.trim().toLowerCase()
      console.log(codigo_upc)
      const phone_upc = ctx.from.slice(-9)
      const validador = validateCode(codigo_upc)
      console.log(validador)
      if (!validador) {
        return ctxFn.fallBack('❌ Código no válido. Ingresa un código correcto (Ej: U202012345): ')
      }

      try {
        await withTyping(ctx, ctxFn.provider, async () => {
          const resp = await axios.post(
            verifyStudentUrl,
            { code: codigo_upc, phone: phone_upc },
            {
              timeout: 5000,                 // evita colgarse
              validateStatus: () => true      // << NO lances error por 4xx/5xx
            }
          )

          // Manejo explícito por status
          if (resp.status >= 500) {
            await ctxFn.flowDynamic('😵‍💫 El servicio está con problemas. Intenta en unos minutos.')
            return
          }
          if (resp.status === 404) {
            await ctxFn.flowDynamic('❌ No encontramos tu código. Verifica y vuelve a intentarlo.')
            return
          }
          if (resp.status === 400) {
            await ctxFn.flowDynamic('❌ Formato de código inválido. Debe ser como U202012345.')
            return
          }
          if (resp.status !== 200) {
            await ctxFn.flowDynamic(`⚠️ No pudimos validar (status ${resp.status}). Intenta más tarde.`)
            return
          }

          // 200 OK
          const data = resp.data
          await ctxFn.state.update({ datos: data, celular: phone_upc, sender: codigo_upc })
          await ctxFn.gotoFlow(validarUsuario)
        })
      } catch (error) {
        // Errores de red/DNS/timeout
        console.log('AXIOS ERROR:', {
          message: error.message,
          code: error.code,
          status: error.response?.status
        })
        await ctxFn.flowDynamic('🌐 No hay conexión con el validador ahora mismo. Intenta más tarde.')
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
    .replace(/[^A-Z0-9]/g, '');
  console.log({ raw: codigo, norm, len: norm.length });
  return /^U[A-Z0-9]{9}$/.test(norm);
}