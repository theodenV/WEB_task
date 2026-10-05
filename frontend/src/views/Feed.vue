<template>
  <div class="feed-controls">  
    <div class="feed-tabs">  
      <button :class="{ active: feed === 'all' }" @click="switchFeed('all')">Обзор</button>  
      <button :class="{ active: feed === 'following' }" @click="switchFeed('following')">Подписки</button>  
    </div>
    <div class="sort-controls">  
      <div class="sort-group">
        <button :class="{ active: sortBy === 'time' }" @click="setSortBy('time')">По времени</button>
        <button :class="{ active: sortBy === 'popular' }" @click="setSortBy('popular')">По популярности</button>
      </div>
      <button class="sort-dir-btn" :title="sortDir === 'desc' ? 'По убыванию' : 'По возрастанию'" @click="toggleDir">
        {{ sortDir === 'desc' ? '↓' : '↑' }}  
      </button>
    </div>
  </div>
  <div class="color-filter-row">
    <button
      v-for="c in COLOR_SWATCHES"  
      :key="c.key"
      class="color-swatch"
      :class="{ active: selectedColor === c.key, 'swatch-light': c.key === 'white' }"
      :style="{ background: c.css }"  
      :title="c.label"  
      @click="pickColor(c.key)"  
    ></button>
    <button v-if="selectedColor !== null" class="color-clear-btn" @click="pickColor(null)" title="Сбросить">✕</button>
  </div>
  <h1 v-if="route.query.q" style="margin-bottom:16px">Результаты по «{{ route.query.q }}»</h1>
  <p v-if="error" class="error">{{ error }}</p>
  <div v-else class="feed-masonry">  
    <template v-if="loading && !posts.length">  
      <div v-for="n in 8" :key="'sk' + n" class="feed-pin">
        <SkeletonCard />  
      </div>
    </template>
    <template v-else>  
      <div v-for="post in posts" :key="post.id" class="feed-pin">
        <PostCard
          :post="post"
          :collections="myCollections"  
          @delete="handleDelete"  
        />
      </div>
    </template>
  </div>
  <p v-if="!loading && !error && !posts.length && feed === 'following'" class="feed-empty">
    Вы ещё ни на кого не подписаны, или у них нет постов.<br>
    <button class="link-btn" @click="switchFeed('all')">Перейти в обзор</button>
  </p>
  <p v-else-if="!loading && !error && !posts.length">Ничего не найдено.</p>  
  <div v-if="nextUrl" ref="sentinel" class="scroll-sentinel"></div>
  <p v-if="loading && posts.length" class="muted" style="text-align:center;padding:16px">Загрузка...</p>
</template>
<script>
export default { name: 'Feed' }  
</script>
<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'  
import { api } from '../api'
import { auth } from '../auth'
import { showConfirm } from '../confirm'
import { toastSuccess, toastError } from '../toast'
import PostCard from '../components/PostCard.vue'
import SkeletonCard from '../components/SkeletonCard.vue'
const route = useRoute()  
const posts = ref([])  
const loading = ref(false)  
const error = ref(null)  
const nextUrl = ref(null)  
const feed = ref('all')  
const sortBy = ref('time')  
const sortDir = ref('desc')  
const sentinel = ref(null)  
const myCollections = ref([])  
const selectedColor = ref(null)  
let observer = null  
const COLOR_SWATCHES = [  
  { key: 'red',    css: 'hsl(0,90%,50%)',    label: 'Красный' },
  { key: 'orange', css: 'hsl(25,95%,55%)',   label: 'Оранжевый' },
  { key: 'yellow', css: 'hsl(55,100%,50%)',  label: 'Жёлтый' },
  { key: 'green',  css: 'hsl(120,65%,40%)',  label: 'Зелёный' },
  { key: 'cyan',   css: 'hsl(190,80%,45%)',  label: 'Голубой' },
  { key: 'blue',   css: 'hsl(225,80%,55%)',  label: 'Синий' },
  { key: 'purple', css: 'hsl(280,65%,50%)',  label: 'Фиолетовый' },
  { key: 'black',  css: '#1a1a1a',           label: 'Чёрный' },
  { key: 'white',  css: '#f0f0f0',           label: 'Белый' },
  { key: 'gray',   css: '#888888',           label: 'Серый' },
]
function pickColor(key) {  
  selectedColor.value = key  
  load()
}
function sortParam() {  
  if (sortBy.value === 'popular') return sortDir.value === 'desc' ? 'popular' : 'popular_asc'
  return sortDir.value === 'desc' ? 'new' : 'old'  
}
function buildUrl() {  
  const params = new URLSearchParams()
  if (feed.value === 'following') params.set('feed', 'following')  
  if (route.query.q) params.set('q', route.query.q)  
  const s = sortParam()
  if (s !== 'new') params.set('sort', s)  
  if (selectedColor.value !== null) params.set('color', selectedColor.value)
  const qs = params.toString()
  return '/api/posts/' + (qs ? '?' + qs : '')  
}
async function load() {  
  loading.value = true
  error.value = null
  posts.value = []  
  nextUrl.value = null
  try {
    const data = await api(buildUrl())  
    posts.value = data.results  
    nextUrl.value = data.next  
  } catch { error.value = 'Ошибка загрузки' }
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
  } catch { error.value = 'Ошибка загрузки' }
  finally { loading.value = false }
}
function switchFeed(mode) {  
  feed.value = mode
  load()
}
function setSortBy(v) { sortBy.value = v; load() }  
function toggleDir() { sortDir.value = sortDir.value === 'desc' ? 'asc' : 'desc'; load() }  
async function handleDelete(post) {  
  if (!(await showConfirm('Удалить этот пост?'))) return  
  try {
    await api(`/api/posts/${post.id}/`, { method: 'DELETE' })
    posts.value = posts.value.filter(p => p.id !== post.id)  
    toastSuccess('Пост удалён')
  } catch { toastError('Не удалось удалить пост') }
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
watch(() => route.query.q, load)  
onMounted(async () => {  
  load()
  if (auth.isAuthenticated()) {
    try { myCollections.value = await api('/api/collections/') } catch {  }
  }
})
</script>