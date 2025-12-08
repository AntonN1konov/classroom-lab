import { create } from 'zustand'
import api from '../services/api'

// Простая реализация persist без middleware
const getStoredAuth = () => {
  try {
    const stored = localStorage.getItem('auth-storage')
    return stored ? JSON.parse(stored) : { user: null, token: null, isAuthenticated: false }
  } catch {
    return { user: null, token: null, isAuthenticated: false }
  }
}

const setStoredAuth = (state) => {
  try {
    localStorage.setItem('auth-storage', JSON.stringify({
      user: state.user,
      token: state.token,
      isAuthenticated: state.isAuthenticated,
    }))
  } catch {}
}

const initialState = getStoredAuth()

const useAuthStore = create(
    (set, get) => ({
      user: initialState.user,
      token: initialState.token,
      isAuthenticated: initialState.isAuthenticated,

      login: async (username, password) => {
        try {
          const response = await api.post('/auth/login', new URLSearchParams({
            username,
            password,
          }), {
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
            },
          })
          
          const { access_token } = response.data
          api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
          
          const userResponse = await api.get('/auth/me')
          
          const newState = {
            token: access_token,
            user: userResponse.data,
            isAuthenticated: true,
          }
          
          set(newState)
          setStoredAuth(newState)
          
          return { success: true }
        } catch (error) {
          return {
            success: false,
            error: error.response?.data?.detail || 'Ошибка входа',
          }
        }
      },

      register: async (userData) => {
        try {
          await api.post('/auth/register', userData)
          return { success: true }
        } catch (error) {
          return {
            success: false,
            error: error.response?.data?.detail || 'Ошибка регистрации',
          }
        }
      },

      logout: () => {
        delete api.defaults.headers.common['Authorization']
        const newState = {
          user: null,
          token: null,
          isAuthenticated: false,
        }
        set(newState)
        setStoredAuth(newState)
      },

      initAuth: () => {
        const stored = getStoredAuth()
        if (stored.token) {
          api.defaults.headers.common['Authorization'] = `Bearer ${stored.token}`
          api.get('/auth/me')
            .then((response) => {
              const newState = {
                user: response.data,
                token: stored.token,
                isAuthenticated: true,
              }
              set(newState)
              setStoredAuth(newState)
            })
            .catch(() => {
              get().logout()
            })
        }
      },
    })
)

export default useAuthStore

