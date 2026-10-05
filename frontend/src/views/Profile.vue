<template>
  <p v-if="loading">Загрузка...</p>
  <p v-else-if="error" class="error">{{ error }}</p>
  <div v-else>
    <div class="profile-cover" :style="user.cover ? { backgroundImage: `url(${user.cover})` } : {}">
      <label v-if="isMe" class="cover-change-btn" title="Изменить обложку">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/>
          <circle cx="12" cy="13" r="4"/>
        </svg>  
        <input type="file" accept="image/*" hidden @change="changeCover">
      </label>
    </div>
    <div class="profile-head">  
      <div class="avatar-wrap">  
        <label v-if="isMe && !user.avatar" class="profile-avatar" style="cursor:pointer" title="Загрузить аватар">
          <span>{{ user.username[0].toUpperCase() }}</span>  
          <input type="file" accept="image/*" hidden @change="changeAvatarWithCrop">
        </label>
        <div v-else class="profile-avatar" @click="clickAvatar" style="cursor:pointer">
          <img v-if="user.avatar" :src="user.avatar" alt="">
          <span v-else>{{ user.username[0].toUpperCase() }}</span>
        </div>
        <span v-if="user.is_online && !isMe" class="online-dot online-dot-lg" title="Онлайн"></span>
      </div>
      <Teleport to="body">
        <CropModal v-if="avatarCropSrc" :src="avatarCropSrc" :square="true"
          @confirm="onAvatarCropConfirm" @cancel="avatarCropSrc = null" />
      </Teleport>
      <h1>{{ (user.first_name + ' ' + (user.last_name || '')).trim() || '@' + user.username }}</h1>
      <p v-if="user.first_name || user.last_name" class="username">@{{ user.username }}</p>
      <p class="counts">  
        <button class="count-btn" @click="openList('followers')"><b>{{ user.followers_count }}</b> подписчиков</button>
        ·
        <button class="count-btn" @click="openList('following')"><b>{{ user.following_count }}</b> подписок</button>
      </p>
      <p v-if="user.bio" class="bio">{{ user.bio }}</p>  
      <div class="profile-buttons" v-if="auth.isAuthenticated() && !isMe">
        <template v-if="user.is_blocking_me">  
          <p class="muted" style="font-size:14px">Пользователь ограничил доступ к профилю</p>
        </template>
        <template v-else>
          <button class="btn" @click="toggleFollow">
            {{ user.is_following ? 'Отписаться' : (user.has_pending_request ? 'Запрос отправлен' : 'Подписаться') }}
          </button>
          <template v-if="!user.is_blocked">
            <button
              v-if="!user.dm_privacy || user.dm_privacy === 'all' || (user.dm_privacy === 'following' && user.is_following)"
              class="btn-outline" @click="requestOpenChat(user)">Сообщение</button>
            <span v-else class="muted" style="font-size:13px">Личные сообщения ограничены</span>
          </template>
          <button class="btn-outline" @click="toggleBlock">{{ user.is_blocked ? 'Разблокировать' : 'Заблокировать' }}</button>
          <button class="btn-outline" @click="reportDialog = true; reportSent = false; reportReason = ''; reportDetail = ''" title="Пожаловаться">⚑</button>
        </template>
      </div>
      <div class="profile-buttons" v-else-if="isMe">
        <router-link to="/settings" class="btn-outline">Изменить профиль</router-link>
      </div>
    </div>
    <div class="tabs">
      <button :class="{ active: tab === 'posts' }" @click="selectTab('posts')">Созданные</button>
      <button v-if="user.collections?.length" :class="{ active: tab === 'collections' }" @click="selectTab('collections')">Сохранённые</button>
      <button :class="{ active: tab === 'reposts' }" @click="selectTab('reposts')">Репосты</button>
      <button :class="{ active: tab === 'liked' }" @click="selectTab('liked')">Понравившиеся</button>
      <button v-if="isMe && returnedPosts.length" :class="{ active: tab === 'returned' }" @click="selectTab('returned')">Возвращённые</button>
    </div>
    <div v-if="tab === 'returned'">
      <p v-if="returnedLoading" class="muted">Загрузка...</p>
      <p v-else-if="!returnedPosts.length" class="empty-state">
        <span class="empty-icon">✅</span><span>Нет возвращённых постов</span>
      </p>
      <div v-else class="mod-list">
        <div v-for="post in returnedPosts" :key="post.id" class="mod-card">
          <router-link :to="'/post/' + post.id">
            <img v-if="post.image" :src="post.image" class="mod-img" alt="">
            <video v-else-if="post.video" :src="post.video" class="mod-img" muted preload="metadata"></video>
            <div v-else class="mod-img mod-img-placeholder">—</div>
          </router-link>
          <div class="mod-info">
            <p class="mod-caption">{{ post.caption || '—' }}</p>
            <div class="returned-reason">
              <span class="returned-reason-label">Причина возврата:</span>
              {{ post.rejection_reason }}  
            </div>
            <span class="mod-date">{{ formatDate(post.created_at) }}</span>
          </div>
          <div class="mod-actions">
            <router-link :to="'/post/' + post.id" class="btn-outline">Просмотреть</router-link>
          </div>
        </div>
      </div>
    </div>
    <div v-else-if="tab === 'collections'" class="collection-grid">
      <router-link v-for="c in user.collections" :key="c.id" :to="'/collection/' + c.id" class="board-card">
        <div class="board-cover">  
          <template v-if="c.preview_images.length">
            <img v-for="(img, i) in c.preview_images.filter(Boolean)" :key="i" :src="img" alt="">
          </template>
          <div v-else class="board-empty"></div>  
        </div>
        <h3>{{ c.name }}</h3>
        <p>{{ c.posts_count }} пинов · {{ c.is_public ? 'публичная' : 'приватная' }}</p>
      </router-link>
    </div>
    <div v-else-if="user.is_private && !user.is_following && !isMe" class="private-account">
      <div class="private-icon">🔒</div>
      <p><b>Это приватный аккаунт</b></p>
      <p class="muted">Подпишитесь, чтобы видеть посты</p>
    </div>
    <template v-else-if="['posts', 'reposts', 'liked'].includes(tab)">
      <div class="feed-masonry">
        <template v-if="tabLoading && !tabState[tab].list.length">  
          <div v-for="n in 6" :key="'sk' + n" class="feed-pin">
            <SkeletonCard />
          </div>
        </template>
        <template v-else>
          <div v-for="post in tabState[tab].list" :key="post.id" class="feed-pin">
            <PostCard :post="post" :collections="myCollections" @delete="p => deletePost(p.id)" />
          </div>
        </template>
      </div>
      <p v-if="!tabLoading && !tabState[tab].list.length" class="empty-state">
        <span class="empty-icon">{{ emptyIcons[tab] }}</span>  
        <span>{{ emptyMessages[tab] }}</span>  
      </p>
      <div v-if="tabState[tab].next" ref="sentinel" class="scroll-sentinel"></div>
    </template>
  </div>
  <div v-if="listModal" class="modal-overlay" @click.self="listModal = null">
    <div class="modal">
      <div class="modal-head">
        <h2>{{ listModal === 'followers' ? 'Подписчики' : 'Подписки' }}</h2>
        <button class="modal-close" @click="listModal = null">✕</button>
      </div>
      <p v-if="listLoading" class="muted" style="padding:16px">Загрузка...</p>
      <p v-else-if="listError" class="error" style="padding:16px">{{ listError }}</p>
      <p v-else-if="!listUsers.length" class="muted" style="padding:16px">Пусто</p>
      <div v-else class="modal-list">
        <router-link v-for="u in listUsers" :key="u.id" :to="'/user/' + u.username" class="modal-user" @click="listModal = null">
          <div style="position:relative;flex-shrink:0">
            <div class="modal-avatar">
              <img v-if="u.avatar" :src="u.avatar" alt="">
              <span v-else>{{ u.username[0].toUpperCase() }}</span>
            </div>
            <span v-if="u.is_online" class="online-dot" title="Онлайн"></span>  
          </div>
          <div>
            <div class="modal-username">@{{ u.username }}</div>
            <div v-if="u.first_name" class="modal-name">{{ u.first_name }}</div>
          </div>
        </router-link>
      </div>
    </div>
  </div>
  <div v-if="reportDialog" class="modal-overlay" @click.self="reportDialog = false">
    <div class="modal" style="max-width:400px">
      <div class="modal-head">
        <h2>Пожаловаться на @{{ user?.username }}</h2>  
        <button class="modal-close" @click="reportDialog = false">✕</button>
      </div>
      <div v-if="reportSent" style="text-align:center;padding:16px 0">  
        <p style="font-size:18px">✓</p>
        <p>Жалоба отправлена</p>
      </div>
      <template v-else>  
        <select v-model="reportReason" style="width:100%;margin-bottom:12px">
          <option value="" disabled>Выберите причину...</option>
          <option value="spam">Спам</option>
          <option value="inappropriate">Неприемлемый контент</option>
          <option value="harassment">Оскорбление или травля</option>
          <option value="fake">Фейковый аккаунт</option>
          <option value="other">Другое</option>
        </select>
        <textarea v-model="reportDetail" rows="2" placeholder="Подробности (необязательно)" style="width:100%;resize:vertical;margin-bottom:12px"></textarea>
        <div style="display:flex;gap:10px">
          <button class="btn btn-danger" :disabled="!reportReason || reportSending" @click="submitUserReport">
            {{ reportSending ? '...' : 'Отправить' }}
          </button>
          <button class="btn-outline" @click="reportDialog = false">Отмена</button>
        </div>
      </template>
    </div>
  </div>
  <Teleport to="body">
    <div v-if="avatarLightbox" class="lightbox" @click="avatarLightbox = false; avatarMenuOpen = false" @wheel.prevent="onAvatarWheel">
      <img :src="user?.avatar" alt="" :style="{ transform: `scale(${avatarLightboxScale})`, transition: 'transform 0.1s' }" @click.stop>
      <button class="lightbox-close" @click.stop="avatarLightbox = false">✕</button>
      <div class="lightbox-menu" @click.stop>  
        <button class="lightbox-dots" @click.stop="avatarMenuOpen = !avatarMenuOpen">⋯</button>
        <div v-if="avatarMenuOpen" class="lightbox-dropdown">
          <a :href="user?.avatar" class="lightbox-option" @click.prevent="downloadImage(user.avatar)">Скачать</a>
          <label v-if="isMe" class="lightbox-option" style="cursor:pointer">
            Изменить
            <input type="file" accept="image/*" hidden @change="changeAvatar">
          </label>
        </div>
      </div>
    </div>
  </Teleport>
