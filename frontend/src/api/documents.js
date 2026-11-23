import api from './client'

export const listDocuments = () => api.get('/documents/').then((r) => r.data)
export const getDocument = (id) => api.get(`/documents/${id}/`).then((r) => r.data)
export const deleteDocument = (id) => api.delete(`/documents/${id}/`)
export const reprocessDocument = (id) => api.post(`/documents/${id}/reprocess/`).then((r) => r.data)
export const summarizeDocument = (id) => api.post(`/documents/${id}/summarize/`).then((r) => r.data)

export const uploadDocument = (file, onProgress) => {
  const form = new FormData()
  form.append('file', file)
  return api
    .post('/documents/', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => e.total && onProgress?.(Math.round((e.loaded * 100) / e.total)),
    })
    .then((r) => r.data)
}
