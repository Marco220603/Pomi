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
        const { number, message, urlMedia} = req.body
        console.log(number)
        console.log(message)
        await bot.sendMessage(number, message, { media: urlMedia ?? null })
        return res.end('sended')
      }catch(error){
        console.log(`Error en el servidor: ${error}`)
        return res.end(`Error ${error}`)
      }
    })
  )

  adapterProvider.server.post(
    'v1/sendAnswer',
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
