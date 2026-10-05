<template>
  <Teleport to="body">  
    <div v-if="postId" class="post-modal-overlay" @click.self="close">
      <div class="post-modal" :class="{ loading: loading }">  
        <button class="post-modal-close" @click="close">✕</button>  
        <template v-if="loading">  
          <div class="post-modal-spinner">Загрузка...</div>
        </template>
        <template v-else-if="error">  
          <p class="error" style="padding:32px">{{ error }}</p>
        </template>
        <template v-else-if="post">  
          <div class="post-modal-img-col">  
            <img :src="post.image" :alt="post.caption || ''" class="post-modal-img" @click="lightbox = true">
          </div>
          <div class="post-modal-info-col">  
            <div class="post-modal-author">  
              <router-link :to="'/user/' + post.author" class="post-modal-author-link" @click="close">
                <div class="post-modal-avatar">
                  <img v-if="post.author_avatar" :src="post.author_avatar" alt="">
                  <span v-else>{{ post.author[0].toUpperCase() }}</span>  
                </div>
                <div>
                  <div class="post-modal-username">@{{ post.author }}</div>
                  <div class="post-modal-date">{{ formatDate(post.created_at) }}</div>  
                </div>
              </router-link>
              <div class="post-modal-author-actions">  
                <button v-if="isOwn() && !editing" class="link-btn" @click="startEdit">Изменить</button>
                <button v-if="isOwn()" class="link-btn" style="color:#d6336c" @click="deletePost">Удалить</button>
              </div>
            </div>
            <div v-if="editing" class="edit-caption-form">
              <textarea v-model="editCaption" rows="3"></textarea>  
              <div class="edit-caption-actions">
                <button class="btn" :disabled="savingCaption" @click="saveCaption">{{ savingCaption ? '...' : 'Сохранить' }}</button>
                <button class="btn-outline" @click="editing = false">Отмена</button>
              </div>
            </div>
            <template v-else>  
              <p v-if="post.caption" class="post-modal-caption"><MentionText :text="post.caption" /></p>
              <div v-if="post.tags && post.tags.length" class="tags-row">
                <router-link v-for="tag in post.tags" :key="tag.id" :to="'/tag/' + tag.slug" class="tag-chip" @click="close">
                  #{{ tag.name }}
                </router-link>
              </div>
            </template>
            <div class="post-modal-actions">  
              <button v-if="auth.isAuthenticated()" class="like-btn" @click="toggleLike">
                {{ post.is_liked ? '♥' : '♡' }} {{ post.likes_count }}  
              </button>
              <span v-else class="stats">♥ {{ post.likes_count }}</span>  
              <button v-if="auth.isAuthenticated()" class="btn-outline" @click="repost">
                {{ post.is_reposted ? '🔁 Репостнуто' : '🔁 Репост' }}  
              </button>
              <button class="btn-outline share-btn" @click="share">{{ shared ? '✓' : '🔗' }} Поделиться</button>
            </div>
            <div v-if="auth.isAuthenticated() && myCollections.length" class="save-form">
              <select v-model="selectedCollection">  
                <option :value="null" disabled>Сохранить в коллекцию...</option>  
                <option v-for="c in myCollections" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
              <button class="btn" :disabled="!selectedCollection" @click="saveToCollection">Сохранить</button>
            </div>
            <section class="post-modal-comments">  
              <h3>Комментарии</h3>
              <div v-if="auth.isAuthenticated()" class="comment-form">  
                <textarea v-model="newComment" rows="2" placeholder="Напишите комментарий..."></textarea>
                <button class="btn" @click="addComment">Отправить</button>
              </div>
              <CommentItem
                v-for="c in comments"
                :key="c.id"
                :comment="c"  
                :post-id="post.id"  
                :post-author="post.author"  
                @added="loadComments"  
                @deleted="loadComments"  
              />
              <p v-if="!comments.length" class="muted" style="font-size:13px">Пока нет комментариев.</p>
            </section>
          </div>
        </template>
      </div>
    </div>
    <div v-if="lightbox" class="lightbox" @click="lightbox = false">
      <img :src="post?.image" alt="">  
      <button class="lightbox-close" @click.stop="lightbox = false">✕</button>  
    </div>
  </Teleport>
