<template>
  <div v-if="tag" class="tag-header">
    <h1>#{{ tag.name }}</h1>
    <p class="muted">Посты с тегом #{{ tag.name }}</p>
  </div>
  <p v-if="loading && !posts.length">Загрузка...</p>  
  <p v-else-if="error" class="error">{{ error }}</p>
  <div class="feed-masonry">  
    <div v-for="post in posts" :key="post.id" class="feed-pin">
      <PostCard :post="post" :collections="myCollections" />
    </div>
  </div>
  <p v-if="!loading && !error && !posts.length" class="empty-state">
    <span class="empty-icon">🏷️</span>
    <span>Постов с этим тегом нет</span>
  </p>
  <div v-if="nextUrl" ref="sentinel" class="scroll-sentinel"></div>  
  <p v-if="loading && posts.length" class="muted" style="text-align:center;padding:16px">Загрузка...</p>
</template>
<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'
import { auth } from '../auth'
import PostCard from '../components/PostCard.vue'
const route = useRoute()
const posts = ref([])  
const tag = ref(null)  
const loading = ref(false)
const error = ref(null)
const nextUrl = ref(null)  
const sentinel = ref(null)  
const myCollections = ref([])  
let observer = null  
async function load() {  
  loading.value = true
  error.value = null
  posts.value = []
  nextUrl.value = null
  try {
    const data = await api('/api/tags/' + route.params.slug + '/')  
    tag.value = data.tag  
    posts.value = data.results  
    nextUrl.value = data.next
  } catch { error.value = 'Тег не найден' }
  finally { loading.value = false }
}
async function loadMore() {  
  if (!nextUrl.value || loading.value) return
  loading.value = true
  try {
    const url = new URL(nextUrl.value)
    const data = await api(url.pathname + url.search)
    posts.value.push(...data.results)  
    nextUrl.value = data.next
  } finally { loading.value = false }
}
watch(sentinel, (el) => {  
  if (observer) { observer.disconnect(); observer = null }
  if (el) {
    observer = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && !loading.value) loadMore()
    }, { rootMargin: '300px' })
    observer.observe(el)
  }
})
onUnmounted(() => { if (observer) observer.disconnect() })
watch(() => route.params.slug, load)  
onMounted(async () => {
  load()
  if (auth.isAuthenticated()) {
    try { myCollections.value = await api('/api/collections/') } catch {  }
  }
})
</script>