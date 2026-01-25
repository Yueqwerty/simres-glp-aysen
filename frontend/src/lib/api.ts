/**
 * Configuración de cliente API.
 */

import axios from "axios"

// Usar proxy de Vite en desarrollo (configurado en vite.config.ts)
// En producción, usar variable de entorno
const API_BASE_URL = import.meta.env.VITE_API_URL || "/api"

export const api = axios.create({
  baseURL: `${API_BASE_URL}/v1`,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 120000, // 2 minutos para operaciones grandes como cargar 100k réplicas
})

// Interceptors para manejo de errores global
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("API Error:", error)
    return Promise.reject(error)
  }
)
