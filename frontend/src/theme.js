import { ref } from 'vue'  

const KEY = 'pingram-theme'  

export const isDark = ref(localStorage.getItem(KEY) === 'dark')  

function applyTheme() {  
  document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')  
}

export function toggleTheme() {  
  isDark.value = !isDark.value  
  localStorage.setItem(KEY, isDark.value ? 'dark' : 'light')  
  document.documentElement.classList.add('theme-transitioning')  
  applyTheme()  
  setTimeout(() => {  
    document.documentElement.classList.remove('theme-transitioning')  
  }, 400)  
}

applyTheme()  
