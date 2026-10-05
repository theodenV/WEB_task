<template>
  <div class="auth-page">  
    <div class="auth-card">  
      <h1 class="auth-title">Вход</h1>  
      <form @submit.prevent="submit" class="auth-form-inner">  
        <div class="field-wrap">  
          <label>Логин или Email</label>
          <input
            v-model="login"  
            placeholder="username или email@mail.com"
            autocomplete="username"  
            title="Введите логин или email"  
          >
        </div>
        <div class="field-wrap">
          <label>Пароль</label>
          <input
            v-model="password"  
            type="password"  
            placeholder="Пароль"
            autocomplete="current-password"  
            title="Введите пароль"
          >
        </div>
        <p v-if="error" class="error">{{ error }}</p>  
        <button type="submit" class="btn auth-submit" :disabled="loading">  
          {{ loading ? 'Вхожу...' : 'Войти' }}  
        </button>
        <p class="auth-switch">Нет аккаунта? <router-link to="/register">Регистрация</router-link></p>  
      </form>
    </div>
  </div>
</template>
<script setup>
import { ref } from 'vue'  
import { useRouter } from 'vue-router'  
import { api } from '../api'  
import { auth } from '../auth'  
const login = ref('')  
const password = ref('')  
const error = ref(null)  
const loading = ref(false)  
const router = useRouter()  
async function submit() {  
  error.value = null  
  loading.value = true  
  try {
    const data = await api('/api/auth/login/', {  
      method: 'POST',
      body: JSON.stringify({ username: login.value, password: password.value }),  
    })
    auth.login(data.token, data.user)  
    router.push('/')  
  } catch (e) {
    if (e.code === 'account_banned') return  
    error.value = e.detail || 'Неверный логин/email или пароль'  
  } finally {
    loading.value = false  
  }
}
</script>