import { reactive } from 'vue'  

export const confirmState = reactive({  
  visible: false,  
  message: '',  
  _resolve: null,  
})

export function showConfirm(message) {  
  return new Promise(resolve => {  
    confirmState.message = message  
    confirmState.visible = true  
    confirmState._resolve = resolve  
  })
}

export function confirmYes() {  
  confirmState._resolve(true)  
  confirmState.visible = false  
}

export function confirmNo() {  
  confirmState._resolve(false)  
  confirmState.visible = false  
}
