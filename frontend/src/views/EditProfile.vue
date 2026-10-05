<template>
  <div class="auth-page">  
    <div class="auth-card" style="max-width:460px">
      <h1 class="auth-title">Изменить профиль</h1>
      <form @submit.prevent="save" class="auth-form-inner">
        <label class="avatar-edit" style="margin-bottom:8px">
          <img v-if="preview" :src="preview" class="avatar-preview" alt="">  
          <span v-else class="avatar-placeholder">Фото</span>  
          <input type="file" accept="image/*" @change="onFile" hidden>  
        </label>
        <Teleport to="body">
          <CropModal v-if="showCrop" :src="cropSrc" :square="true" @confirm="onCropConfirm" @cancel="showCrop = false" />
        </Teleport>
        <div class="field-wrap">
          <label>Имя</label>
          <input v-model="form.first_name" placeholder="Имя">
        </div>
        <div class="field-wrap">
          <label>Фамилия</label>
          <input v-model="form.last_name" placeholder="Фамилия">
        </div>
        <div class="field-wrap">
          <label>Email</label>
          <input v-model="form.email" type="email" placeholder="email@mail.com">
        </div>
        <div class="field-wrap">
          <label>Дата рождения</label>
          <input v-model="form.birth_date" type="date">
        </div>
        <div class="field-wrap">
          <label>Телефон</label>
          <input v-model="form.phone" placeholder="+79991234567">
        </div>
        <div class="field-wrap">
          <label>О себе</label>
          <textarea v-model="form.bio" placeholder="Пару слов о себе" rows="3"></textarea>
        </div>
        <p v-if="error" class="error">{{ error }}</p>
        <p v-if="saved" class="save-msg">Сохранено ✓</p>  
        <button type="submit" class="btn auth-submit" :disabled="saving">{{ saving ? 'Сохранение...' : 'Сохранить' }}</button>
      </form>
      <div class="settings-section">
        <h2>Сменить пароль</h2>
        <form @submit.prevent="changePassword" class="auth-form-inner">
          <div class="field-wrap">
            <label>Текущий пароль</label>
            <input v-model="oldPwd" type="password" autocomplete="current-password">
          </div>
          <div class="field-wrap">
            <label>Новый пароль</label>
            <input v-model="newPwd" type="password" placeholder="Минимум 8 символов" autocomplete="new-password">
          </div>
          <p v-if="pwdError" class="error">{{ pwdError }}</p>
          <p v-if="pwdSaved" class="save-msg">Пароль изменён ✓</p>
          <button type="submit" class="btn" :disabled="pwdSaving">{{ pwdSaving ? 'Сохранение...' : 'Изменить пароль' }}</button>
        </form>
      </div>
      <div class="settings-section">
        <h2>Приватность</h2>
        <div class="privacy-row">  
          <div>
            <b>Приватный аккаунт</b>
            <p class="muted" style="font-size:13px;margin:2px 0 0">Только подписчики видят ваши посты</p>
          </div>
          <label class="toggle-switch">  
            <input type="checkbox" v-model="privacy.is_private" @change="savePrivacy">
            <span class="toggle-slider"></span>  
          </label>
        </div>
        <div class="field-wrap" style="margin-top:14px">
          <label>Кто может комментировать посты</label>
          <select v-model="privacy.comment_privacy" @change="savePrivacy">  
            <option value="all">Все</option>
            <option value="following">Только подписчики</option>
            <option value="none">Никто</option>
          </select>
        </div>
        <div class="field-wrap">
          <label>Кто может писать в личные сообщения</label>
          <select v-model="privacy.dm_privacy" @change="savePrivacy">
            <option value="all">Все</option>
            <option value="following">Только подписчики</option>
            <option value="none">Никто</option>
          </select>
        </div>
        <p v-if="privacySaved" class="save-msg">Сохранено ✓</p>
      </div>
      <div class="settings-section">
        <h2>Заблокированные пользователи</h2>
        <p v-if="blockedLoading" class="muted">Загрузка...</p>
        <p v-else-if="!blocked.length" class="muted">Нет заблокированных пользователей</p>
        <div v-else class="blocked-list">
          <div v-for="b in blocked" :key="b.id" class="blocked-item">
            <router-link :to="'/user/' + b.username" class="blocked-user-link">
              <div class="modal-avatar" style="width:36px;height:36px">
                <img v-if="b.avatar" :src="b.avatar" alt="">
                <span v-else>{{ b.username[0].toUpperCase() }}</span>
              </div>
              <span>@{{ b.username }}</span>
            </router-link>
            <button class="btn-outline btn-sm" @click="unblock(b)">Разблокировать</button>
          </div>
        </div>
      </div>
      <div class="settings-section danger-zone">
        <h2>Удаление аккаунта</h2>
        <p class="muted" style="margin-bottom:12px">Это действие необратимо. Все ваши посты, комментарии и данные будут удалены.</p>
        <button class="btn btn-danger" @click="deleteAccount">Удалить аккаунт</button>
      </div>
    </div>
  </div>
