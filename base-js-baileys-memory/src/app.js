import { createBot, createProvider, createFlow} from '@builderbot/bot'
import { BaileysProvider as Provider } from '@builderbot/provider-baileys'
import { MongoAdapter as Database } from '@builderbot/database-mongo'
import dotenv from 'dotenv'

// Cargar variables de entorno
dotenv.config()

// Flujos
import { mensajeBienvenida, validarUsuario } from './flows/flowLogin.js'
import { menu } from './flows/flowMenu.js' 
import { generarTicket, flowTicket_TIPO, flowTicket_DESC, flowTicket_ENVIO,  } from './flows/flowTicket.js'
import { flowConsulta } from './flows/flowConsulta.js'

const PORT = process.env.PORT ?? 3008

/** ------------------ Flujos ------------------ */

const main = async () => {
  const adapterFlow = createFlow([mensajeBienvenida, validarUsuario, menu, generarTicket, flowTicket_TIPO, flowTicket_DESC, flowTicket_ENVIO, flowConsulta])
  const adapterProvider = createProvider(Provider,{
    version: [2, 3000, 1025190524]
  })
  
  const adapterDB = new Database({
    dbUri: process.env.MONGO_DB_URI,
    dbName: process.env.MONGO_DB_NAME,
  })

  const { handleCtx, httpServer } = await createBot({
    flow: adapterFlow,
    provider: adapterProvider,
    database: adapterDB,
  }, {
    queue: {
      timeout: 30000,        // 30 s de tope por mensaje: sobrado para esos ~7 s de tabla
      concurrencyLimit: 15    // permite hasta 20 tareas en paralelo (tus ~15 usuarios caben)
    }
  })

  // Health check endpoint
  adapterProvider.server.get('/health', (req, res) => {
    res.writeHead(200, { 'Content-Type': 'application/json' })
    return res.end(JSON.stringify({ 
      status: 'ok', 
      timestamp: new Date().toISOString(),
      message: 'Bot servidor funcionando correctamente'
    }))
  })

  adapterProvider.server.post(
    '/v1/messages',
    handleCtx(async (bot, req, res) => {
      const { number, message, urlMedia } = req.body
      await bot.sendMessage(number, message, { media: urlMedia ?? null })
      return res.end('sended')
    })
  )

  adapterProvider.server.post(
    '/v1/register',
    handleCtx(async (bot, req, res) => {
      const { number, name } = req.body
      await bot.dispatch('REGISTER_FLOW', { from: number, name })
      return res.end('trigger')
    })
  )

  adapterProvider.server.post(
    '/v1/samples',
    handleCtx(async (bot, req, res) => {
      const { number, name } = req.body
      await bot.dispatch('SAMPLES', { from: number, name })
      return res.end('trigger')
    })
  )

  adapterProvider.server.post(
    '/v1/blacklist',
    handleCtx(async (bot, req, res) => {
      const { number, intent } = req.body
      if (intent === 'remove') bot.blacklist.remove(number)
      if (intent === 'add') bot.blacklist.add(number)

      res.writeHead(200, { 'Content-Type': 'application/json' })
      return res.end(JSON.stringify({ status: 'ok', number, intent }))
    })
  )

  adapterProvider.server.post(
    '/v1/sendAdmin',
    handleCtx(async (bot, req, res) => {
      try{
        console.log('========== REQUEST /v1/sendAdmin ==========')
        console.log('Body recibido:', JSON.stringify(req.body, null, 2))
        
        const { number, message, urlMedia} = req.body
        
        if (!number || !message) {
          console.log('ERROR: Faltan campos requeridos')
          res.writeHead(400, { 'Content-Type': 'application/json' })
          return res.end(JSON.stringify({ 
            error: 'Campos requeridos faltantes',
            received: { number, message, urlMedia }
          }))
        }
        
        console.log('Enviando mensaje...')
        console.log('  → Número:', number)
        console.log('  → Mensaje:', message)
        console.log('  → Media:', urlMedia)
        
        await bot.sendMessage(number, message, { media: urlMedia ?? null })
        
        console.log('✓ Mensaje enviado exitosamente')
        res.writeHead(200, { 'Content-Type': 'application/json' })
        return res.end(JSON.stringify({ 
          status: 'success',
          message: 'Mensaje enviado correctamente'
        }))
      }catch(error){
        console.log('✗ ERROR al enviar mensaje:', error.message)
        console.error(error)
        res.writeHead(500, { 'Content-Type': 'application/json' })
        return res.end(JSON.stringify({ 
          error: error.message,
          stack: error.stack
        }))
      }
    })
  )

  adapterProvider.server.post(
    '/v1/sendAnswer',
    handleCtx(async (bot, req, res) => {
      try{
        const { number, message, urlMedia} = req.body
        console.log(number)
        console.log(message)
        await bot.sendMessage(number, message, {media: urlMedia ?? null})
        return res.end('Enviado')
      }catch(e){
        console.log(`Error ${e}`)
        return res.end('Error')
      }
    })
  )
  // Texto
  httpServer(+PORT)
}

main()
