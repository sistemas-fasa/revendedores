<template>
  <button 
    v-if="isInstallable && !isInstalled"
    @click="installApp"
    class="pwa-install-btn"
    :class="{ 'pulse': showPulse }"
    :title="buttonTitle"
  >
    <span class="btn-icon">⬇️</span>
    <span class="btn-text">Instalar App</span>
  </button>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'

export default {
  name: 'PWAInstallButton',
  setup() {
    const isInstallable = ref(false)
    const isInstalled = ref(false)
    const showPulse = ref(false)
    const buttonTitle = ref('Instalar aplicación en tu dispositivo')
    let deferredPrompt = null

    // Verificar si la app ya está instalada
    const checkIfInstalled = () => {
      if (window.matchMedia('(display-mode: standalone)').matches) {
        isInstalled.value = true
        isInstallable.value = false
      }
    }

    onMounted(() => {
      checkIfInstalled()

      // Evento cuando el navegador puede mostrar el prompt de instalación
      window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault()
        deferredPrompt = e
        isInstallable.value = true
        
        // Efecto de pulso para llamar la atención
        showPulse.value = true
        setTimeout(() => {
          showPulse.value = false
        }, 3000)
      })

      // Evento cuando la app es instalada
      window.addEventListener('appinstalled', () => {
        isInstalled.value = true
        isInstallable.value = false
        console.log('App instalada correctamente')
      })

      // Verificar periodicamente el estado de instalación
      const checkInterval = setInterval(checkIfInstalled, 5000)
      
      onUnmounted(() => {
        clearInterval(checkInterval)
      })
    })

    const installApp = async () => {
      if (!deferredPrompt) {
        alert('Tu navegador no soporta la instalación de PWAs')
        return
      }

      try {
        // Mostrar el prompt de instalación
        deferredPrompt.prompt()
        
        // Esperar a que el usuario responda
        const { outcome } = await deferredPrompt.userChoice
        
        if (outcome === 'accepted') {
          console.log('Usuario aceptó la instalación')
          buttonTitle.value = '¡App instalada!'
        } else {
          console.log('Usuario rechazó la instalación')
          buttonTitle.value = 'Instalación cancelada'
        }
        
        // Limpiar el prompt
        deferredPrompt = null
        isInstallable.value = false
        
      } catch (error) {
        console.error('Error durante la instalación:', error)
        alert('Error al instalar la aplicación: ' + error.message)
      }
    }

    return {
      isInstallable,
      isInstalled,
      showPulse,
      buttonTitle,
      installApp
    }
  }
}
</script>

<style scoped>
.pwa-install-btn {
  position: fixed;
  bottom: 20px;
  right: 20px;
  background: linear-gradient(135deg, #42b883, #338b6d);
  color: white;
  border: none;
  border-radius: 50px;
  padding: 12px 20px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 4px 15px rgba(66, 184, 131, 0.3);
  display: flex;
  align-items: center;
  gap: 8px;
  z-index: 1000;
  transition: all 0.3s ease;
  animation: slideIn 0.5s ease-out;
}

.pwa-install-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(66, 184, 131, 0.4);
  background: linear-gradient(135deg, #338b6d, #42b883);
}

.pwa-install-btn:active {
  transform: translateY(0);
}

.pulse {
  animation: pulse 2s infinite;
}

.btn-icon {
  font-size: 18px;
}

.btn-text {
  white-space: nowrap;
}

/* Animaciones */
@keyframes slideIn {
  from {
    transform: translateX(100px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(66, 184, 131, 0.7);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(66, 184, 131, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(66, 184, 131, 0);
  }
}

/* Responsive */
@media (max-width: 768px) {
  .pwa-install-btn {
    display: none; /* Ocultar en móvil ya que está en el navbar */
  }
}
</style>