</template>
<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { auth } from '../auth'
import { showConfirm } from '../confirm'  
import { toastSuccess, toastError } from '../toast'
import CropModal from '../components/CropModal.vue'
const router = useRouter()
const form = reactive({ first_name: '', last_name: '', email: '', birth_date: '', phone: '', bio: '' })  
const privacy = reactive({ is_private: false, comment_privacy: 'all', dm_privacy: 'all' })  
const privacySaved = ref(false)  
const blocked = ref([])  
const blockedLoading = ref(false)  
const file = ref(null)  
const preview = ref(null)  
const cropSrc = ref(null)  
const showCrop = ref(false)  
const error = ref(null)  
const saving = ref(false)  
const saved = ref(false)  
const oldPwd = ref('')  
const newPwd = ref('')  
const pwdError = ref(null)  
const pwdSaving = ref(false)  
const pwdSaved = ref(false)  
function onFile(e) {  
  const raw = e.target.files[0]
  if (!raw) return
  e.target.value = ''  
  cropSrc.value = URL.createObjectURL(raw)  
  showCrop.value = true  
}
function onCropConfirm(croppedFile) {  
  showCrop.value = false  
  file.value = croppedFile  
  preview.value = URL.createObjectURL(croppedFile)  
}
async function save() {  
  error.value = null
  saved.value = false
  saving.value = true
  const fd = new FormData()  
  fd.append('first_name', form.first_name)
  fd.append('last_name', form.last_name)
  fd.append('email', form.email)
  fd.append('bio', form.bio)
  fd.append('phone', form.phone)
  if (form.birth_date) fd.append('birth_date', form.birth_date)  
  if (file.value) fd.append('avatar', file.value)  
  try {
    const data = await api('/api/me/', { method: 'PATCH', body: fd })  
    auth.setUser(data)  
    saved.value = true
  } catch { error.value = 'Не удалось сохранить' }
  finally { saving.value = false }
}
async function changePassword() {  
  pwdError.value = null
  pwdSaved.value = false
  if (!oldPwd.value || !newPwd.value) { pwdError.value = 'Заполни оба поля'; return }
  if (newPwd.value.length < 8) { pwdError.value = 'Новый пароль — минимум 8 символов'; return }
  pwdSaving.value = true
  try {
    const data = await api('/api/me/password/', {  
      method: 'POST',
      body: JSON.stringify({ old_password: oldPwd.value, new_password: newPwd.value }),
    })
    auth.token = data.token  
    localStorage.setItem('token', data.token)  
    pwdSaved.value = true
    oldPwd.value = ''  
    newPwd.value = ''
  } catch (e) {
    pwdError.value = e.old_password || e.detail || 'Ошибка'  
  } finally { pwdSaving.value = false }
}
async function deleteAccount() {  
  const confirmed = await showConfirm('Вы уверены? Аккаунт и все данные будут удалены без возможности восстановления.')
  if (!confirmed) return
  try {
    await api('/api/me/delete/', { method: 'DELETE' })
    auth.logout()  
    router.push('/welcome')  
  } catch {  }
}
async function savePrivacy() {  
  privacySaved.value = false
  try {
    await api('/api/me/', {
      method: 'PATCH',
      body: JSON.stringify({  
        is_private: privacy.is_private,
        comment_privacy: privacy.comment_privacy,
        dm_privacy: privacy.dm_privacy,
      }),
    })
    privacySaved.value = true
    setTimeout(() => { privacySaved.value = false }, 2000)  
  } catch { toastError('Не удалось сохранить настройки приватности') }
}
async function loadBlocked() {  
  blockedLoading.value = true
  try { blocked.value = await api('/api/me/blocked/') }  
  catch {  }
  finally { blockedLoading.value = false }
}
async function unblock(b) {  
  try {
    await api(`/api/users/${b.username}/block/`, { method: 'POST' })  
    blocked.value = blocked.value.filter(x => x.id !== b.id)  
    toastSuccess('Пользователь разблокирован')
  } catch { toastError('Ошибка') }
}
onMounted(async () => {  
  const me = await api('/api/me/')  
  form.first_name = me.first_name || ''
  form.last_name = me.last_name || ''
  form.email = me.email || ''
  form.birth_date = me.birth_date || ''
  form.phone = me.phone || ''
  form.bio = me.bio || ''
  preview.value = me.avatar || null  
  privacy.is_private = me.is_private || false
  privacy.comment_privacy = me.comment_privacy || 'all'
  privacy.dm_privacy = me.dm_privacy || 'all'
  loadBlocked()  
})
</script>