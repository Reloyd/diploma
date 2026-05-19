import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Auto-logout on 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// --- Auth ---
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  me: () => api.get('/auth/me'),
}

// --- Tracks / Catalog ---
export const tracksAPI = {
  list: (params) => api.get('/tracks', { params }),
  get: (id) => api.get(`/tracks/${id}`),
  listArtists: (params) => api.get('/tracks/artists/list', { params }),
  getArtist: (id) => api.get(`/tracks/artists/${id}`),
  getAlbum: (id) => api.get(`/tracks/albums/${id}`),
  listGenres: () => api.get('/tracks/genres/list'),
}

// --- Library ---
export const libraryAPI = {
  get: (params) => api.get('/library', { params }),
  add: (trackId) => api.post(`/library/${trackId}`),
  remove: (trackId) => api.delete(`/library/${trackId}`),
}

// --- Playlists ---
export const playlistsAPI = {
  list: () => api.get('/playlists'),
  get: (id) => api.get(`/playlists/${id}`),
  create: (data) => api.post('/playlists', data),
  update: (id, data) => api.patch(`/playlists/${id}`, data),
  delete: (id) => api.delete(`/playlists/${id}`),
  reorder: (plId, trackIds) => api.patch(`/playlists/${plId}/reorder`, trackIds),
  addTrack: (plId, trackId) => api.post(`/playlists/${plId}/tracks/${trackId}`),
  removeTrack: (plId, trackId) => api.delete(`/playlists/${plId}/tracks/${trackId}`),
  previewAI: (data) => api.post('/playlists/ai/preview', data),
  createAI: (data) => api.post('/playlists/ai/create', data),
}

// --- Events ---
export const eventsAPI = {
  record: (data) => api.post('/events', data),
}

// --- Stats ---
export const statsAPI = {
  get: () => api.get('/stats', {
    params: { tz: Intl.DateTimeFormat().resolvedOptions().timeZone }
  }),
}

// --- Recommendations ---
export const recommendationsAPI = {
  get: (params) => api.get('/recommendations', { params }),
  refresh: (context) => api.post('/recommendations/refresh', null, { params: { context } }),
}

export default api
