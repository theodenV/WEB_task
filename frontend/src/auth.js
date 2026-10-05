import { reactive } from 'vue'  

export const auth = reactive({  
  token: localStorage.getItem('token') || null,  
  user: JSON.parse(localStorage.getItem('user') || 'null'),  
  isAuthenticated() { return !!this.token },  
  setUser(user) {  
    this.user = user  
    localStorage.setItem('user', JSON.stringify(user))  
  },
  login(token, user) {  
    this.token = token  
    this.user = user  
    localStorage.setItem('token', token)  
    localStorage.setItem('user', JSON.stringify(user))  
  },
  logout() {  
    this.token = null  
    this.user = null  
    localStorage.removeItem('token')  
    localStorage.removeItem('user')  
  },
})
