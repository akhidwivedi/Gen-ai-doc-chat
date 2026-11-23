import api from './client'

export const getHistory = (docId) => api.get(`/documents/${docId}/chat/`).then((r) => r.data)
export const askQuestion = (docId, question) =>
  api.post(`/documents/${docId}/chat/`, { question }).then((r) => r.data)
export const clearHistory = (docId) => api.delete(`/documents/${docId}/chat/`)