</template>
<script setup>
import { ref, reactive, computed, watch, onUnmounted, onMounted } from 'vue'
const profileTabMemory = {}  
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'
import { auth } from '../auth'
import { showConfirm } from '../confirm'
import { toastSuccess, toastError } from '../toast'
import { requestOpenChat } from '../openChat'  
import PostCard from '../components/PostCard.vue'
import SkeletonCard from '../components/SkeletonCard.vue'
import CropModal from '../components/CropModal.vue'  
const route = useRoute()
const router = useRouter()
const user = ref(null)  
const loading = ref(true)  
const error = ref(null)  
const tab = ref('posts')  
const avatarMenuOpen = ref(false)  
const avatarLightbox = ref(false)  
const avatarLightboxScale = ref(1)  
const avatarCropSrc = ref(null)  
const myCollections = ref([])  
const tabState = reactive({ posts: { list: [], next: null }, reposts: { list: [], next: null }, liked: { list: [], next: null } })
const tabLoaded = reactive({ posts: false, reposts: false, liked: false })  
const tabLoading = ref(false)  
const returnedPosts = ref([])  
const returnedLoading = ref(false)  
const listModal = ref(null)  
const listUsers = ref([])  
const listLoading = ref(false)  
const listError = ref(null)
const sentinel = ref(null)  
const reportDialog = ref(false)  
const reportSent = ref(false)  
const reportReason = ref('')  
const reportDetail = ref('')  
const reportSending = ref(false)  
let observer = null  
const isMe = computed(() => auth.user && user.value && auth.user.username === user.value.username)  
const emptyIcons = { posts: '📷', reposts: '🔁', liked: '♥' }  
const emptyMessages = { posts: 'Постов пока нет', reposts: 'Репостов пока нет', liked: 'Понравившихся нет' }
const TAB_ENDPOINTS = {  
  posts: (u) => `/api/users/${u}/posts/`,
  reposts: (u) => `/api/users/${u}/reposts/`,
  liked: (u) => `/api/users/${u}/liked/`,
}
function formatDate(s) { return new Date(s).toLocaleString('ru-RU') }
watch(sentinel, (el) => {  
  if (observer) { observer.disconnect(); observer = null }
  if (el) {
    observer = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && !tabLoading.value) loadMore()
    }, { rootMargin: '300px' })
    observer.observe(el)
  }
})
onUnmounted(() => { if (observer) observer.disconnect() })  
async function loadTabPosts() {  
  const t = tab.value
  if (!['posts', 'reposts', 'liked'].includes(t) || tabLoaded[t]) return  
  tabLoading.value = true
  try {
    const data = await api(TAB_ENDPOINTS[t](user.value.username))  
    tabState[t].list = data.results
    tabState[t].next = data.next  
    tabLoaded[t] = true  
  } finally { tabLoading.value = false }
}
async function loadMore() {  
  const t = tab.value
  if (!tabState[t].next || tabLoading.value) return
  tabLoading.value = true
  try {
    const url = new URL(tabState[t].next)
    const data = await api(url.pathname + url.search)
    tabState[t].list.push(...data.results)  
    tabState[t].next = data.next
  } finally { tabLoading.value = false }
}
async function loadReturnedPosts() {  
  returnedLoading.value = true
  try { returnedPosts.value = await api(`/api/users/${user.value.username}/returned/`) }
  catch { toastError('Не удалось загрузить возвращённые посты') }
  finally { returnedLoading.value = false }
}
function selectTab(t) {  
  tab.value = t
  profileTabMemory[route.params.username] = t  
}
async function openList(type) {  
  listModal.value = type  
  listLoading.value = true
  listError.value = null
  listUsers.value = []
  try {
    const ep = type === 'followers'
      ? `/api/users/${user.value.username}/followers/`
      : `/api/users/${user.value.username}/following/`
    listUsers.value = await api(ep)
  } catch { listError.value = 'Не удалось загрузить список' }
  finally { listLoading.value = false }
}
async function deletePost(idOrPost) {  
  const id = typeof idOrPost === 'object' ? idOrPost.id : idOrPost  
  if (!(await showConfirm('Удалить этот пост?'))) return
  try {
    await api(`/api/posts/${id}/`, { method: 'DELETE' })
    for (const t of ['posts', 'reposts', 'liked']) {  
      tabState[t].list = tabState[t].list.filter(p => p.id !== id)
    }
    toastSuccess('Пост удалён')
  } catch { toastError('Не удалось удалить') }
}
function clickAvatar() {  
  if (user.value?.avatar) {
    avatarMenuOpen.value = false
    avatarLightboxScale.value = 1  
    avatarLightbox.value = true
  }
}
function onAvatarWheel(e) {  
  const delta = e.deltaY > 0 ? -0.15 : 0.15  
  avatarLightboxScale.value = Math.max(0.5, Math.min(4, avatarLightboxScale.value + delta))  
}
async function downloadImage(url) {  
  try {
    const res = await fetch(url)  
    const blob = await res.blob()
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = url.split('/').pop() || 'image'  
    a.click()  
    URL.revokeObjectURL(a.href)  
  } catch {  }
}
async function changeCover(e) {  
  const file = e.target.files[0]
  if (!file) return
  const form = new FormData()
  form.append('cover', file)
  try {
    const data = await api('/api/me/', { method: 'PATCH', body: form })  
    auth.setUser(data)  
    user.value.cover = data.cover  
    toastSuccess('Обложка обновлена')
  } catch { toastError('Не удалось обновить обложку') }
}
function changeAvatarWithCrop(e) {  
  const raw = e.target.files[0]
  e.target.value = ''  
  if (!raw) return
  avatarLightbox.value = false  
  avatarMenuOpen.value = false
  const url = URL.createObjectURL(raw)  
  avatarCropSrc.value = url  
}
async function onAvatarCropConfirm(croppedFile) {  
  if (avatarCropSrc.value) URL.revokeObjectURL(avatarCropSrc.value)  
  avatarCropSrc.value = null  
  const form = new FormData()
  form.append('avatar', croppedFile)
  try {
    const data = await api('/api/me/', { method: 'PATCH', body: form })
    auth.setUser(data)  
    user.value.avatar = data.avatar  
    toastSuccess('Аватар обновлён')
  } catch { toastError('Не удалось обновить аватар') }
}
function changeAvatar(e) { changeAvatarWithCrop(e) }  
async function toggleFollow() {  
  try {
    const data = await api(`/api/users/${user.value.username}/follow/`, { method: 'POST' })
    user.value.is_following = data.following  
    user.value.has_pending_request = data.requested  
    user.value.followers_count = data.followers_count  
  } catch (e) {
    toastError(e.detail || 'Ошибка')
  }
}
async function toggleBlock() {  
  try {
    const data = await api(`/api/users/${user.value.username}/block/`, { method: 'POST' })
    user.value.is_blocked = data.blocked  
    if (data.blocked) {
      user.value.is_following = false  
      user.value.has_pending_request = false
      toastSuccess('Пользователь заблокирован')
    } else {
      toastSuccess('Пользователь разблокирован')
    }
  } catch { toastError('Ошибка') }
}
async function submitUserReport() {  
  if (!reportReason.value || reportSending.value) return
  reportSending.value = true
  try {
    await api(`/api/users/${user.value.username}/report/`, {
      method: 'POST',
      body: JSON.stringify({ reason: reportReason.value, detail: reportDetail.value }),
    })
    reportSent.value = true  
  } catch (e) {
    toastError(e.detail || 'Ошибка при отправке жалобы')
  } finally { reportSending.value = false }
}
watch(tab, (t) => {  
  if (!user.value) return
  if (t === 'returned') loadReturnedPosts()  
  else loadTabPosts()  
})
async function load() {  
  loading.value = true
  error.value = null
  returnedPosts.value = []
  Object.keys(tabState).forEach(k => { tabState[k].list = []; tabState[k].next = null })  
  Object.keys(tabLoaded).forEach(k => { tabLoaded[k] = false })  
  try {
    user.value = await api(`/api/users/${route.params.username}/`)  
    tab.value = profileTabMemory[route.params.username] || 'posts'  
    await loadTabPosts()  
    if (auth.isAuthenticated()) myCollections.value = await api('/api/collections/')
    if (auth.user && auth.user.username === route.params.username) {
      await loadReturnedPosts()  
    }
  } catch { error.value = 'Не удалось загрузить профиль' }
  finally { loading.value = false }
}
watch(() => route.params.username, () => {  
  router.replace({ query: {} })  
  load()
}, { immediate: true })  
</script>