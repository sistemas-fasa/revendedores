<template>
  <main class="login-page">
    <section class="brand-panel" aria-label="Ferretería Avenida">
      <div class="brand-top"><img src="/logo.png" alt="Ferretería Avenida S.A." class="brand-logo" /></div>
      <div class="brand-content">
        <span class="eyebrow"><span></span> PORTAL DE VENTAS</span>
        <h1>Todo lo que buscás,<br /><em>en un solo lugar.</em></h1>
        <p>Encontrá productos y gestioná tus pedidos de forma simple.</p>
      </div>
      <div class="brand-bottom"><span>FERRETERÍA AVENIDA</span><span>Juntos hacemos más.</span></div>
      <div class="brand-mark" aria-hidden="true">A</div>
    </section>

    <section class="form-panel" aria-labelledby="login-title">
      <div class="form-wrap">
        <div class="mobile-brand"><img src="/logo.png" alt="Ferretería Avenida S.A." /></div>
        <div class="form-heading">
          <span class="form-eyebrow">PORTAL DE VENTAS</span>
          <h2 id="login-title">Qué bueno verte.</h2>
          <p>Ingresá tus datos para acceder a tu cuenta.</p>
        </div>
        <form @submit.prevent="handleSubmit">
          <div class="field">
            <label for="username">Usuario o código de cliente</label>
            <input id="username" v-model="username" name="username" type="text" autocomplete="username" required placeholder="Tu usuario o el código de tu factura" />
          </div>
          <div class="field">
            <label for="password">Contraseña</label>
            <div class="password-field">
              <input id="password" v-model="password" name="password" :type="showPassword ? 'text' : 'password'" autocomplete="current-password" required placeholder="Ingresá tu contraseña" />
              <button type="button" class="password-toggle" :aria-label="showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'" :aria-pressed="showPassword" @click="showPassword = !showPassword">
                <svg v-if="showPassword" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M3 3l18 18M10.6 10.6a2 2 0 002.8 2.8M9.9 5.2A10.8 10.8 0 0112 5c4.5 0 8.2 2.9 9.5 7a11.3 11.3 0 01-3.1 4.6M6.3 6.3A11.3 11.3 0 002.5 12c1.3 4.1 5 7 9.5 7 1.5 0 2.9-.3 4.1-.9" /></svg>
                <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M2.5 12C3.8 7.9 7.5 5 12 5s8.2 2.9 9.5 7c-1.3 4.1-5 7-9.5 7s-8.2-2.9-9.5-7z"/><circle cx="12" cy="12" r="3" /></svg>
              </button>
            </div>
          </div>
          <div v-if="error" class="error-message" role="alert">{{ error }}</div>
          <button type="submit" class="submit-button" :disabled="loading">
            <span>{{ loading ? 'Ingresando...' : 'Ingresar a mi cuenta' }}</span>
            <svg v-if="!loading" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M5 12h14m-6-6l6 6-6 6" /></svg>
            <span v-else class="spinner" aria-hidden="true"></span>
          </button>

          <div class="register-banner" role="note" aria-label="Solicitar alta por WhatsApp">
            <div class="register-text">
              <strong>¿Todavía no estás registrado?</strong>
              <span>Escribinos por WhatsApp y te damos de alta.</span>
            </div>
            <a
              class="whatsapp-button"
              href="https://wa.me/5493743400209?text=Hola%2C%20quiero%20solicitar%20el%20alta%20en%20el%20Portal%20de%20Ventas%20de%20Ferreter%C3%ADa%20Avenida."
              target="_blank"
              rel="noopener"
            >
              <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm0 2a8 8 0 1 1-4.1 14.9l-.3-.2-2.9.8.8-2.8-.2-.3A8 8 0 0 1 12 4zm-3.2 4c-.2 0-.5 0-.7.3-.2.3-.9.9-.9 2.2s.9 2.5 1.1 2.7c.1.2 1.9 3.1 4.8 4.1 2.4.9 2.9.7 3.4.7.5-.1 1.7-.7 1.9-1.4.2-.6.2-1.2.2-1.3-.1-.1-.3-.2-.6-.3l-2-1c-.3-.1-.5-.2-.7.1l-.9 1.1c-.2.2-.3.2-.6.1-.9-.4-1.7-.9-2.4-1.6-.6-.6-1-1.2-1.1-1.4-.1-.2 0-.4.1-.5l.5-.6c.2-.2.2-.4.3-.6.1-.2 0-.4 0-.6L8.6 6.2c-.2-.2-.4-.2-.8-.2z"/></svg>
              <span>Solicitar alta por WhatsApp</span>
            </a>
          </div>

          <div class="recovery-toggle">
            <button type="button" class="link-button" @click="showRecovery = !showRecovery">
              ¿Olvidaste tu contraseña?
            </button>
          </div>

          <div v-if="showRecovery" class="recovery-panel">
            <p>Ingresá tu usuario y te enviamos un link a tu email registrado para crear una nueva.</p>
            <div class="recovery-row">
              <input
                v-model="recoveryId"
                type="text"
                placeholder="Tu usuario o email"
                aria-label="Usuario o email para recuperar contraseña"
              />
              <button
                type="button"
                class="secondary-button"
                @click="handleRecovery"
                :disabled="recoveryLoading"
              >
                {{ recoveryLoading ? 'Enviando...' : 'Enviar link' }}
              </button>
            </div>
            <div v-if="recoveryMsg" class="success-message" role="status">{{ recoveryMsg }}</div>
            <div v-if="recoveryError" class="error-message" role="alert">{{ recoveryError }}</div>
          </div>
        </form>
        <div class="activation-toggle">
          <router-link to="/activar" class="link-button">¿Primera vez? Activá tu cuenta</router-link>
        </div>
        <p class="form-footer">Ferretería Avenida <span>·</span> Portal de ventas</p>
      </div>
    </section>
  </main>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import api from '../services/api'

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const showPassword = ref(false)
const authStore = useAuthStore()
const router = useRouter()

