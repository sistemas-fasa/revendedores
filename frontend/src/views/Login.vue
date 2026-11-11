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
        </form>
        <div class="activation-toggle">
          <button type="button" class="link-button" @click="abrirActivacion()">
            ¿Primera vez? Activá tu cuenta
          </button>
        </div>

        <div v-if="showActivation" class="activation-panel" role="dialog" aria-label="Activar cuenta">
          <p class="activation-steps">Paso {{ actPaso }} de 3</p>
          <h3 v-if="actPaso === 1">Activá tu cuenta</h3>
          <h3 v-if="actPaso === 2">Verificá que sos vos</h3>
          <h3 v-if="actPaso === 3">Creá tu contraseña</h3>

          <div v-if="actPaso === 1">
            <p class="activation-help">Ingresá el código de cliente de tu factura. Te pediremos tu email y WhatsApp para enviarte un código de verificación.</p>
            <div class="field">
              <label for="act-codigo">Código de cliente</label>
              <input id="act-codigo" v-model="actCodigo" type="text" inputmode="numeric" placeholder="Ej: 40" />
            </div>
          </div>

          <div v-if="actPaso === 2">
            <p class="activation-help">Hola, <strong>{{ actNombre }}</strong>. Te enviamos el mismo código por email<span v-if="actEmailMask"> ({{ actEmailMask }})</span> y WhatsApp<span v-if="actWhatsappMask"> ({{ actWhatsappMask }})</span>.</p>
            <div v-if="!actEnviado">
              <div class="field">
                <label for="act-email">Email</label>
                <input id="act-email" v-model="actEmail" type="email" autocomplete="email" placeholder="tu@email.com" />
              </div>
              <div class="field">
                <label for="act-wpp">WhatsApp (móvil argentino)</label>
                <input id="act-wpp" v-model="actWhatsapp" type="tel" autocomplete="tel" placeholder="11-1234-5678" />
              </div>
            </div>
            <div v-else>
              <div class="field">
                <label for="act-otp">Código de verificación</label>
                <input id="act-otp" v-model="actOtp" type="text" inputmode="numeric" maxlength="6" placeholder="6 dígitos" />
              </div>
              <p v-if="actCanales.whatsapp === 'omitido'" class="activation-help">WhatsApp no disponible: revisá tu email.</p>
            </div>
          </div>

          <div v-if="actPaso === 3">
            <p class="activation-help">Código correcto. Creá tu contraseña para entrar al portal.</p>
            <div class="field">
              <label for="act-p1">Nueva contraseña</label>
              <input id="act-p1" v-model="actPassword1" type="password" autocomplete="new-password" placeholder="Mínimo 8 caracteres" />
            </div>
            <div class="field">
              <label for="act-p2">Repetí la contraseña</label>
              <input id="act-p2" v-model="actPassword2" type="password" autocomplete="new-password" placeholder="Igual que arriba" />
            </div>
          </div>

          <div v-if="actError" class="error-message" role="alert">{{ actError }}</div>
          <div v-if="actMsg" class="success-message" role="status">{{ actMsg }}</div>

          <div class="activation-actions">
            <button
              v-if="actPaso === 1"
              type="button" class="submit-button" :disabled="actLoading"
              @click="actIniciar"
            ><span>{{ actLoading ? 'Buscando...' : 'Continuar' }}</span></button>
            <button
              v-if="actPaso === 2 && !actEnviado"
              type="button" class="submit-button" :disabled="actLoading"
              @click="actEnviar"
            ><span>{{ actLoading ? 'Enviando...' : 'Enviarme el código' }}</span></button>
            <button
              v-if="actPaso === 2 && actEnviado"
              type="button" class="submit-button" :disabled="actLoading"
              @click="actVerificar"
            ><span>{{ actLoading ? 'Verificando...' : 'Verificar código' }}</span></button>
            <button
              v-if="actPaso === 3"
              type="button" class="submit-button" :disabled="actLoading"
              @click="actConfirmar"
            ><span>{{ actLoading ? 'Creando...' : 'Crear contraseña e ingresar' }}</span></button>
            <button
              v-if="actPaso === 2 && actEnviado"
              type="button" class="link-button" :disabled="actLoading"
              @click="actReenviar"
            >Reenviar código</button>
            <button type="button" class="link-button" @click="cerrarActivacion()">Volver al ingreso</button>
          </div>
        </div>
        <p class="form-footer">Ferretería Avenida <span>·</span> Portal de ventas</p>
      </div>
    </section>
  </main>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import api from '../services/api'

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const showPassword = ref(false)
const authStore = useAuthStore()

// --- Activación con código de cliente + OTP ---
const showActivation = ref(false)
const actPaso = ref(1)
const actCodigo = ref('')
const actNombre = ref('')
const actEmailMask = ref('')
const actWhatsappMask = ref('')
const actEmail = ref('')
const actWhatsapp = ref('')
const actEnviado = ref(false)
const actCanales = ref({})
const actOtp = ref('')
const actPassword1 = ref('')
const actPassword2 = ref('')
const actError = ref('')
const actMsg = ref('')
const actLoading = ref(false)

const actApiError = (err, fallback) => {
  actError.value = err.response?.data?.error || fallback
}

const abrirActivacion = (codigo = '') => {
  showActivation.value = true
  actPaso.value = 1
  actError.value = ''
  actMsg.value = ''
  actEnviado.value = false
  actCanales.value = {}
  actOtp.value = ''
  actPassword1.value = ''
  actPassword2.value = ''
  if (codigo) actCodigo.value = codigo
}

