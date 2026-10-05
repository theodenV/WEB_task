<template>
  <div class="collections-header">  
    <h1>Мои коллекции</h1>
    <button class="btn collections-add-btn" title="Создать коллекцию" @click="showCreate = true">＋</button>
  </div>
  <p v-if="loadError" class="error">Не удалось загрузить коллекции</p>
  <div class="collection-grid">  
    <router-link v-for="c in collections" :key="c.id" :to="'/collection/' + c.id" class="board-card">
      <div class="board-cover">  
        <template v-if="c.preview_images && c.preview_images.length">
          <img v-for="(img, i) in c.preview_images" :key="i" :src="img" alt="">
        </template>
        <div v-else class="board-empty"></div>  
      </div>
      <h3>{{ c.name }}</h3>
      <p>{{ c.posts_count }} пинов · {{ c.is_public ? 'публичная' : 'приватная' }}</p>
    </router-link>
  </div>
  <p v-if="!loading && !collections.length" class="empty-state">
    <span class="empty-icon">🗂️</span>
    <span>Коллекций пока нет</span>
    <span class="muted" style="font-size:14px;font-weight:400">Нажми «＋» выше, чтобы создать</span>
  </p>
  <div v-if="showCreate" class="modal-overlay" @click.self="showCreate = false">
    <div class="modal" style="padding:28px 24px">
      <div class="modal-head" style="margin-bottom:18px">
        <h2 style="margin:0">Новая коллекция</h2>
        <button class="modal-close" @click="showCreate = false">✕</button>
      </div>
      <div class="field-wrap" style="margin-bottom:14px">
        <label>Название</label>
        <input v-model="newName" placeholder="Название коллекции" @keyup.enter="create">
      </div>
      <label style="display:flex;align-items:center;gap:8px;margin-bottom:20px;font-weight:600;cursor:pointer">
        <input type="checkbox" v-model="newPrivate"> Приватная
      </label>
      <p v-if="createError" class="error">{{ createError }}</p>
      <div style="display:flex;gap:10px">
        <button class="btn" :disabled="creating" @click="create">{{ creating ? '...' : 'Создать' }}</button>
        <button class="btn-outline" @click="showCreate = false">Отмена</button>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'
const collections = ref([])  
const loading = ref(true)  
const loadError = ref(false)  
const showCreate = ref(false)  
const newName = ref('')  
const newPrivate = ref(false)  
const creating = ref(false)  
const createError = ref(null)  
async function load() {  
  loading.value = true
  try { collections.value = await api('/api/collections/'); loadError.value = false }  
  catch { loadError.value = true }
  finally { loading.value = false }
}
async function create() {  
  createError.value = null
  if (!newName.value.trim()) { createError.value = 'Введите название'; return }
  creating.value = true
  try {
    await api('/api/collections/', {  
      method: 'POST',
      body: JSON.stringify({ name: newName.value, is_public: !newPrivate.value }),
    })
    newName.value = ''  
    newPrivate.value = false
    showCreate.value = false  
    load()  
  } catch { createError.value = 'Не удалось создать' }
  finally { creating.value = false }
}
onMounted(load)  
</script>