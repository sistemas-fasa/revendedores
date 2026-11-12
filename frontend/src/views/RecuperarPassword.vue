<template>
  <main class="login-page">
    <section class="brand-panel" aria-label="Ferretería Avenida">
      <div class="brand-top"><img src="/logo.png" alt="Ferretería Avenida S.A." class="brand-logo" /></div>
      <div class="brand-content">
        <span class="eyebrow"><span></span> PORTAL DE CLIENTES</span>
        <h1>Todo lo que buscás,<br /><em>en un solo lugar.</em></h1>
        <p>Encontrá productos y gestioná tus pedidos de forma simple.</p>
      </div>
      <div class="brand-bottom"><span>FERRETERÍA AVENIDA</span><span>Juntos hacemos más.</span></div>
      <div class="brand-mark" aria-hidden="true">A</div>
    </section>

    <section class="form-panel" aria-labelledby="reset-title">
      <div class="form-wrap">
        <div class="mobile-brand"><img src="/logo.png" alt="Ferretería Avenida S.A." /></div>
        <div class="form-heading">
          <span class="form-eyebrow">PORTAL DE CLIENTES</span>
          <h2 id="reset-title">Crear nueva contraseña.</h2>
          <p>Elegí una clave nueva para tu cuenta.</p>
        </div>
        <form @submit.prevent="handleConfirm">
          <div class="field">
            <label for="new-password">Nueva contraseña</label>
            <input id="new-password" v-model="password1" type="password" autocomplete="new-password" required minlength="8" placeholder="Mínimo 8 caracteres" />
          </div>
          <div class="field">
            <label for="new-password2">Repetí la contraseña</label>
            <input id="new-password2" v-model="password2" type="password" autocomplete="new-password" required placeholder="Repetí la contraseña" />
          </div>
          <div v-if="msg" class="success-message" role="status">
            {{ msg }}
            <router-link to="/login" class="inline-link">Ir a ingresar</router-link>
          </div>
          <div v-if="error" class="error-message" role="alert">
            {{ error }}
            <router-link v-if="linkExpired" to="/login" class="inline-link">Volver al login para pedir un link nuevo</router-link>
          </div>
          <button type="submit" class="submit-button" :disabled="loading">
            <span>{{ loading ? 'Guardando...' : 'Guardar nueva contraseña' }}</span>
            <svg v-if="!loading" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M5 12h14m-6-6l6 6-6 6" /></svg>
            <span v-else class="spinner" aria-hidden="true"></span>
          </button>
        </form>
        <p class="form-footer">Ferretería Avenida <span>·</span> Portal de clientes</p>
      </div>
    </section>
  </main>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import api from '../services/api'

const route = useRoute()
const password1 = ref('')
const password2 = ref('')
const error = ref('')
const msg = ref('')
const loading = ref(false)
const linkExpired = ref(false)

const handleConfirm = async () => {
  error.value = ''
  msg.value = ''
  linkExpired.value = false
  if (password1.value !== password2.value) {
    error.value = 'Las contraseñas no coinciden.'
    return
  }
  loading.value = true
  try {
    const { data } = await api.post('/api/password-reset/confirm/', {
      uid: route.params.uid,
      token: route.params.token,
      new_password: password1.value,
    })
    msg.value = data.message
  } catch (err) {
    error.value = err.response?.data?.error || 'No se pudo guardar. Intentá más tarde.'
    linkExpired.value = (err.response?.status || 0) === 400
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
.submit-button { display: flex; align-items: center; justify-content: center; gap: 12px; width: 100%; min-height: 56px; margin-top: 32px; border: 0; border-radius: 8px; background: #c5001a; color: white; font: inherit; font-weight: 700; font-size: 15px; cursor: pointer; box-shadow: 0 8px 20px rgba(174,0,23,.16); transition: background .2s, transform .2s; }
.submit-button:hover:not(:disabled) { background: #a90016; transform: translateY(-1px); }
.submit-button:disabled { opacity: .7; cursor: wait; }
.submit-button:focus-visible { outline: 3px solid #ec8390; outline-offset: 3px; }
.submit-button svg { width: 20px; height: 20px; }
.spinner { width: 17px; height: 17px; border: 2px solid rgba(255,255,255,.4); border-top-color: #fff; border-radius: 50%; animation: spin .8s linear infinite; }
.error-message { margin-top: 4px; margin-bottom: 16px; padding: 13px 15px; border: 1px solid #f1c3c9; border-radius: 8px; background: #fff1f2; color: #a90016; font-size: 14px; line-height: 1.4; }
.success-message { margin-top: 4px; margin-bottom: 16px; padding: 13px 15px; border: 1px solid #bfe3c9; border-radius: 8px; background: #eef9f0; color: #166534; font-size: 14px; line-height: 1.4; }
.inline-link { display: block; margin-top: 8px; font-weight: 700; color: inherit; }
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