const showRecovery = ref(false)
const recoveryId = ref('')
const recoveryMsg = ref('')
const recoveryError = ref('')
const recoveryLoading = ref(false)

const handleSubmit = async () => {
  error.value = ''
  loading.value = true
  try {
    await authStore.login(username.value, password.value)
  } catch (err) {
    if (err.response?.status === 401) {
      error.value = 'Usuario o contraseña incorrectos.'
    } else if (err.response?.status === 409 && err.response?.data?.code === 'activacion_pendiente') {
      router.push({ name: 'activar-cuenta', query: { codigo: username.value } })
      return
    } else {
      error.value = 'No se pudo conectar con el servidor. Intenta más tarde.'
    }
  } finally {
    loading.value = false
  }
}

const handleRecovery = async () => {
  recoveryMsg.value = ''
  recoveryError.value = ''
  if (!recoveryId.value.trim()) {
    recoveryError.value = 'Ingresá tu usuario o email.'
    return
  }
  recoveryLoading.value = true
  try {
    const { data } = await api.post('/api/password-reset/', {
      identificador: recoveryId.value.trim(),
    })
    recoveryMsg.value = data.message
  } catch (err) {
    recoveryError.value = err.response?.data?.error || 'No se pudo enviar el email. Intentá más tarde.'
  } finally {
    recoveryLoading.value = false
  }
}
</script>

