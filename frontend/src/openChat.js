import { ref } from 'vue'  

export const pendingChatUser = ref(null)  

export function requestOpenChat(user) {  
  pendingChatUser.value = user  
}
