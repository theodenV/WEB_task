<template>
  <div class="auth-page">  
    <div class="auth-card">  
      <h1 class="auth-title">Регистрация</h1>
      <form @submit.prevent="submit" class="auth-form-inner" novalidate>  
        <div class="field-wrap" :class="form.username ? (usernameChecking ? '' : (getError('username') ? 'field-invalid' : 'field-valid')) : ''">
          <label>Логин</label>
          <input v-model="form.username" placeholder="Только латиница, цифры и _" autocomplete="username" @input="onUsernameInput">  
          <span v-if="usernameChecking && form.username && !usernameFormatError" class="field-checking-msg">Проверка...</span>  
          <span v-else-if="isFieldOk('username')" class="field-ok">✓</span>  
          <span v-else-if="isFieldErr('username')" class="field-err-msg">{{ getError('username') }}</span>  
        </div>
        <div class="field-wrap" :class="fieldClass('first_name')">  
          <label>Имя</label>
          <input v-model="form.first_name" placeholder="Ваше имя">
          <span v-if="isFieldOk('first_name')" class="field-ok">✓</span>
        </div>
        <div class="field-wrap" :class="fieldClass('last_name')">
          <label>Фамилия</label>
          <input v-model="form.last_name" placeholder="Ваша фамилия">
          <span v-if="isFieldOk('last_name')" class="field-ok">✓</span>
        </div>
        <div class="field-wrap" :class="fieldClass('email')">
          <label>Email</label>
          <input v-model="form.email" type="email" placeholder="example@mail.com" autocomplete="email">
          <span v-if="isFieldOk('email')" class="field-ok">✓</span>
          <span v-else-if="isFieldErr('email')" class="field-err-msg">{{ getError('email') }}</span>
        </div>
        <div class="field-wrap" :class="fieldClass('birth_date')">
          <label>Дата рождения</label>
          <input v-model="form.birth_date" type="date">  
          <span v-if="isFieldOk('birth_date')" class="field-ok">✓</span>
          <span v-else-if="isFieldErr('birth_date')" class="field-err-msg">{{ getError('birth_date') }}</span>
        </div>
        <div class="field-wrap" :class="fieldClass('phone')">
          <label>Телефон <span class="field-optional">(не обязательно)</span></label>  
          <input v-model="form.phone" placeholder="+79991234567" autocomplete="tel">
          <span v-if="isFieldOk('phone')" class="field-ok">✓</span>
          <span v-else-if="isFieldErr('phone')" class="field-err-msg">{{ getError('phone') }}</span>
        </div>
        <div class="field-wrap" :class="fieldClass('password')">
          <label>Пароль</label>
          <input v-model="form.password" type="password" placeholder="Минимум 8 символов" autocomplete="new-password">
          <span v-if="isFieldOk('password')" class="field-ok">✓</span>
          <span v-else-if="isFieldErr('password')" class="field-err-msg">{{ getError('password') }}</span>
        </div>
        <div class="field-wrap" :class="fieldClass('password2')">
          <label>Повтор пароля</label>
          <input v-model="form.password2" type="password" placeholder="Повторите пароль" autocomplete="new-password">
          <span v-if="isFieldOk('password2')" class="field-ok">✓</span>
          <span v-else-if="isFieldErr('password2')" class="field-err-msg">{{ getError('password2') }}</span>
        </div>
        <ul v-if="serverErrors.length" class="error server-errors">  
          <li v-for="(e, i) in serverErrors" :key="i">{{ e }}</li>  
        </ul>
        <button type="submit" class="btn auth-submit" :disabled="loading">  
          {{ loading ? 'Регистрация...' : 'Зарегистрироваться' }}
        </button>
        <p class="auth-switch">Уже есть аккаунт? <router-link to="/login">Войти</router-link></p>
      </form>
    </div>
  </div>
</template>
<script setup>
import { reactive, ref, computed } from 'vue'  
import { useRouter } from 'vue-router'  
import { api } from '../api'  
import { auth } from '../auth'  
const router = useRouter()
const loading = ref(false)  
const serverErrors = ref([])  
const form = reactive({  
  username: '', first_name: '', last_name: '',
  email: '', birth_date: '', phone: '',
  password: '', password2: '',
})
const usernameChecking = ref(false)  
const usernameTaken = ref(false)  
let usernameTimer = null  
const usernameFormatError = computed(() => {  
  const v = form.username
  if (!v) return null  
  if (!/^[A-Za-z0-9_]+$/.test(v)) return 'Только латиница, цифры и _'  
  if (v.length < 3) return 'Минимум 3 символа'  
  return null  
})
function onUsernameInput() {  
  usernameTaken.value = false  
  usernameChecking.value = false  
  clearTimeout(usernameTimer)  
  if (!form.username || usernameFormatError.value) return  
  usernameChecking.value = true  
  usernameTimer = setTimeout(async () => {  
    try {
      await api('/api/users/' + form.username + '/')  
      usernameTaken.value = true  
    } catch {
      usernameTaken.value = false  
    } finally {
      usernameChecking.value = false  
    }
  }, 400)  
}
function getError(field) {  
  const v = form[field]
  if (!v) return null  
  switch (field) {
    case 'username':
      if (usernameFormatError.value) return usernameFormatError.value  
      if (usernameTaken.value) return 'Имя пользователя уже занято'  
      break
    case 'first_name':
    case 'last_name':
      break  
    case 'email':
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) return 'Неверный формат email'  
      break
    case 'birth_date': {
      const d = new Date(v)  
      const now = new Date()
      if (isNaN(d.getTime())) return 'Неверная дата'  
      if (d > now) return 'Дата в будущем'  
      if (now.getFullYear() - d.getFullYear() < 10) return 'Слишком молодой возраст'  
      break
    }
    case 'phone':
      if (!/^\+?\d{10,15}$/.test(v)) return 'Формат: +79991234567'  
      break
    case 'password':
      if (v.length < 8) return 'Минимум 8 символов'
      break
    case 'password2':
      if (v !== form.password) return 'Пароли не совпадают'  
      break
  }
  return null  
}
function getSubmitError(field) {  
  const v = form[field]
  const required = ['username', 'first_name', 'last_name', 'email', 'birth_date', 'password', 'password2']  
  if (!v && required.includes(field)) return 'Обязательное поле'  
  return getError(field)  
}
function fieldClass(field) {  
  const v = form[field]
  if (!v) return ''  
  return getError(field) ? 'field-invalid' : 'field-valid'  
}
function isFieldOk(field) {  
  return !!form[field] && !getError(field)  
}
function isFieldErr(field) {  
  return !!form[field] && !!getError(field)
}
async function submit() {  
  if (usernameChecking.value) return  
  const fields = ['username', 'first_name', 'last_name', 'email', 'birth_date', 'phone', 'password', 'password2']
  const hasErrors = fields.some(f => getSubmitError(f))  
  if (hasErrors) {
    const msgs = fields.map(f => getSubmitError(f)).filter(Boolean)  
    serverErrors.value = [...new Set(msgs)]  
    return  
  }
  serverErrors.value = []  
  loading.value = true
  try {
    const data = await api('/api/auth/register/', {  
      method: 'POST',
      body: JSON.stringify({
        username: form.username,
        first_name: form.first_name,
        last_name: form.last_name,
        email: form.email,
        birth_date: form.birth_date || null,  
        phone: form.phone,
        password: form.password,
      }),
    })
    auth.login(data.token, data.user)  
    router.push('/')  
  } catch (e) {
    serverErrors.value = Object.values(e).flat()  
  } finally {
    loading.value = false
  }
}
</script>