import { createBot, createProvider, createFlow} from '@builderbot/bot'
import { MemoryDB as Database } from '@builderbot/bot'
import { BaileysProvider as Provider } from '@builderbot/provider-baileys'

// Flujos
import { mensajeBienvenida, validarUsuario } from './flows/flowLogin.js'
import { menu } from './flows/flowMenu.js' 
import { generarTicket, flowTicket_TIPO, flowTicket_DESC, flowTicket_ENVIO,  } from './flows/flowTicket.js'
import { flowConsulta } from './flows/flowConsulta.js'

const PORT = process.env.PORT ?? 3008

/** ------------------ Flujos ------------------ */

const main = async () => {
  const adapterFlow = createFlow([mensajeBienvenida, validarUsuario, menu, generarTicket, flowTicket_TIPO, flowTicket_DESC, flowTicket_ENVIO, flowConsulta])
  const adapterProvider = createProvider(Provider)
  const adapterDB = new Database()

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

  httpServer(+PORT)
}

main()
