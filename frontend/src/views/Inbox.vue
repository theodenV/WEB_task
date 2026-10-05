<template>
  <h1>Сообщения</h1>
  <p v-if="loading" class="muted">Загрузка...</p>
  <div class="inbox-list">  
    <router-link v-for="p in partners" :key="p.id" :to="'/messages/' + p.username" class="inbox-item">
      <div class="inbox-avatar">  
        <img v-if="p.avatar" :src="p.avatar" alt="">
        <span v-else>{{ p.username[0].toUpperCase() }}</span>
      </div>
      <div class="inbox-body">  
        <div class="inbox-username">@{{ p.username }}<span v-if="p.first_name" class="inbox-name"> · {{ p.first_name }}</span></div>
        <div class="inbox-preview">  
          <span v-if="p.last_image">📷 Фото</span>  
          <span v-else-if="p.last_message">{{ p.last_message.slice(0, 60) }}{{ p.last_message.length > 60 ? '...' : '' }}</span>
          <span v-else class="muted">Нет сообщений</span>  
        </div>
      </div>
      <span v-if="p.last_timestamp" class="inbox-time">{{ formatTime(p.last_timestamp) }}</span>
    </router-link>
  </div>
  <p v-if="!loading && !partners.length" class="empty-state">
    <span class="empty-icon">💬</span>
    <span>Переписок пока нет</span>
    <span class="muted" style="font-size:14px;font-weight:400">Напиши кому-нибудь с его профиля</span>
  </p>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'
const partners = ref([])  
const loading = ref(true)
function formatTime(ts) {  
  const d = new Date(ts)
  const now = new Date()
  const diff = Math.floor((now - d) / 1000)  
  if (diff < 60) return 'только что'
  if (diff < 3600) return Math.floor(diff / 60) + ' мин'  
  if (diff < 86400) return Math.floor(diff / 3600) + ' ч'
  return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })  
}
onMounted(async () => {
  try { partners.value = await api('/api/chat/') } finally { loading.value = false }
})
</script>