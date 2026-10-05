<template>
  <h1>Уведомления</h1>
  <p v-if="loading">Загрузка...</p>
  <p v-else-if="!notifications.length" class="muted">Уведомлений пока нет.</p>
  <div v-else class="notif-list">  
    <div
      v-for="n in notifications"
      :key="n.id"
      class="notif-item"
      :class="{ unread: !n.is_read }"  
    >
      <router-link :to="'/user/' + n.actor" class="notif-avatar">
        <img v-if="n.actor_avatar" :src="n.actor_avatar" alt="" loading="lazy">
        <span v-else>{{ n.actor[0].toUpperCase() }}</span>
      </router-link>
      <div class="notif-body">  
        <router-link :to="'/user/' + n.actor" class="notif-actor">@{{ n.actor }}</router-link>  
        <span class="notif-text"> {{ typeLabel(n.type) }}</span>  
        <router-link v-if="n.post_id" :to="'/post/' + n.post_id" class="notif-post-link"> → пост</router-link>
      </div>
      <span class="notif-time">{{ formatTime(n.created_at) }}</span>  
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'
const notifications = ref([])  
const loading = ref(true)
const labels = {  
  like: 'лайкнул(а) ваш пост',
  comment: 'прокомментировал(а) ваш пост',
  follow: 'подписался(ась) на вас',
  repost: 'сделал(а) репост вашего поста',
  mention: 'упомянул(а) вас в комментарии',
}
function typeLabel(t) { return labels[t] || t }  
function formatTime(s) {  
  const d = new Date(s)
  const now = new Date()
  const diff = Math.floor((now - d) / 1000)  
  if (diff < 60) return 'только что'  
  if (diff < 3600) return Math.floor(diff / 60) + ' мин назад'  
  if (diff < 86400) return Math.floor(diff / 3600) + ' ч назад'  
  return d.toLocaleDateString('ru-RU')  
}
onMounted(async () => {
  try {
    notifications.value = await api('/api/notifications/')  
    await api('/api/notifications/read/', { method: 'POST' })  
  } finally {
    loading.value = false
  }
})
</script>