// src/api/user.js
import api from '@/services/api'  // 👈 Tu cliente con interceptores y refresh

/**
 * Actualiza la información del usuario (nombre, email, contraseña opcional)
 * @param {Object} userData - { first_name, last_name, email, password }
 * @returns {Promise<Object>} - Datos actualizados del usuario
 */
export const updateUserInfo = async (userData) => {
  try {
    const response = await api.put('/api/profile/', userData)
    return response.data
  } catch (error) {
    // Manejo de errores
    if (error.response?.data?.error) {
      throw new Error(error.response.data.error)
    } else if (error.response?.status === 401) {
      throw new Error('No autorizado. Por favor inicia sesión nuevamente.')
    } else {
      throw new Error('Error de conexión con el servidor.')
    }
  }
}

/**
 * Opcional: Obtener datos del usuario (si no los tienes en el store)
 */
export const fetchUserProfile = async () => {
  try {
    const response = await api.get('/api/profile/') // Si creas este endpoint
    return response.data
  } catch (error) {
    throw new Error('Error al cargar el perfil')
  }
}