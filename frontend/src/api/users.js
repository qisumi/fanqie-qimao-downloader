import api from './index'

export function listUsers() {
  return api.get('/users')
}

export function createUser(username) {
  return api.post('/users', { username })
}

export function renameUser(userId, username) {
  return api.patch(`/users/${userId}`, { username })
}

export function deleteUser(userId) {
  return api.delete(`/users/${userId}`)
}

export function listUserBooks(userId, params = {}) {
  return api.get(`/users/${userId}/books`, { params })
}

export function addBookToUser(userId, bookId) {
  return api.post(`/users/${userId}/books/${bookId}`)
}

export function removeBookFromUser(userId, bookId) {
  return api.delete(`/users/${userId}/books/${bookId}`)
}
