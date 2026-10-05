<template>
  <p v-if="loading">Загрузка...</p>
  <p v-else-if="error" class="error">{{ error }}</p>
  <div v-else>
    <div class="post-detail-layout">  
      <div class="post-media-col">
        <template v-if="post.media_type === 'video'">
          <video :src="post.video" class="post-img post-video" controls preload="metadata"></video>
        </template>
        <template v-else-if="allImages.length > 1">
          <div class="carousel">
            <button class="carousel-btn carousel-prev" @click.stop="prevSlide" :disabled="slideIndex === 0">‹</button>
            <img :src="allImages[slideIndex]" alt="" class="post-img" loading="lazy"
              @click="openLightbox(allImages[slideIndex])">  
            <button class="carousel-btn carousel-next" @click.stop="nextSlide" :disabled="slideIndex === allImages.length - 1">›</button>
            <div class="carousel-dots">
              <span v-for="(_, i) in allImages" :key="i" class="carousel-dot" :class="{ active: i === slideIndex }" @click.stop="slideIndex = i"></span>
            </div>
          </div>
        </template>
        <template v-else-if="post.image">
          <img :src="post.image" alt="" class="post-img" loading="lazy"
            @click="openLightbox(post.image)">
        </template>
        <div v-if="post.quoted_post" class="quoted-post-card" @click="$router.push('/post/' + post.quoted_post.id)">
          <div class="quoted-post-header">
            <span class="quoted-label">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 014-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 01-4 4H3"/></svg>
              Репост
            </span>
            <router-link :to="'/user/' + post.quoted_post.author" class="quoted-author" @click.stop>
              @{{ post.quoted_post.author }}  
            </router-link>
          </div>
          <img v-if="post.quoted_post.image" :src="post.quoted_post.image" class="quoted-post-img" alt="" loading="lazy">
          <video v-else-if="post.quoted_post.video" :src="post.quoted_post.video" class="quoted-post-img" muted preload="metadata"></video>
          <p v-if="post.quoted_post.caption" class="quoted-post-caption">{{ post.quoted_post.caption }}</p>
        </div>
        <div v-if="editing" class="edit-caption-form">
          <textarea v-model="editCaption" rows="3" placeholder="Подпись..."></textarea>
          <div class="tag-chips-wrap">  
            <span v-for="(tag, i) in editTags" :key="i" class="tag-edit-chip">
              #{{ tag }}<button type="button" @click="editTags.splice(i, 1)">×</button>
            </span>
            <input
              v-model="editTagInput"
              type="text"
              placeholder="Добавить тег..."
              class="tag-inline-input"
              @keydown.enter.prevent="addEditTag"  
              @keydown.space.prevent="addEditTag"  
              @keydown.backspace="onTagBackspace"  
            >
          </div>
          <div class="edit-caption-actions">
            <button class="btn" :disabled="savingCaption" @click="saveCaption">
              {{ savingCaption ? 'Сохраняю...' : 'Сохранить' }}
            </button>
            <button class="btn-outline" @click="editing = false">Отмена</button>
          </div>
        </div>
        <template v-else>
          <p v-if="captionText" class="caption"><MentionText :text="captionText" /></p>
          <div v-if="post.tags && post.tags.length" class="tags-row">
            <router-link v-for="tag in post.tags" :key="tag.id" :to="'/tag/' + tag.slug" class="tag-chip">
              #{{ tag.name }}
            </router-link>
          </div>
        </template>
        <p class="author">
          <router-link :to="'/user/' + post.author">@{{ post.author }}</router-link>
          · {{ formatDate(post.created_at) }}
          <button v-if="isMyPost && !editing" class="link-btn" @click="startEdit">Изменить</button>
          <button v-if="isMyPost" class="link-btn link-btn-danger" @click="handleDelete">Удалить</button>
        </p>
        <div class="post-actions">
          <button v-if="auth.isAuthenticated()" class="like-btn" @click="toggleLike">
            {{ post.is_liked ? '♥' : '♡' }} {{ post.likes_count }}
          </button>
          <span v-else class="stats">♥ {{ post.likes_count }}</span>
          <button v-if="auth.isAuthenticated()" class="btn btn-outline" @click="openRepostMenu">
            {{ post.is_reposted ? '🔁 Репостнуто' : '🔁 Репост' }}
          </button>
          <div class="share-dropdown-wrap" style="position:relative;display:inline-block" @mouseleave="shareMenuOpen = false">
            <button class="btn-outline share-btn" @click="shareMenuOpen = !shareMenuOpen">
              🔗 Поделиться
            </button>
            <div v-if="shareMenuOpen" class="share-dropdown-menu">
              <button @click="share(); shareMenuOpen = false">🔗 Скопировать ссылку</button>
            </div>
          </div>
          <button v-if="auth.isAuthenticated() && !isMyPost" class="btn-outline report-btn" @click="reportDialog = true; reportSent = false; reportReason = ''; reportComment = ''">
            Пожаловаться
          </button>
        </div>
        <div v-if="auth.isAuthenticated()" class="save-form">
          <template v-if="myCollections.length">  
            <select v-model="selectedCollection">
              <option :value="null" disabled>Сохранить в коллекцию...</option>
              <option v-for="c in myCollections" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
            <button class="btn" :disabled="!selectedCollection" @click="saveToCollection">Сохранить</button>
          </template>
          <router-link v-else to="/collections">Создай коллекцию, чтобы сохранять посты</router-link>
        </div>
      </div>
      <div class="post-comments-col">
        <h2>Комментарии</h2>
        <template v-if="auth.isAuthenticated()">
          <template v-if="isMyPost || canComment">
            <div class="comment-form">
              <textarea v-model="newComment" rows="2" placeholder="Напишите комментарий..."></textarea>
              <button class="btn" @click="addComment">Отправить</button>
            </div>
          </template>
          <p v-else class="muted restriction-notice">Автор ограничил возможность комментирования.</p>
        </template>
        <p v-else><router-link to="/login">Войдите</router-link>, чтобы комментировать.</p>
        <p v-if="commentsLoading && !comments.length" class="muted">Загрузка...</p>
        <CommentItem
          v-for="c in comments"
          :key="c.id"
          :comment="c"
          :post-id="post.id"
          :post-author="post.author"
          @added="loadComments(true)"  
          @deleted="loadComments(true)"
        />
        <p v-if="!commentsLoading && !comments.length" class="muted">Пока нет комментариев.</p>
        <button v-if="commentsNext" class="btn-outline load-more-btn" :disabled="commentsLoading" @click="loadMoreComments">
          {{ commentsLoading ? 'Загрузка...' : 'Ещё комментарии' }}
        </button>
      </div>
    </div>
    <section v-if="similarPosts.length" class="similar-posts">
      <h2>Похожие посты</h2>
      <div class="masonry">
        <router-link v-for="p in similarPosts" :key="p.id" :to="'/post/' + p.id" class="card">
          <img v-if="p.image" :src="p.image" alt="" loading="lazy">
          <div v-else class="similar-video-placeholder">▶</div>
          <p v-if="p.caption" class="card-caption">{{ p.caption }}</p>
          <span class="author">@{{ p.author }}</span>
        </router-link>
      </div>
    </section>
  </div>
  <div v-if="repostMenuOpen" class="modal-overlay" @click.self="repostMenuOpen = false">
    <div class="modal" style="max-width:400px">
      <div class="modal-head">
        <h2>Репост</h2>
        <button class="modal-close" @click="repostMenuOpen = false">✕</button>
      </div>
      <div style="display:flex;flex-direction:column;gap:10px;padding:8px 0">
        <button class="btn btn-outline" @click="doSimpleRepost">
          {{ post && post.is_reposted ? '🔁 Отменить репост' : '🔁 Быстрый репост' }}
        </button>
        <button class="btn" @click="repostMenuOpen = false; quoteDialog = true; quoteCaption = ''">
          💬 Репост с комментарием  
        </button>
      </div>
    </div>
  </div>
  <div v-if="quoteDialog" class="modal-overlay" @click.self="quoteDialog = false">
    <div class="modal" style="max-width:440px">
      <div class="modal-head">
        <h2>Репост с комментарием</h2>
        <button class="modal-close" @click="quoteDialog = false">✕</button>
      </div>
      <textarea v-model="quoteCaption" rows="4" placeholder="Добавьте комментарий к репосту..." style="width:100%;margin-bottom:12px;resize:vertical"></textarea>
      <div v-if="post" class="quoted-post-card" style="cursor:default;margin-bottom:16px">
        <div class="quoted-post-header">
          <router-link :to="'/user/' + post.author" class="quoted-author" @click.stop>@{{ post.author }}</router-link>
        </div>
        <img v-if="post.image" :src="post.image" class="quoted-post-img" alt="">
        <p v-if="post.caption" class="quoted-post-caption">{{ post.caption }}</p>
      </div>
      <div style="display:flex;gap:10px">
        <button class="btn" :disabled="!quoteCaption.trim() || quoting" @click="submitQuoteRepost">
          {{ quoting ? '...' : 'Опубликовать' }}
        </button>
        <button class="btn-outline" @click="quoteDialog = false">Отмена</button>
      </div>
    </div>
  </div>
  <div v-if="reportDialog" class="modal-overlay" @click.self="reportDialog = false">
    <div class="modal" style="max-width:420px">
      <div class="modal-head">
        <h2>Пожаловаться на пост</h2>
        <button class="modal-close" @click="reportDialog = false">✕</button>
      </div>
      <div v-if="reportSent" style="padding:16px 0;text-align:center">
        <p style="font-size:18px">✓</p>
        <p>Жалоба отправлена. Мы рассмотрим её в ближайшее время.</p>
      </div>
      <template v-else>
        <label style="display:block;margin-bottom:8px;font-weight:600">Причина</label>
        <select v-model="reportReason" style="width:100%;margin-bottom:12px">
          <option value="" disabled>Выберите причину...</option>
          <option value="spam">Спам</option>
          <option value="inappropriate">Неприемлемый контент</option>
          <option value="copyright">Нарушение авторских прав</option>
          <option value="harassment">Оскорбление или травля</option>
          <option value="other">Другое</option>
        </select>
        <label style="display:block;margin-bottom:8px;font-weight:600">Комментарий <span style="font-weight:400;color:var(--muted)">(необязательно)</span></label>
        <textarea v-model="reportComment" rows="3" placeholder="Подробности..." style="width:100%;resize:vertical"></textarea>
        <div style="display:flex;gap:10px;margin-top:16px">
          <button class="btn btn-danger" :disabled="!reportReason || reporting" @click="submitReport">
            {{ reporting ? '...' : 'Отправить' }}
          </button>
          <button class="btn-outline" @click="reportDialog = false">Отмена</button>
        </div>
      </template>
    </div>
  </div>
  <Teleport to="body">
    <div v-if="lightboxOpen" class="lightbox"
      :style="{ cursor: lightboxScale > 1 ? (dragging ? 'grabbing' : 'grab') : 'default' }"
      @click="closeLightbox"
      @wheel.prevent="onLightboxWheel"  
      @mousedown.prevent="onLightboxMousedown"  
      @mousemove="onLightboxMousemove"  
      @mouseup="dragging = false"
      @mouseleave="dragging = false">  
      <img :src="lightboxImg" alt=""
        :style="{ transform: `translate(${lightboxPanX}px, ${lightboxPanY}px) scale(${lightboxScale})`, transition: dragging ? 'none' : 'transform 0.1s' }"
        @click.stop>  
      <button class="lightbox-close" @click.stop="closeLightbox">✕</button>
      <div class="lightbox-menu" @click.stop>
        <button class="lightbox-dots" @click.stop="lightboxMenuOpen = !lightboxMenuOpen">⋯</button>
        <div v-if="lightboxMenuOpen" class="lightbox-dropdown">
          <a :href="lightboxImg" class="lightbox-option" @click.prevent="downloadImage(lightboxImg)">Скачать</a>
        </div>
      </div>
    </div>
  </Teleport>
