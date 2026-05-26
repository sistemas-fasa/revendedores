<template>
  <div v-if="showInstallPrompt" class="pwa-install-prompt">
    <div class="pwa-install-content">
      <h3>Instalar aplicación</h3>
      <p>Instala esta aplicación en tu dispositivo para una mejor experiencia</p>
      <div class="pwa-install-buttons">
        <button @click="installApp" class="install-button">Instalar</button>
        <button @click="dismissPrompt" class="dismiss-button">Ahora no</button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'

export default {
  name: 'PWAInstaller',
  setup() {
    const showInstallPrompt = ref(false)
    let deferredPrompt = null

    onMounted(() => {
      window.addEventListener('beforeinstallprompt', (e) => {
        // Previene que el mini-infobar aparezca en mobile
        e.preventDefault()
        // Guarda el evento para que pueda ser activado después
        deferredPrompt = e
        // Actualiza la UI para notificar al usuario que puede instalar la PWA
        showInstallPrompt.value = true
      })

      window.addEventListener('appinstalled', () => {
        // Oculta la promoción de instalación
        showInstallPrompt.value = false
        // Limpia el deferredPrompt para que sea recolectado por garbage collection
        deferredPrompt = null
        console.log('PWA fue instalada')
      })
    })

    const installApp = async () => {
      if (deferredPrompt) {
        // Muestra el prompt de instalación
        deferredPrompt.prompt()
        // Espera a que el usuario responda al prompt
        const { outcome } = await deferredPrompt.userChoice
        if (outcome === 'accepted') {
          console.log('Usuario aceptó la instalación')
        } else {
          console.log('Usuario rechazó la instalación')
        }
        // Ya no necesitamos el prompt, lo limpiamos
        deferredPrompt = null
        // Ocultamos el prompt de instalación
        showInstallPrompt.value = false
      }
    }

    const dismissPrompt = () => {
      showInstallPrompt.value = false
    }

    return {
      showInstallPrompt,
      installApp,
      dismissPrompt
    }
  }
}
</script>

<style scoped>
.pwa-install-prompt {
  position: fixed;
  bottom: 20px;
  right: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  padding: 16px;
  z-index: 1000;
  max-width: 320px;
}

.pwa-install-content h3 {
  margin: 0 0 8px 0;
  color: #2c3e50;
}

.pwa-install-content p {
  margin: 0 0 16px 0;
  color: #34495e;
  font-size: 14px;
}

.pwa-install-buttons {
  display: flex;
  gap: 8px;
}

.install-button {
  background-color: #42b883;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
}

.dismiss-button {
  background-color: #f1f1f1;
  color: #333;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}
</style>