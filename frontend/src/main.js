import { createApp } from 'vue'  
import App from './App.vue'  
import router from './router'  
import './style.css'  
import './theme.js'  

createApp(App)  
  .use(router)  
  .mount('#app')  
