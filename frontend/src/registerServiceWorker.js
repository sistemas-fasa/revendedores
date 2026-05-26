import { registerSW } from 'virtual:pwa-register'

// Solo registrar en producción o si está explícitamente habilitado en desarrollo
if (import.meta.env.PROD || import.meta.env.VITE_PWA_DEV === 'true') {
  const updateSW = registerSW({
    onNeedRefresh() {
      // Muestra una notificación más amigable
      const shouldUpdate = confirm('¡Hay una nueva versión disponible! ¿Quieres actualizar ahora?')
      if (shouldUpdate) {
        updateSW()
      }
    },
    onOfflineReady() {
      console.log('La aplicación está lista para funcionar sin conexión')
      // Puedes mostrar una notificación al usuario
      // alert('La aplicación está lista para usar sin conexión a internet')
    },
    onRegisteredSW(swScriptUrl, registration) {
      console.log('Service Worker registrado:', swScriptUrl)
    },
    onRegisterError(error) {
      console.error('Error registrando Service Worker:', error)
    }
  })
} else {
  console.log('PWA deshabilitada en modo desarrollo')
}