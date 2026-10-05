import { reactive } from 'vue'  

export const toasts = reactive([])  
let _id = 0  

export function toast(message, type = 'info', duration = 3500) {  
  const id = ++_id  
  toasts.push({ id, message, type })  
  setTimeout(() => {  
    const i = toasts.findIndex(t => t.id === id)  
    if (i !== -1) toasts.splice(i, 1)  
  }, duration)  
}

export const toastSuccess = (msg) => toast(msg, 'success')  
export const toastError = (msg) => toast(msg, 'error')  
export const toastInfo = (msg) => toast(msg, 'info')  
