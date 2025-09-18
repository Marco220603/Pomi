/**
 * Módulo de Animación de Escritura para Baileys + BuilderBot (ES6 Modules)
 *
 * - Normaliza JIDs (evita errores de jidDecode undefined)
 * - Prioriza ctx.key?.remoteJid sobre ctx.from
 * - Maneja presenceSubscribe/available/composing con tolerancia a fallos
 */

// ==== Utilidades ====

/** Delay simple */
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/** Normaliza un id a JID válido para Baileys */
const normalizeJid = (id) => {
  if (!id) throw new Error('JID vacío/indefinido');

  // Ya es JID válido
  if (/@(s\.whatsapp\.net|g\.us|broadcast)$/.test(id)) return id;

  const clean = String(id).trim();

  // Grupo (tiene guion tipo 12345-67890)
  if (clean.includes('-')) return `${clean}@g.us`;

  // Persona 1:1
  const digits = clean.replace(/[^\d]/g, '');
  if (!digits) throw new Error(`No se pudo normalizar JID desde "${id}"`);
  return `${digits}@s.whatsapp.net`;
};

/** Evita destinos no soportados para presencia */
const isPresenceAllowed = (jid) => /@(s\.whatsapp\.net|g\.us)$/.test(jid);

// ==== Manager de typing ====

class TypingAnimationManager {
  constructor() {
    /** @type {Map<string, boolean>} */
    this.activeTyping = new Map();
    /** @type {Map<string, NodeJS.Timeout>} */
    this.typingTimeouts = new Map();
  }

  /**
   * Muestra animación "escribiendo..." por un tiempo
   * @param {Object} sock - Socket Baileys
   * @param {string} chatId - JID o número sin sufijo
   * @param {number} duration - ms (default 3000)
   */
  async showTyping(sock, chatId, duration = 3000) {
    try {
      const jid = normalizeJid(chatId);
      if (!isPresenceAllowed(jid)) return;

      // Cancelar cualquier animación previa en este chat
      await this.stopTyping(sock, jid);

      // Marcar como activo
      this.activeTyping.set(jid, true);

      // Suscribirse y preparar presencia
      try { await sock.presenceSubscribe?.(jid); } catch (_) {}
      try { await sock.sendPresenceUpdate?.('available', jid); } catch (_) {}

      // Enviar "composing"
      await sock.sendPresenceUpdate('composing', jid);

      console.log(`[TYPING] Iniciada animación de escritura para ${jid} por ${duration}ms`);

      // Programar detención automática
      const timeout = setTimeout(async () => {
        await this.stopTyping(sock, jid);
      }, duration);

      this.typingTimeouts.set(jid, timeout);
    } catch (error) {
      console.error('[TYPING ERROR] Error al mostrar animación de escritura:', error);
      await this.stopTyping(sock, chatId);
    }
  }

  /**
   * Detiene animación "escribiendo..." para un chat
   * @param {Object} sock - Socket Baileys
   * @param {string} chatId - JID o número sin sufijo
   */
  async stopTyping(sock, chatId) {
    try {
      const jid = normalizeJid(chatId);

      // Limpiar timeout
      if (this.typingTimeouts.has(jid)) {
        clearTimeout(this.typingTimeouts.get(jid));
        this.typingTimeouts.delete(jid);
      }

      // Cambiar presencia si estaba activo
      if (this.activeTyping.has(jid)) {
        try { await sock.sendPresenceUpdate?.('available', jid); } catch (_) {}
        this.activeTyping.delete(jid);
        console.log(`[TYPING] Detenida animación de escritura para ${jid}`);
      }
    } catch (error) {
      console.error('[TYPING ERROR] Error al detener animación de escritura:', error);
    }
  }

  /**
   * Mantiene "composing" renovándose hasta que una promesa se resuelva
   * @param {Object} sock
   * @param {string} chatId
   * @param {Promise<any>} promise
   * @param {number} intervalMs
   */
  async typingUntilPromiseResolves(sock, chatId, promise, intervalMs = 2000) {
    let typingInterval;
    const jid = normalizeJid(chatId);

    try {
      console.log(`[TYPING] Iniciando escritura continua para ${jid} hasta resolver promesa`);

      // Primera animación un poco más larga para cubrir la primera renovación
      await this.showTyping(sock, jid, intervalMs + 500);

      // Renovación periódica del "composing"
      typingInterval = setInterval(async () => {
        if (this.activeTyping.has(jid)) {
          try {
            await sock.sendPresenceUpdate('composing', jid);
            console.log(`[TYPING] Renovando animación para ${jid}`);
          } catch (error) {
            console.error('[TYPING ERROR] Error renovando typing:', error);
          }
        }
      }, intervalMs);

      const result = await promise;

      // Limpieza
      clearInterval(typingInterval);
      await this.stopTyping(sock, jid);
      console.log(`[TYPING] Promesa resuelta, deteniendo animación para ${jid}`);

      return result;
    } catch (error) {
      if (typingInterval) clearInterval(typingInterval);
      await this.stopTyping(sock, jid);
      console.error('[TYPING ERROR] Error en typingUntilPromiseResolves:', error);
      throw error;
    }
  }