</template>
<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'  
import { api } from '../api'  
import { auth } from '../auth'  
import { toastSuccess, toastError } from '../toast'  
import { showConfirm } from '../confirm'  
import CommentItem from './CommentItem.vue'  
import MentionText from './MentionText.vue'  
const props = defineProps({ postId: { type: Number, default: null } })  
const emit = defineEmits(['close', 'deleted'])  
const post = ref(null)  
const comments = ref([])  
const loading = ref(false)  
const error = ref(null)  
const myCollections = ref([])  
const selectedCollection = ref(null)  
const editing = ref(false)  
const editCaption = ref('')  
const savingCaption = ref(false)  
const newComment = ref('')  
const lightbox = ref(false)  
const shared = ref(false)  
const isOwn = () => auth.user && post.value && auth.user.username === post.value.author  
function formatDate(s) { return new Date(s).toLocaleString('ru-RU') }  
function close() { emit('close') }  
function onKey(e) {  
  if (e.key === 'Escape') {
    if (lightbox.value) { lightbox.value = false; return }  
    close()  
  }
}
onMounted(() => window.addEventListener('keydown', onKey))  
onUnmounted(() => window.removeEventListener('keydown', onKey))  
watch(() => props.postId, async (id) => {  
  if (!id) { post.value = null; comments.value = []; return }  
  loading.value = true
  error.value = null
  post.value = null  
  try {
    const [p, cols] = await Promise.all([  
      api(`/api/posts/${id}/`),  
      auth.isAuthenticated() ? api('/api/collections/') : Promise.resolve([]),  
    ])
    post.value = p  
    myCollections.value = cols  
    await loadComments()  
  } catch { error.value = 'Не удалось загрузить пост' }
  finally { loading.value = false }
}, { immediate: true })  
async function loadComments() {  
  if (!post.value) return
  comments.value = await api(`/api/posts/${post.value.id}/comments/`)  
}
async function toggleLike() {  
  const data = await api(`/api/posts/${post.value.id}/like/`, { method: 'POST' })  
  post.value.is_liked = data.liked  
  post.value.likes_count = data.likes_count  
}
async function repost() {  
  const data = await api(`/api/posts/${post.value.id}/repost/`, { method: 'POST' })
  post.value.is_reposted = data.reposted
  toastSuccess(data.reposted ? 'Репостнуто' : 'Репост отменён')
}
async function share() {  
  await navigator.clipboard.writeText(`${location.origin}/post/${post.value.id}`)
  shared.value = true  
  toastSuccess('Ссылка скопирована')
  setTimeout(() => { shared.value = false }, 2000)  
}
async function saveToCollection() {  
  await api(`/api/collections/${selectedCollection.value}/add/`, {
    method: 'POST',
    body: JSON.stringify({ post: post.value.id }),
  })
  toastSuccess('Сохранено в коллекцию')
  selectedCollection.value = null  
}
function startEdit() {  
  editCaption.value = post.value.caption  
  editing.value = true
}
async function saveCaption() {  
  savingCaption.value = true
  try {
    const updated = await api(`/api/posts/${post.value.id}/`, {  
      method: 'PATCH',
      body: JSON.stringify({ caption: editCaption.value }),
    })
    post.value.caption = updated.caption  
    post.value.tags = updated.tags  
    editing.value = false
    toastSuccess('Подпись обновлена')
  } catch { toastError('Не удалось сохранить') }
  finally { savingCaption.value = false }
}
async function deletePost() {  
  if (!(await showConfirm('Удалить этот пост?'))) return  
  try {
    await api(`/api/posts/${post.value.id}/`, { method: 'DELETE' })  
    toastSuccess('Пост удалён')
    emit('deleted', post.value.id)  
    close()
  } catch { toastError('Не удалось удалить') }
}
async function addComment() {  
  if (!newComment.value.trim()) return  
  await api(`/api/posts/${post.value.id}/comments/`, {  
    method: 'POST',
    body: JSON.stringify({ text: newComment.value }),
  })
  newComment.value = ''  
  loadComments()  
}
</script>