</template>
<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'
import { auth } from '../auth'
import { showConfirm } from '../confirm'
import { toastSuccess, toastError } from '../toast'
import CommentItem from '../components/CommentItem.vue'
import MentionText from '../components/MentionText.vue'
const route = useRoute()
const router = useRouter()
const post = ref(null)  
const comments = ref([])  
const commentsNext = ref(null)  
const commentsLoading = ref(false)
const newComment = ref('')  
const loading = ref(true)
const error = ref(null)
const myCollections = ref([])  
const selectedCollection = ref(null)  
const editing = ref(false)  
const editCaption = ref('')  
const editTags = ref([])  
const editTagInput = ref('')  
const savingCaption = ref(false)
const lightboxOpen = ref(false)  
const lightboxMenuOpen = ref(false)  
const lightboxScale = ref(1)  
const lightboxImg = ref(null)  
const lightboxPanX = ref(0)  
const lightboxPanY = ref(0)  
const dragging = ref(false)  
const slideIndex = ref(0)  
const similarPosts = ref([])  
const copied = ref(false)  
const reportDialog = ref(false)
const reportReason = ref('')
const reportComment = ref('')
const reporting = ref(false)
const reportSent = ref(false)
const repostMenuOpen = ref(false)  
const quoteDialog = ref(false)  
const quoteCaption = ref('')  
const quoting = ref(false)  
const shareMenuOpen = ref(false)  
const authorProfile = ref(null)  
let dragStart = { x: 0, y: 0, px: 0, py: 0 }  
const isMyPost = computed(() => auth.user && post.value && auth.user.username === post.value.author)
const canComment = computed(() => {  
  if (!authorProfile.value) return true  
  const cp = authorProfile.value.comment_privacy
  if (!cp || cp === 'all') return true  
  if (cp === 'none') return false  
  if (cp === 'following') return authorProfile.value.is_following  
  return true
})
const allImages = computed(() => {  
  if (!post.value || !post.value.image) return []
  const extras = (post.value.extra_images || []).map(i => i.image_url)  
  return [post.value.image, ...extras]  
})
const captionText = computed(() => {  
  if (!post.value?.caption) return ''
  if (!post.value.tags?.length) return post.value.caption  
  let text = post.value.caption
  for (const tag of post.value.tags) {
    text = text.replace(new RegExp('#' + tag.name + '\\b', 'gi'), '')  
  }
  return text.replace(/\s+/g, ' ').trim()  
})
function formatDate(s) { return new Date(s).toLocaleString('ru-RU') }
function prevSlide() { if (slideIndex.value > 0) slideIndex.value-- }  
function nextSlide() { if (slideIndex.value < allImages.value.length - 1) slideIndex.value++ }  
function onKeydown(e) {  
  if (e.key === 'Escape') closeLightbox()
  if (e.key === 'ArrowLeft') prevSlide()  
  if (e.key === 'ArrowRight') nextSlide()
}
function openLightbox(img) {  
  lightboxImg.value = img
  lightboxScale.value = 1  
  lightboxPanX.value = 0  
  lightboxPanY.value = 0
  lightboxMenuOpen.value = false
  dragging.value = false
  lightboxOpen.value = true
}
function closeLightbox() {
  lightboxOpen.value = false
  lightboxMenuOpen.value = false
  dragging.value = false
}
function onLightboxWheel(e) {  
  const delta = e.deltaY > 0 ? -0.15 : 0.15  
  lightboxScale.value = Math.max(0.5, Math.min(4, lightboxScale.value + delta))
  if (lightboxScale.value <= 1) { lightboxPanX.value = 0; lightboxPanY.value = 0 }  
}
function onLightboxMousedown(e) {  
  if (lightboxScale.value <= 1) return  
  dragging.value = true
  dragStart = { x: e.clientX, y: e.clientY, px: lightboxPanX.value, py: lightboxPanY.value }
}
function onLightboxMousemove(e) {  
  if (!dragging.value) return
  lightboxPanX.value = dragStart.px + (e.clientX - dragStart.x)  
  lightboxPanY.value = dragStart.py + (e.clientY - dragStart.y)
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
onMounted(() => window.addEventListener('keydown', onKeydown))  
onUnmounted(() => window.removeEventListener('keydown', onKeydown))  
function startEdit() {  
  editCaption.value = post.value.caption  
  editTags.value = (post.value.tags || []).map(t => t.name)  
  editTagInput.value = ''
  editing.value = true
}
function addEditTag() {  
  const tag = editTagInput.value.trim().replace(/^#/, '').toLowerCase().replace(/\s+/g, '')
  if (tag && !editTags.value.includes(tag)) editTags.value.push(tag)  
  editTagInput.value = ''  
}
function onTagBackspace() {  
  if (!editTagInput.value && editTags.value.length) editTags.value.pop()
}
async function saveCaption() {  
  savingCaption.value = true
  try {
    const updated = await api('/api/posts/' + post.value.id + '/', {
      method: 'PATCH',
      body: JSON.stringify({ caption: editCaption.value, tags: editTags.value }),
    })
    post.value.caption = updated.caption
    post.value.tags = updated.tags
    editing.value = false
    toastSuccess('Подпись обновлена')
  } catch {
    toastError('Не удалось сохранить')
  } finally {
    savingCaption.value = false
  }
}
async function handleDelete() {  
  if (!(await showConfirm('Удалить этот пост?'))) return
  try {
    await api(`/api/posts/${post.value.id}/`, { method: 'DELETE' })
    toastSuccess('Пост удалён')
    router.push('/')  
  } catch {
    toastError('Не удалось удалить пост')
  }
}
async function loadComments(reset = true) {  
  if (reset) { comments.value = []; commentsNext.value = null }  
  commentsLoading.value = true
  try {
    const data = await api('/api/posts/' + route.params.id + '/comments/')
    comments.value = data.results ?? data  
    commentsNext.value = data.next ?? null
  } finally { commentsLoading.value = false }
}
async function loadMoreComments() {  
  if (!commentsNext.value || commentsLoading.value) return
  commentsLoading.value = true
  try {
    const url = new URL(commentsNext.value)
    const data = await api(url.pathname + url.search)
    comments.value.push(...(data.results ?? data))
    commentsNext.value = data.next ?? null
  } finally { commentsLoading.value = false }
}
async function toggleLike() {
  const data = await api('/api/posts/' + post.value.id + '/like/', { method: 'POST' })
  post.value.is_liked = data.liked
  post.value.likes_count = data.likes_count
}
function openRepostMenu() { repostMenuOpen.value = true }  
async function doSimpleRepost() {  
  repostMenuOpen.value = false
  try {
    const data = await api('/api/posts/' + post.value.id + '/repost/', { method: 'POST' })
    post.value.is_reposted = data.reposted
    post.value.reposts_count = data.reposts_count
    toastSuccess(data.reposted ? 'Репостнуто' : 'Репост отменён')
  } catch { toastError('Ошибка') }
}
async function submitQuoteRepost() {  
  if (!quoteCaption.value.trim() || quoting.value) return
  quoting.value = true
  try {
    await api(`/api/posts/${post.value.id}/quote/`, {  
      method: 'POST',
      body: JSON.stringify({ caption: quoteCaption.value.trim() }),
    })
    quoteDialog.value = false
    toastSuccess('Репост опубликован')
  } catch (e) {
    toastError(e.detail || 'Ошибка')
  } finally { quoting.value = false }
}
async function saveToCollection() {
  await api('/api/collections/' + selectedCollection.value + '/add/', {
    method: 'POST',
    body: JSON.stringify({ post: post.value.id }),
  })
  toastSuccess('Сохранено в коллекцию')
  selectedCollection.value = null
}
async function share() {  
  try {
    await navigator.clipboard.writeText(window.location.href)  
    copied.value = true
    toastSuccess('Ссылка скопирована')
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    toastError('Не удалось скопировать ссылку')
  }
}
async function submitReport() {  
  if (!reportReason.value || reporting.value) return
  reporting.value = true
  try {
    await api(`/api/posts/${post.value.id}/report/`, {  
      method: 'POST',
      body: JSON.stringify({ reason: reportReason.value, comment: reportComment.value }),
    })
    reportSent.value = true
  } catch (e) {
    toastError(e.detail || 'Ошибка при отправке жалобы')
  } finally { reporting.value = false }
}
async function addComment() {  
  if (!newComment.value.trim()) return
  await api('/api/posts/' + post.value.id + '/comments/', {
    method: 'POST',
    body: JSON.stringify({ text: newComment.value }),
  })
  newComment.value = ''
  loadComments()  
}
onMounted(async () => {
  try {
    post.value = await api('/api/posts/' + route.params.id + '/')  
    await loadComments()  
    const [cols, sim, authorData] = await Promise.all([  
      auth.isAuthenticated() ? api('/api/collections/') : Promise.resolve([]),
      api('/api/posts/' + route.params.id + '/similar/'),  
      api('/api/users/' + post.value.author + '/').catch(() => null),  
    ])
    myCollections.value = cols
    similarPosts.value = sim
    authorProfile.value = authorData  
  } catch {
    error.value = 'Не удалось загрузить пост'
  } finally {
    loading.value = false
  }
})
</script>