  /**
   * Simula escritura basada en longitud del mensaje
   * @param {Object} sock
   * @param {string} chatId
   * @param {string} message
   * @param {number} wpmSpeed
   */
  async simulateRealisticTyping(sock, chatId, message, wpmSpeed = 40) {
    try {
      const words = message.trim().split(/\s+/).length;
      const typingTimeMs = Math.max((words / wpmSpeed) * 60 * 1000, 1000);
      console.log(`[TYPING] Simulando escritura realista para ${words} palabras en ${typingTimeMs}ms`);
      await this.showTyping(sock, chatId, typingTimeMs);
    } catch (error) {
      console.error('[TYPING ERROR] Error en simulateRealisticTyping:', error);
    }
  }

  /**
   * Integración con BuilderBot
   * @param {Object} ctx
   * @param {Object} provider
   * @param {number} duration
   */
  async typingForBuilderBot(ctx, provider, duration = 3000) {
    try {
      const raw = ctx?.key?.remoteJid || ctx?.from; // PRIORIDAD remoteJid
      const sock = provider.vendor;
      await this.showTyping(sock, raw, duration);
    } catch (error) {
      console.error('[TYPING ERROR] Error en integración con BuilderBot:', error);
    }
  }

  /**
   * Ejecuta una función async mostrando typing hasta que termine
   * @param {Object} ctx
   * @param {Object} provider
   * @param {Function} asyncFunction
   * @param {Object} options { interval, showInitial }
   */
  async withTypingAnimation(ctx, provider, asyncFunction, options = {}) {
    const { interval = 2000, showInitial = true } = options;
    const raw = ctx?.key?.remoteJid || ctx?.from; // PRIORIDAD remoteJid
    const sock = provider.vendor;

    try {
      if (showInitial) {
        console.log(`[TYPING] Iniciando animación para función asíncrona en ${raw}`);
      }

      const functionPromise = asyncFunction();
      return await this.typingUntilPromiseResolves(sock, raw, functionPromise, interval);
    } catch (error) {
      await this.stopTyping(sock, raw);
      console.error('[TYPING ERROR] Error en withTypingAnimation:', error);
      throw error;
    }
  }

  /**
   * Limpia cualquier animación activa
   * @param {Object} sock
   */
  async cleanupAllTyping(sock) {
    console.log('[TYPING] Limpiando todas las animaciones activas...');

    for (const timeout of this.typingTimeouts.values()) {
      clearTimeout(timeout);
    }
    this.typingTimeouts.clear();

    const promises = Array.from(this.activeTyping.keys()).map((chatId) =>
      this.stopTyping(sock, chatId)
    );

    await Promise.allSettled(promises);
    console.log('[TYPING] Limpieza completada');
  }

  /**
   * ¿Hay animación activa para este chat?
   * @param {string} chatId
   */
  isTypingActive(chatId) {
    try {
      const jid = normalizeJid(chatId);
      return this.activeTyping.has(jid);
    } catch {
      return false;
    }
  }
}

// Instancia global
const typingManager = new TypingAnimationManager();

// ===== Exportaciones ES6 =====
export { typingManager };
export { delay };

/** API simple */
export const showTyping = (sock, chatId, duration = 3000) =>
  typingManager.showTyping(sock, chatId, duration);

export const stopTyping = (sock, chatId) =>
  typingManager.stopTyping(sock, chatId);

export const typingUntilResolve = (sock, chatId, promise, intervalMs = 2000) =>
  typingManager.typingUntilPromiseResolves(sock, chatId, promise, intervalMs);

export const builderBotTyping = (ctx, provider, duration = 3000) =>
  typingManager.typingForBuilderBot(ctx, provider, duration);

export const withTyping = (ctx, provider, asyncFn, options = {}) =>
  typingManager.withTypingAnimation(ctx, provider, asyncFn, options);

export const realisticTyping = (sock, chatId, message, wpm = 40) =>
  typingManager.simulateRealisticTyping(sock, chatId, message, wpm);

/* ========= Ejemplos de uso (referencia) =========

1) En un flow simple:
import { builderBotTyping } from '../behavior/typing.js';
.addAction(async (ctx, { provider }) => {
  await builderBotTyping(ctx, provider, 2000);
})

2) Esperando una API:
import { withTyping } from '../behavior/typing.js';
.addAction(async (ctx, { provider, flowDynamic }) => {
  const data = await withTyping(ctx, provider, async () => {
    const r = await fetch('https://api.ejemplo.com').then(x => x.json());
    return r;
  });
  return flowDynamic(`Listo: ${JSON.stringify(data)}`);
})

3) Control manual:
import { showTyping, stopTyping, delay } from '../behavior/typing.js';
.addAction(async (ctx, { provider }) => {
  const sock = provider.vendor;
  await showTyping(sock, ctx.key?.remoteJid || ctx.from, 5000);
  await delay(3000);
  await stopTyping(sock, ctx.key?.remoteJid || ctx.from);
})

================================================== */
