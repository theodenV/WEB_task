<template>
  <div class="comment">  
    <p class="comment-author">  
      <router-link :to="'/user/' + comment.author">@{{ comment.author }}</router-link>  
      <span class="comment-date">{{ formatDate(comment.created_at) }}</span>  
      <button v-if="canEdit && !editing" class="comment-edit-btn" title="Изменить" @click="startEdit">✎</button>  
      <button v-if="canDelete && !editing" class="comment-del-btn" title="Удалить" @click="del">✕</button>  
    </p>
    <div v-if="editing" class="comment-edit-form">  
      <textarea v-model="editText" rows="2"></textarea>  
      <div class="comment-edit-actions">
        <button class="btn" @click="saveEdit">Сохранить</button>  
        <button class="btn-outline" @click="editing = false">Отмена</button>  
      </div>
    </div>
    <p v-else class="comment-text"><MentionText :text="localText" /></p>  
    <div class="comment-meta-row">  
      <button v-if="auth.isAuthenticated()" class="comment-like-btn" :class="{ liked: localLiked }" @click="toggleLike">  
        {{ localLiked ? '♥' : '♡' }} {{ localLikesCount || '' }}  
      </button>
      <button v-if="auth.isAuthenticated() && !editing" class="reply-btn" @click="startReply">Ответить</button>  
      <button v-if="auth.isAuthenticated() && !canEdit" class="comment-report-btn" @click="reportOpen = true" title="Пожаловаться">⚑</button>  
    </div>
    <div v-if="reportOpen" class="modal-overlay" @click.self="reportOpen = false">  
      <div class="modal" style="max-width:380px">
        <div class="modal-head">
          <h2>Жалоба на комментарий</h2>
          <button class="modal-close" @click="reportOpen = false">✕</button>  
        </div>
        <div v-if="reportSent" style="text-align:center;padding:16px 0">  
          <p style="font-size:18px">✓</p><p>Жалоба отправлена</p>
        </div>
        <template v-else>  
          <select v-model="reportReason" style="width:100%;margin-bottom:12px">  
            <option value="" disabled>Причина...</option>  
            <option value="spam">Спам</option>
            <option value="inappropriate">Неприемлемый контент</option>
            <option value="harassment">Оскорбление или травля</option>
            <option value="other">Другое</option>
          </select>
          <div style="display:flex;gap:10px">
            <button class="btn btn-danger" :disabled="!reportReason || reportSending" @click="submitReport">  
              {{ reportSending ? '...' : 'Отправить' }}  
            </button>
            <button class="btn-outline" @click="reportOpen = false">Отмена</button>
          </div>
        </template>
      </div>
    </div>
    <div v-if="showReply" class="reply-form">  
      <textarea v-model="replyText" rows="2" :placeholder="'Ответ для @' + comment.author + '...'"></textarea>  
      <div class="reply-form-actions">
        <button class="btn" @click="sendReply">Отправить</button>
        <button class="btn-outline" @click="showReply = false">Отмена</button>
      </div>
    </div>
    <div v-if="comment.replies && comment.replies.length" class="replies">  
      <CommentItem  
        v-for="reply in comment.replies"  
        :key="reply.id"  
        :comment="reply"  
        :post-id="postId"  
        :post-author="postAuthor"  
        @added="$emit('added')"  
        @deleted="$emit('deleted')"  
      />
    </div>
  </div>
</template>
<script setup>
import { ref, computed, watch } from 'vue'  
import { api } from '../api'  
import { auth } from '../auth'  
import { toastError } from '../toast'  
import MentionText from './MentionText.vue'  
const props = defineProps(['comment', 'postId', 'postAuthor'])  
const emit = defineEmits(['added', 'deleted'])  
const showReply = ref(false)  
const replyText = ref('')  
const editing = ref(false)  
const editText = ref('')  
const localText = ref(props.comment.text)  
const localLiked = ref(props.comment.is_liked || false)  
const localLikesCount = ref(props.comment.likes_count || 0)  
const reportOpen = ref(false)  
const reportSent = ref(false)  
const reportReason = ref('')  
const reportSending = ref(false)  
watch(() => props.comment.text, v => { localText.value = v })  
watch(() => props.comment.is_liked, v => { localLiked.value = v })
watch(() => props.comment.likes_count, v => { localLikesCount.value = v })
const canEdit = computed(() => auth.user && auth.user.username === props.comment.author)  
const canDelete = computed(() =>  
  auth.user && (auth.user.username === props.comment.author || auth.user.username === props.postAuthor)
)
function formatDate(s) { return new Date(s).toLocaleString('ru-RU') }  
function startEdit() {  
  editText.value = localText.value  
  editing.value = true  
}
async function saveEdit() {  
  if (!editText.value.trim()) return  
  try {
    await api(`/api/posts/${props.postId}/comments/${props.comment.id}/`, {  
      method: 'PATCH',
      body: JSON.stringify({ text: editText.value }),  
    })
    localText.value = editText.value  
    editing.value = false  
  } catch {
    toastError('Не удалось сохранить комментарий')  
  }
}
async function toggleLike() {  
  try {
    const data = await api(`/api/posts/${props.postId}/comments/${props.comment.id}/like/`, { method: 'POST' })
    localLiked.value = data.liked  
    localLikesCount.value = data.likes_count  
  } catch {  }
}
function startReply() {  
  if (!showReply.value) replyText.value = `@${props.comment.author} `  
  showReply.value = !showReply.value  
}
async function sendReply() {  
  if (!replyText.value.trim()) return  
  await api('/api/posts/' + props.postId + '/comments/', {  
    method: 'POST',
    body: JSON.stringify({ text: replyText.value, parent: props.comment.id }),  
  })
  replyText.value = ''  
  showReply.value = false  
  emit('added')  
}
async function del() {  
  await api(`/api/posts/${props.postId}/comments/${props.comment.id}/`, { method: 'DELETE' })
  emit('deleted')  
}
async function submitReport() {  
  if (!reportReason.value || reportSending.value) return  
  reportSending.value = true  
  try {
    await api(`/api/posts/${props.postId}/comments/${props.comment.id}/report/`, {
      method: 'POST',
      body: JSON.stringify({ reason: reportReason.value }),  
    })
    reportSent.value = true  
  } catch (e) {
    toastError(e.detail || 'Ошибка')  
  } finally { reportSending.value = false }  
}
</script>