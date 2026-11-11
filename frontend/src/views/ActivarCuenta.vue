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

    <section class="form-panel" aria-labelledby="activar-title">
      <div class="form-wrap">
        <div class="mobile-brand"><img src="/logo.png" alt="Ferretería Avenida S.A." /></div>
        <div class="form-heading">
          <span class="form-eyebrow">PORTAL DE VENTAS</span>
          <h2 id="activar-title">Activá tu cuenta.</h2>
          <p>Ingresá el código de cliente de tu factura y te enviamos un código de verificación.</p>
        </div>

        <ol class="steps" aria-label="Progreso">
          <li :class="{ active: paso === 1, done: paso > 1 }"><span>1</span> Código</li>
          <li :class="{ active: paso === 2, done: paso > 2 }"><span>2</span> Verificación</li>
          <li :class="{ active: paso === 3 }"><span>3</span> Contraseña</li>
        </ol>

        <div v-if="paso === 1">
          <div class="field">
            <label for="act-codigo">Código de cliente</label>
            <input id="act-codigo" v-model="codigo" type="text" inputmode="numeric" placeholder="Ej: 40" />
          </div>
        </div>

        <div v-if="paso === 2">
          <p class="activation-help">Hola, <strong>{{ nombre }}</strong>. Te enviamos el mismo código por email<span v-if="emailMask"> ({{ emailMask }})</span> y WhatsApp<span v-if="whatsappMask"> ({{ whatsappMask }})</span>.</p>
          <div v-if="!enviado">
            <div class="field">
              <label for="act-email">Email</label>
              <input id="act-email" v-model="email" type="email" autocomplete="email" placeholder="tu@email.com" />
            </div>
            <div class="field">
              <label for="act-wpp">WhatsApp (móvil argentino)</label>
              <input id="act-wpp" v-model="whatsapp" type="tel" autocomplete="tel" placeholder="11-1234-5678" />
            </div>
          </div>
          <div v-else>
            <div class="field">
              <label for="act-otp">Código de verificación</label>
              <input id="act-otp" v-model="otp" type="text" inputmode="numeric" maxlength="6" placeholder="6 dígitos" />
            </div>
            <p v-if="canales.whatsapp === 'omitido'" class="activation-help">WhatsApp no disponible: revisá tu email.</p>
          </div>
        </div>

        <div v-if="paso === 3">
          <p class="activation-help">Código correcto. Elegí tu usuario y creá tu contraseña para entrar al portal.</p>
          <div class="field">
            <label for="act-user">Nombre de usuario</label>
            <input id="act-user" v-model="username" type="text" autocomplete="username" :placeholder="codigo" />
          </div>
          <div class="field">
            <label for="act-p1">Nueva contraseña</label>
            <input id="act-p1" v-model="password1" type="password" autocomplete="new-password" placeholder="Mínimo 8 caracteres" />
          </div>
          <div class="field">
            <label for="act-p2">Repetí la contraseña</label>
            <input id="act-p2" v-model="password2" type="password" autocomplete="new-password" placeholder="Igual que arriba" />
          </div>
        </div>

        <div v-if="error" class="error-message" role="alert">{{ error }}</div>
        <div v-if="msg" class="success-message" role="status">{{ msg }}</div>

        <div class="activation-actions">
          <button v-if="paso === 1" type="button" class="submit-button" :disabled="loading" @click="iniciar">
            <span>{{ loading ? 'Buscando...' : 'Continuar' }}</span>
          </button>
          <button v-if="paso === 2 && !enviado" type="button" class="submit-button" :disabled="loading" @click="enviar">
            <span>{{ loading ? 'Enviando...' : 'Enviarme el código' }}</span>
          </button>
          <button v-if="paso === 2 && enviado" type="button" class="submit-button" :disabled="loading" @click="verificar">
            <span>{{ loading ? 'Verificando...' : 'Verificar código' }}</span>
          </button>
          <button v-if="paso === 3" type="button" class="submit-button" :disabled="loading" @click="confirmar">
            <span>{{ loading ? 'Creando...' : 'Crear contraseña e ingresar' }}</span>
          </button>
          <button v-if="paso === 2 && enviado" type="button" class="link-button" :disabled="loading" @click="reenviar">
            Reenviar código
          </button>
          <router-link to="/login" class="link-button back-link">Volver al ingreso</router-link>
        </div>
        <p class="form-footer">Ferretería Avenida <span>·</span> Portal de ventas</p>
      </div>
    </section>
  </main>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import api from '../services/api'

const route = useRoute()
const authStore = useAuthStore()

const paso = ref(1)
const codigo = ref('')
const nombre = ref('')
const emailMask = ref('')
const whatsappMask = ref('')
const email = ref('')
const whatsapp = ref('')
const enviado = ref(false)
const canales = ref({})
const otp = ref('')
const username = ref('')
const password1 = ref('')
const password2 = ref('')
const error = ref('')
const msg = ref('')
const loading = ref(false)

const apiError = (err, fallback) => {
  error.value = err.response?.data?.error || fallback
}

onMounted(() => {
  if (route.query.codigo) {
    codigo.value = String(route.query.codigo)
  }
})

const iniciar = async () => {
  error.value = ''
  msg.value = ''
  if (!codigo.value.trim()) {
    error.value = 'Ingresá tu código de cliente.'
    return
  }
  loading.value = true
  try {
    const { data } = await api.post('/api/activacion/iniciar/', { codigo_cliente: codigo.value.trim() })
    nombre.value = data.nombre
    emailMask.value = data.email_enmascarado
    whatsappMask.value = data.whatsapp_enmascarado
    paso.value = 2
  } catch (err) {
    if (err.response?.status === 409 && err.response?.data?.code === 'ya_activa') {
      error.value = 'Esta cuenta ya tiene contraseña. Ingresá con tu usuario o código y tu clave.'
    } else {
      apiError(err, 'No pudimos validar el código. Intentá más tarde.')
    }
  } finally {
    loading.value = false
  }
}