<style scoped>
.login-page { min-height: 100vh; min-height: 100dvh; display: grid; grid-template-columns: 1fr 1fr; background: #f8f9fa; color: #202735; font-family: 'Segoe UI', Arial, sans-serif; }
.brand-panel { position: relative; overflow: hidden; display: flex; flex-direction: column; justify-content: space-between; padding: 52px clamp(40px, 6vw, 104px); background: #a90016; color: white; isolation: isolate; }
.brand-panel::before { content: ''; position: absolute; inset: 0; z-index: -2; background: linear-gradient(145deg, #df001b 0%, #b90018 48%, #840013 100%); }
.brand-panel::after { content: ''; position: absolute; width: 75%; aspect-ratio: 1; right: -30%; top: -25%; border: 1px solid rgba(255,255,255,.18); border-radius: 50%; box-shadow: 0 0 0 65px rgba(255,255,255,.035), 0 0 0 130px rgba(255,255,255,.025); z-index: -1; }
.brand-top { align-self: flex-start; background: #fff; padding: 14px 20px; border-radius: 5px; }
.brand-logo { display: block; width: 218px; height: auto; }
.brand-content { position: relative; padding: 80px 0; max-width: 600px; }
.eyebrow, .form-eyebrow { display: flex; align-items: center; gap: 10px; font-size: 11px; font-weight: 700; letter-spacing: .17em; }
.eyebrow { color: rgba(255,255,255,.78); }
.eyebrow span { width: 26px; height: 2px; background: #fff; }
.brand-content h1 { margin: 26px 0 22px; font-size: clamp(42px, 4.6vw, 72px); letter-spacing: -.055em; line-height: 1.07; font-weight: 700; }
.brand-content h1 em { font-style: normal; color: #ffd7d9; }
.brand-content p { max-width: 370px; margin: 0; color: rgba(255,255,255,.82); font-size: 17px; line-height: 1.7; }
.brand-bottom { display: flex; justify-content: space-between; gap: 20px; padding-top: 22px; border-top: 1px solid rgba(255,255,255,.25); color: rgba(255,255,255,.75); font-size: 11px; letter-spacing: .08em; }
.brand-bottom span:first-child { font-weight: 700; }
.brand-mark { position: absolute; right: -20px; bottom: -180px; z-index: -1; color: rgba(255,255,255,.045); font-size: clamp(390px, 45vw, 680px); font-weight: 900; line-height: 1; pointer-events: none; }
.form-panel { display: flex; align-items: center; justify-content: center; padding: 64px 32px; }
.form-wrap { width: 100%; max-width: 400px; }
.mobile-brand { display: none; }
.form-eyebrow { color: #bb0019; }
.form-heading h2 { margin: 18px 0 10px; font-size: clamp(32px, 3vw, 42px); letter-spacing: -.045em; line-height: 1.15; font-weight: 700; }
.form-heading p { margin: 0; color: #707988; font-size: 15px; line-height: 1.6; }
form { margin-top: 44px; }
.field { margin-bottom: 23px; }
.field label { display: block; margin-bottom: 9px; color: #313b49; font-size: 13px; font-weight: 650; }
.field input { width: 100%; height: 56px; box-sizing: border-box; border: 1px solid #dce0e5; border-radius: 8px; background: #fff; color: #202735; font: inherit; font-size: 15px; padding: 0 16px; transition: border-color .2s, box-shadow .2s; }
.field input::placeholder { color: #a2a9b3; }
.field input:focus { outline: none; border-color: #be001a; box-shadow: 0 0 0 3px rgba(190,0,26,.12); }
.password-field { position: relative; }
.password-field input { padding-right: 54px; }
.password-toggle { position: absolute; right: 5px; top: 5px; width: 46px; height: 46px; display: grid; place-items: center; border: 0; background: transparent; color: #8b95a2; cursor: pointer; border-radius: 6px; }
.password-toggle:hover { color: #b90018; }
.password-toggle:focus-visible, .submit-button:focus-visible { outline: 3px solid #ec8390; outline-offset: 3px; }
.password-toggle svg, .submit-button svg { width: 20px; height: 20px; }
.submit-button { display: flex; align-items: center; justify-content: center; gap: 12px; width: 100%; min-height: 56px; margin-top: 32px; border: 0; border-radius: 8px; background: #c5001a; color: white; font: inherit; font-weight: 700; font-size: 15px; cursor: pointer; box-shadow: 0 8px 20px rgba(174,0,23,.16); transition: background .2s, transform .2s; }
.submit-button:hover:not(:disabled) { background: #a90016; transform: translateY(-1px); }
.submit-button:disabled { opacity: .7; cursor: wait; }
.spinner { width: 17px; height: 17px; border: 2px solid rgba(255,255,255,.4); border-top-color: #fff; border-radius: 50%; animation: spin .8s linear infinite; }
.error-message { margin-top: 4px; padding: 13px 15px; border: 1px solid #f1c3c9; border-radius: 8px; background: #fff1f2; color: #a90016; font-size: 14px; line-height: 1.4; }
.recovery-toggle { margin-top: 20px; text-align: center; }
.register-banner { margin-top: 22px; padding: 18px; border: 1.5px dashed #16a34a; border-radius: 10px; background: #f0fdf4; text-align: center; }
.register-text strong { display: block; color: #14532d; font-size: 15px; font-weight: 750; }
.register-text span { display: block; margin-top: 4px; color: #4d5a6b; font-size: 13.5px; line-height: 1.5; }
.whatsapp-button { display: flex; align-items: center; justify-content: center; gap: 10px; width: 100%; box-sizing: border-box; margin-top: 14px; min-height: 52px; padding: 12px 16px; border: 0; border-radius: 8px; background: #22c55e; color: #fff; font: inherit; font-weight: 700; font-size: 15px; text-decoration: none; cursor: pointer; box-shadow: 0 8px 20px rgba(34,197,94,.25); transition: background .2s, transform .2s; }
.whatsapp-button:hover { background: #16a34a; transform: translateY(-1px); }
.whatsapp-button:focus-visible { outline: 3px solid #86efac; outline-offset: 3px; }
.whatsapp-button svg { width: 22px; height: 22px; flex-shrink: 0; }
.link-button { border: 0; background: none; padding: 4px; color: #b90018; font: inherit; font-size: 14px; font-weight: 650; cursor: pointer; }
.link-button:hover { text-decoration: underline; }
.link-button:focus-visible, .secondary-button:focus-visible { outline: 3px solid #ec8390; outline-offset: 3px; }
.recovery-panel { margin-top: 16px; padding: 18px; border: 1px solid #dce0e5; border-radius: 8px; background: #fff; }
.recovery-panel > p { margin: 0 0 12px; color: #707988; font-size: 14px; line-height: 1.5; }
.recovery-row { display: flex; gap: 10px; }
.recovery-row input { flex: 1; min-width: 0; height: 48px; box-sizing: border-box; border: 1px solid #dce0e5; border-radius: 8px; background: #fff; color: #202735; font: inherit; font-size: 14px; padding: 0 14px; }
.recovery-row input::placeholder { color: #a2a9b3; }
.recovery-row input:focus { outline: none; border-color: #be001a; box-shadow: 0 0 0 3px rgba(190,0,26,.12); }
.secondary-button { border: 0; border-radius: 8px; background: #313b49; color: #fff; font: inherit; font-size: 14px; font-weight: 700; padding: 0 18px; cursor: pointer; white-space: nowrap; }
.secondary-button:hover:not(:disabled) { background: #202735; }
.secondary-button:disabled { opacity: .7; cursor: wait; }
.success-message { margin-top: 12px; padding: 13px 15px; border: 1px solid #bfe3c9; border-radius: 8px; background: #eef9f0; color: #166534; font-size: 14px; line-height: 1.4; }
.activation-toggle { margin-top: 16px; text-align: center; }
.recovery-panel .error-message { margin-top: 12px; }
.form-footer { margin: 55px 0 0; color: #929aa5; font-size: 12px; }
.form-footer span { padding: 0 5px; color: #c5001a; }
@keyframes spin { to { transform: rotate(360deg); } }
@media (max-width: 767px) {
  .login-page { display: block; background: #f8f9fa; }
  .brand-panel { min-height: 240px; padding: 30px 26px; }
  .brand-top { padding: 10px 14px; }
  .brand-logo { width: 165px; }
  .brand-content { padding: 46px 0 4px; }
  .brand-content h1 { margin: 15px 0 0; font-size: clamp(32px, 8vw, 42px); }
  .brand-content p, .brand-bottom, .brand-mark { display: none; }
  .form-panel { padding: 48px 26px 50px; }
  .form-heading h2 { font-size: 32px; }
  form { margin-top: 32px; }
  .form-footer { margin-top: 40px; }
  .recovery-row { flex-direction: column; }
  .secondary-button { min-height: 48px; }
}
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: .01ms !important; animation-iteration-count: 1 !important; transition-duration: .01ms !important; } }
</style>
