import { auth } from './auth'  
import { banState } from './ban'  

const BASE = 'http://127.0.0.1:8000'

export async function api(path, options = {}) {  
  const headers = { ...(options.headers || {}) }  
  const isForm = options.body instanceof FormData  
  if (!isForm) headers['Content-Type'] = 'application/json'  
  if (auth.token) headers['Authorization'] = 'Token ' + auth.token  
  const res = await fetch(BASE + path, { ...options, headers })  
  if (!res.ok) {  
    let detail  
    try { detail = await res.json() } catch { detail = { detail: 'Ошибка' } }  
    if (detail.code === 'account_banned') {  
      auth.logout()  
      banState.value = { reason: detail.ban_reason || '' }  
    }
    throw detail  
  }
  if (res.status === 204) return null  
  return res.json()  
}
