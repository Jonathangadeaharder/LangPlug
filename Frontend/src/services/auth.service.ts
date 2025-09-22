import { apiClient } from '../client/api-client'
import { tokenStorage } from '../utils/token-storage'

export type RegisterData = { username: string; email: string; password: string }
export type LoginData = { email: string; password: string }

const isValidEmail = (email: string) => /.+@.+\..+/.test(email)

export class AuthService {
  private userCache: any | null = null

  async register(data: RegisterData) {
    if (!isValidEmail(data.email)) throw new Error('Invalid email format')
    if ((data.password ?? '').length < 8) {
      throw new Error('Password must be at least 8 characters')
    }
    try {
      const res = await apiClient.post('/api/auth/register', data)
      return res.data
    } catch (err: any) {
      const detail = err?.response?.data?.detail || err?.message || 'Registration failed'
      throw new Error(detail)
    }
  }

  async login(data: LoginData) {
    try {
      const form = new URLSearchParams()
      form.set('username', data.email)
      form.set('password', data.password)
      const res = await apiClient.post('/api/auth/login', form, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })
      const token = res.data?.access_token
      if (token) tokenStorage.setToken(token)
      return res.data
    } catch (err: any) {
      tokenStorage.clear()
      const detail = err?.response?.data?.detail || err?.message || 'Login failed'
      throw new Error(detail)
    }
  }

  async logout() {
    const token = tokenStorage.getToken()
    try {
      if (token) {
        await apiClient.post('/api/auth/logout', {}, {
          headers: { Authorization: `Bearer ${token}` },
        })
      }
    } catch (_) {
      // ignore
    } finally {
      tokenStorage.clear()
    }
  }

  async getCurrentUser() {
    const token = tokenStorage.getToken()
    if (!token) return null
    if (this.userCache) return this.userCache
    try {
      const res = await apiClient.get('/api/auth/me', {
        headers: { Authorization: `Bearer ${token}` },
      })
      this.userCache = res.data
      return res.data
    } catch (err: any) {
      if (err?.response?.status === 401) {
        // Try refresh flow
        try {
          const refreshed = await this.refreshToken()
          const newToken = refreshed?.access_token
          if (!newToken) throw new Error('No refreshed token')
          const res2 = await apiClient.get('/api/auth/me', {
            headers: { Authorization: `Bearer ${newToken}` },
          })
          this.userCache = res2.data
          return res2.data
        } catch (_refreshErr) {
          tokenStorage.clear()
          return null
        }
      }
      throw err
    }
  }

  async refreshToken() {
    const refresh = tokenStorage.getRefreshToken()
    if (!refresh) throw new Error('No refresh token available')
    try {
      const res = await apiClient.post('/api/auth/refresh', { refresh_token: refresh })
      const token = res.data?.access_token
      if (token) tokenStorage.setToken(token)
      return res.data
    } catch (err: any) {
      const detail = err?.response?.data?.detail || err?.message || 'Refresh failed'
      tokenStorage.clear()
      throw new Error(detail)
    }
  }

  isAuthenticated() {
    const token = tokenStorage.getToken()
    if (!token) return false
    return !tokenStorage.isTokenExpired(token)
  }

  async changePassword(current_password: string, new_password: string) {
    if ((new_password ?? '').length < 8) {
      throw new Error('Password must be at least 8 characters')
    }
    const token = tokenStorage.getToken()
    if (!token) throw new Error('Not authenticated')
    try {
      const res = await apiClient.post(
        '/api/auth/change-password',
        { current_password, new_password },
        { headers: { Authorization: `Bearer ${token}` } }
      )
      return res.data
    } catch (err: any) {
      const detail = err?.response?.data?.detail || err?.message || 'Change password failed'
      throw new Error(detail)
    }
  }

  async requestPasswordReset(email: string) {
    try {
      const res = await apiClient.post('/api/auth/forgot-password', { email })
      return res.data
    } catch (err: any) {
      const detail = err?.response?.data?.detail || err?.message || 'Request failed'
      throw new Error(detail)
    }
  }

  async confirmPasswordReset(token: string, new_password: string) {
    try {
      const res = await apiClient.post('/api/auth/reset-password', { token, new_password })
      return res.data
    } catch (err: any) {
      const detail = err?.response?.data?.detail || err?.message || 'Reset password failed'
      throw new Error(detail)
    }
  }
}