const cerrarActivacion = () => {
  showActivation.value = false
  actError.value = ''
  actMsg.value = ''
}

const actIniciar = async () => {
  actError.value = ''
  actMsg.value = ''
  if (!actCodigo.value.trim()) {
    actError.value = 'Ingresá tu código de cliente.'
    return
  }
  actLoading.value = true
  try {
    const { data } = await api.post('/api/activacion/iniciar/', { codigo_cliente: actCodigo.value.trim() })
    actNombre.value = data.nombre
    actEmailMask.value = data.email_enmascarado
    actWhatsappMask.value = data.whatsapp_enmascarado
    actPaso.value = 2
  } catch (err) {
    if (err.response?.status === 409 && err.response?.data?.code === 'ya_activa') {
      actError.value = 'Esta cuenta ya tiene contraseña. Ingresá con tu usuario o código y tu clave.'
    } else {
      actApiError(err, 'No pudimos validar el código. Intentá más tarde.')
    }
  } finally {
    actLoading.value = false
  }
}

const actEnviar = async () => {
  actError.value = ''
  actMsg.value = ''
  actLoading.value = true
  try {
    const { data } = await api.post('/api/activacion/enviar/', {
      codigo_cliente: actCodigo.value.trim(),
      email: actEmail.value.trim(),
      whatsapp: actWhatsapp.value.trim(),
    })
    actEnviado.value = true
    actCanales.value = data.canales || {}
    actMsg.value = data.canales?.whatsapp === 'omitido'
      ? 'Te enviamos el código por email. Revisá tu casilla (y spam).'
      : 'Te enviamos el código por email y WhatsApp. Revisá ambos.'
  } catch (err) {
    if (err.response?.status === 429) {
      actError.value = err.response.data?.error || 'Esperá antes de pedir otro código.'
    } else {
      actApiError(err, 'No pudimos enviar el código. Intentá más tarde.')
    }
  } finally {
    actLoading.value = false
  }
}

const actReenviar = async () => {
  actError.value = ''
  actMsg.value = ''
  actLoading.value = true
  try {
    const { data } = await api.post('/api/activacion/reenviar/', {
      codigo_cliente: actCodigo.value.trim(),
    })
    actCanales.value = data.canales || {}
    actMsg.value = 'Te enviamos un código nuevo.'
  } catch (err) {
    actApiError(err, 'No pudimos reenviar el código. Intentá más tarde.')
  } finally {
    actLoading.value = false
  }
}

const actVerificar = async () => {
  actError.value = ''
  actMsg.value = ''
  if (!actOtp.value.trim()) {
    actError.value = 'Ingresá el código de 6 dígitos.'
    return
  }
  actLoading.value = true
  try {
    await api.post('/api/activacion/verificar/', {
      codigo_cliente: actCodigo.value.trim(),
      otp: actOtp.value.trim(),
    })
    actPaso.value = 3
  } catch (err) {
    actApiError(err, 'No pudimos verificar el código. Intentá más tarde.')
  } finally {
    actLoading.value = false
  }
}

const actConfirmar = async () => {
  actError.value = ''
  actMsg.value = ''
  actLoading.value = true
  try {
    const { data } = await api.post('/api/activacion/confirmar/', {
      codigo_cliente: actCodigo.value.trim(),
      otp: actOtp.value.trim(),
      password1: actPassword1.value,
      password2: actPassword2.value,
    })
    await authStore.applySession(data)
  } catch (err) {
    actApiError(err, 'No pudimos crear la contraseña. Intentá más tarde.')
    actLoading.value = false
  }
}

const handleSubmit = async () => {
  error.value = ''
  loading.value = true
  try {
    await authStore.login(username.value, password.value)
  } catch (err) {
    if (err.response?.status === 401) {
      error.value = 'Usuario o contraseña incorrectos.'
    } else if (err.response?.status === 409 && err.response?.data?.code === 'activacion_pendiente') {
      error.value = 'Esta cuenta aún no tiene contraseña. Activala con tu código de cliente.'
      abrirActivacion(username.value)
    } else {
      error.value = 'No se pudo conectar con el servidor. Intenta más tarde.'
    }
  } finally {
    loading.value = false
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
.success-message { margin-top: 12px; padding: 13px 15px; border: 1px solid #bfe3c9; border-radius: 8px; background: #eef9f0; color: #166534; font-size: 14px; line-height: 1.4; }
.activation-toggle { margin-top: 20px; text-align: center; }
.link-button { border: 0; background: none; padding: 4px; color: #b90018; font: inherit; font-size: 14px; font-weight: 650; cursor: pointer; }
.link-button:hover:not(:disabled) { text-decoration: underline; }
.link-button:disabled { opacity: .6; cursor: wait; }
.link-button:focus-visible { outline: 3px solid #ec8390; outline-offset: 3px; }
.activation-panel { margin-top: 16px; padding: 18px; border: 1px solid #dce0e5; border-radius: 8px; background: #fff; }
.activation-panel h3 { margin: 6px 0 4px; font-size: 19px; letter-spacing: -.02em; }
.activation-steps { margin: 0; color: #b90018; font-size: 11px; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; }
.activation-help { margin: 0 0 14px; color: #707988; font-size: 14px; line-height: 1.5; }
.activation-panel .field input { height: 52px; }
.activation-panel .submit-button { margin-top: 14px; }
.activation-actions { display: flex; flex-direction: column; gap: 8px; margin-top: 6px; }
.activation-actions .link-button { align-self: center; }
.activation-panel .success-message { margin-top: 12px; }
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
}
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: .01ms !important; animation-iteration-count: 1 !important; transition-duration: .01ms !important; } }
</style>