const enviar = async () => {
  error.value = ''
  msg.value = ''
  loading.value = true
  try {
    const { data } = await api.post('/api/activacion/enviar/', {
      codigo_cliente: codigo.value.trim(),
      email: email.value.trim(),
      whatsapp: whatsapp.value.trim(),
    })
    enviado.value = true
    canales.value = data.canales || {}
    msg.value = data.canales?.whatsapp === 'omitido'
      ? 'Te enviamos el código por email. Revisá tu casilla (y spam).'
      : 'Te enviamos el código por email y WhatsApp. Revisá ambos.'
  } catch (err) {
    if (err.response?.status === 429) {
      error.value = err.response.data?.error || 'Esperá antes de pedir otro código.'
    } else {
      apiError(err, 'No pudimos enviar el código. Intentá más tarde.')
    }
  } finally {
    loading.value = false
  }
}

const reenviar = async () => {
  error.value = ''
  msg.value = ''
  loading.value = true
  try {
    const { data } = await api.post('/api/activacion/reenviar/', {
      codigo_cliente: codigo.value.trim(),
    })
    canales.value = data.canales || {}
    msg.value = 'Te enviamos un código nuevo.'
  } catch (err) {
    apiError(err, 'No pudimos reenviar el código. Intentá más tarde.')
  } finally {
    loading.value = false
  }
}

const verificar = async () => {
  error.value = ''
  msg.value = ''
  if (!otp.value.trim()) {
    error.value = 'Ingresá el código de 6 dígitos.'
    return
  }
  loading.value = true
  try {
    await api.post('/api/activacion/verificar/', {
      codigo_cliente: codigo.value.trim(),
      otp: otp.value.trim(),
    })
    paso.value = 3
  } catch (err) {
    apiError(err, 'No pudimos verificar el código. Intentá más tarde.')
  } finally {
    loading.value = false
  }
}

const confirmar = async () => {
  error.value = ''
  msg.value = ''
  loading.value = true
  try {
    const { data } = await api.post('/api/activacion/confirmar/', {
      codigo_cliente: codigo.value.trim(),
      otp: otp.value.trim(),
      username: username.value.trim(),
      password1: password1.value,
      password2: password2.value,
    })
    await authStore.applySession(data)
  } catch (err) {
    apiError(err, 'No pudimos crear la contraseña. Intentá más tarde.')
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
.steps { display: flex; gap: 8px; margin: 26px 0 6px; padding: 0; list-style: none; }
.steps li { flex: 1; display: flex; align-items: center; gap: 8px; font-size: 12px; font-weight: 650; color: #a2a9b3; border-top: 3px solid #dce0e5; padding-top: 8px; }
.steps li span { display: grid; place-items: center; width: 22px; height: 22px; border-radius: 50%; background: #dce0e5; color: #fff; font-size: 12px; }
.steps li.active { color: #313b49; border-top-color: #c5001a; }
.steps li.active span { background: #c5001a; }
.steps li.done { color: #166534; border-top-color: #166534; }
.steps li.done span { background: #166534; }
.field { margin-bottom: 23px; margin-top: 18px; }
.field label { display: block; margin-bottom: 9px; color: #313b49; font-size: 13px; font-weight: 650; }
.field input { width: 100%; height: 56px; box-sizing: border-box; border: 1px solid #dce0e5; border-radius: 8px; background: #fff; color: #202735; font: inherit; font-size: 15px; padding: 0 16px; transition: border-color .2s, box-shadow .2s; }
.field input::placeholder { color: #a2a9b3; }
.field input:focus { outline: none; border-color: #be001a; box-shadow: 0 0 0 3px rgba(190,0,26,.12); }
.activation-help { margin: 14px 0 4px; color: #707988; font-size: 14px; line-height: 1.5; }
.submit-button { display: flex; align-items: center; justify-content: center; gap: 12px; width: 100%; min-height: 56px; margin-top: 20px; border: 0; border-radius: 8px; background: #c5001a; color: white; font: inherit; font-weight: 700; font-size: 15px; cursor: pointer; box-shadow: 0 8px 20px rgba(174,0,23,.16); transition: background .2s, transform .2s; }
.submit-button:hover:not(:disabled) { background: #a90016; transform: translateY(-1px); }
.submit-button:disabled { opacity: .7; cursor: wait; }
.error-message { margin-top: 12px; padding: 13px 15px; border: 1px solid #f1c3c9; border-radius: 8px; background: #fff1f2; color: #a90016; font-size: 14px; line-height: 1.4; }
.success-message { margin-top: 12px; padding: 13px 15px; border: 1px solid #bfe3c9; border-radius: 8px; background: #eef9f0; color: #166534; font-size: 14px; line-height: 1.4; }
.activation-actions { display: flex; flex-direction: column; gap: 8px; }
.link-button { border: 0; background: none; padding: 4px; color: #b90018; font: inherit; font-size: 14px; font-weight: 650; cursor: pointer; }
.link-button:hover:not(:disabled) { text-decoration: underline; }
.link-button:disabled { opacity: .6; cursor: wait; }
.link-button:focus-visible, .submit-button:focus-visible { outline: 3px solid #ec8390; outline-offset: 3px; }
.back-link { align-self: center; text-decoration: none; }
.form-footer { margin: 55px 0 0; color: #929aa5; font-size: 12px; }
.form-footer span { padding: 0 5px; color: #c5001a; }
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
  .form-footer { margin-top: 40px; }
}
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: .01ms !important; animation-iteration-count: 1 !important; transition-duration: .01ms !important; } }
</style>
