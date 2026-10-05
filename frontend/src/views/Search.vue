<template>
  <div class="search-page">
    <h1 v-if="query">Поиск: «{{ query }}»</h1>  
    <p v-else class="muted" style="padding:32px 0;text-align:center">Введи запрос в строку поиска выше</p>
    <template v-if="query">  
      <p v-if="loading" class="muted">Загрузка...</p>
      <template v-else>
        <div v-if="tags.length">
          <div class="search-section-title">Теги</div>
          <div class="trending-tags" style="margin-bottom:24px">
            <router-link v-for="t in tags" :key="t.id" :to="'/tag/' + t.slug" class="tag-chip">
              #{{ t.name }}  
            </router-link>
          </div>
        </div>
        <div v-if="users.length">
          <div class="search-section-title">Люди</div>
          <div class="user-list">
            <router-link v-for="u in users" :key="u.id" :to="'/user/' + u.username" class="user-item">
              <div class="user-item-avatar">
                <img v-if="u.avatar" :src="u.avatar" alt="" loading="lazy">
                <span v-else>{{ u.username[0].toUpperCase() }}</span>  
              </div>
              <div class="user-item-info">
                <div class="user-item-name">@{{ u.username }}</div>
                <div v-if="u.first_name" class="user-item-full">{{ u.first_name }}</div>
              </div>
            </router-link>
          </div>
        </div>
        <div v-if="posts.length">
          <div class="search-section-title">Посты</div>
          <div class="feed-masonry">  
            <div v-for="post in posts" :key="post.id" class="feed-pin">
              <PostCard :post="post" :collections="myCollections" />
            </div>
          </div>
        </div>
        <p v-if="!tags.length && !users.length && !posts.length" class="empty-state">
          <span class="empty-icon">🔍</span>
          <span>Ничего не найдено по запросу «{{ query }}»</span>
        </p>
      </template>
    </template>
  </div>
</template>
<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'  
import { api } from '../api'
import { auth } from '../auth'
import PostCard from '../components/PostCard.vue'
const route = useRoute()
const tags = ref([])  
const users = ref([])  
const posts = ref([])  
const loading = ref(false)  
const query = ref(route.query.q || '')  
const myCollections = ref([])  
async function search(q) {  
  query.value = q
  if (!q) { tags.value = []; users.value = []; posts.value = []; return }  
  loading.value = true
  try {
    const [t, u, p] = await Promise.all([  
      api(`/api/tags/?q=${encodeURIComponent(q)}`),  
      api(`/api/users/search/?q=${encodeURIComponent(q)}`),  
      api(`/api/posts/?q=${encodeURIComponent(q)}`),  
    ])
    tags.value = t.results ?? t  
    users.value = u.results ?? u
    posts.value = p.results ?? p
  } finally { loading.value = false }
}
watch(() => route.query.q, (q) => search(q || ''))  
onMounted(async () => {
  if (query.value) search(query.value)  
  if (auth.isAuthenticated()) {
    try { myCollections.value = await api('/api/collections/') } catch {  }
  }
})
</script>