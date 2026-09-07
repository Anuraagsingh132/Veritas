import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getStats = () => api.get('/system/stats').then(res => res.data);
export const getStatus = () => api.get('/system/status').then(res => res.data);
export const updateApiKey = (key) => api.post('/system/key', { groq_api_key: key }).then(res => res.data);
export const reseedData = () => api.post('/system/reseed').then(res => res.data);

export const getDocuments = () => api.get('/documents').then(res => res.data);
export const getDocumentDetail = (id) => api.get(`/documents/${id}`).then(res => res.data);
export const uploadDocument = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }).then(res => res.data);
};
export const deleteDocument = (id) => api.delete(`/documents/${id}`).then(res => res.data);

export const getFacts = (params = {}) => api.get('/facts', { params }).then(res => res.data);
export const getFactDetail = (id) => api.get(`/facts/${id}`).then(res => res.data);

export const getReconciliation = (params = {}) => api.get('/reconciliation', { params }).then(res => res.data);
export const runReconciliation = () => api.post('/reconciliation/reconcile-all').then(res => res.data);

export const getShowcaseCases = () => api.get('/showcase').then(res => res.data);

export default api;
