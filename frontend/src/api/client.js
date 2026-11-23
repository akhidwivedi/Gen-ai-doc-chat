import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

const ACCESS_KEY = 'docchat_access'
const REFRESH_KEY = 'docchat_refresh'

export const tokenStore = {
  get access() { return localStorage.getItem(ACCESS_KEY) },
  get refresh() { return localStorage.getItem(REFRESH_KEY) },
  set({ access, refresh }) {
    if (access) localStorage.setItem(ACCESS_KEY, access)
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh)
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
  },
}

const api = axios.create({ baseURL: API_URL })

api.interceptors.request.use((config) => {
  const token = tokenStore.access
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// On 401, try once to refresh the access token, then replay the request.
let refreshPromise = null

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    const isAuthCall = original?.url?.includes('/auth/login') || original?.url?.includes('/auth/refresh')
    if (error.response?.status === 401 && !original._retry && !isAuthCall && tokenStore.refresh) {
      original._retry = true
      try {
        refreshPromise ??= axios
          .post(`${API_URL}/auth/refresh/`, { refresh: tokenStore.refresh })
          .finally(() => { refreshPromise = null })
        const { data } = await refreshPromise
        tokenStore.set({ access: data.access, refresh: data.refresh })
        original.headers.Authorization = `Bearer ${data.access}`
        return api(original)
      } catch {
        tokenStore.clear()
        window.dispatchEvent(new Event('docchat:logout'))
      }
    }
    return Promise.reject(error)
  },
)

/** Turn any axios/DRF error into a readable string. */
export function errorMessage(error, fallback = 'Something went wrong.') {
  const data = error?.response?.data
  if (!data) return error?.message === 'Network Error'
    ? 'Cannot reach the server. Is the backend running?'
    : fallback
  if (typeof data === 'string') return fallback
  if (data.detail) return data.detail
  const first = Object.entries(data)[0]
  if (first) {
    const [field, msgs] = first
    const text = Array.isArray(msgs) ? msgs.join(' ') : String(msgs)
    return field === 'non_field_errors' ? text : `${field}: ${text}`
  }
  return fallback
}

export default api
