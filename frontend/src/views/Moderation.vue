<template>
  <div>
    <div class="tabs" style="margin-bottom:20px">
      <button :class="{ active: tab === 'queue' }" @click="switchTab('queue')">
        На модерации <span v-if="queue.length" class="mod-badge">{{ queue.length }}</span>
      </button>
      <button :class="{ active: tab === 'post_reports' }" @click="switchTab('post_reports')">
        Жалобы на посты <span v-if="reports.length" class="mod-badge">{{ reports.length }}</span>
      </button>
      <button :class="{ active: tab === 'comment_reports' }" @click="switchTab('comment_reports')">
        Жалобы на комментарии <span v-if="commentReports.length" class="mod-badge">{{ commentReports.length }}</span>
      </button>
      <button :class="{ active: tab === 'user_reports' }" @click="switchTab('user_reports')">
        Жалобы на пользователей <span v-if="userReports.length" class="mod-badge">{{ userReports.length }}</span>
      </button>
      <button :class="{ active: tab === 'users' }" @click="switchTab('users')">Пользователи</button>
    </div>
    <template v-if="tab === 'queue'">
      <p v-if="queueLoading" class="muted">Загрузка...</p>
      <p v-else-if="!queue.length" class="empty-state"><span class="empty-icon">✅</span><span>Нет постов на модерации</span></p>
      <div v-else class="mod-list">
        <div v-for="post in queue" :key="post.id" class="mod-card">
          <img v-if="post.image" :src="post.image" class="mod-img" style="cursor:zoom-in" alt=""
            @click="lightboxImg = post.image; lightboxScale = 1">  
          <video v-else-if="post.video" :src="post.video" class="mod-img" muted controls preload="metadata"></video>
          <div v-else class="mod-img mod-img-placeholder">—</div>
          <div class="mod-info">
            <router-link :to="'/user/' + post.author" class="mod-author">@{{ post.author }}</router-link>
            <p class="mod-caption">{{ post.caption || '—' }}</p>
            <span class="mod-date">{{ formatDate(post.created_at) }}</span>
            <span v-if="post.locked_by && !post.locked_by_me" class="mod-locked">Занят: @{{ post.locked_by }}</span>
          </div>
          <div class="mod-actions">
            <template v-if="!post.locked_by || post.locked_by_me">
              <button class="btn" @click="approve(post)">✓ Принять</button>  
              <button class="btn-outline btn-danger" @click="openRejectDialog(post)">✗ Вернуть</button>  
            </template>
            <span v-else class="muted" style="font-size:12px">Другой модератор</span>
          </div>
        </div>
      </div>
    </template>
    <template v-if="tab === 'post_reports'">
      <p v-if="reportsLoading" class="muted">Загрузка...</p>
      <p v-else-if="!reports.length" class="empty-state"><span class="empty-icon">🏳️</span><span>Нет жалоб на посты</span></p>
      <div v-else class="mod-list">
        <div v-for="r in reports" :key="r.id" class="mod-card">
          <img v-if="r.post_image" :src="r.post_image" class="mod-img" style="cursor:zoom-in" alt=""
            @click="lightboxImg = r.post_image; lightboxScale = 1">
          <div v-else class="mod-img mod-img-placeholder">—</div>
          <div class="mod-info">
            <div class="mod-report-row">
              <router-link :to="'/user/' + r.post_author" class="mod-author">@{{ r.post_author }}</router-link>
              <span class="mod-report-reason">{{ r.reason_display }}</span>  
            </div>
            <p v-if="r.comment" class="mod-caption">«{{ r.comment }}»</p>  
            <span class="muted" style="font-size:12px">от @{{ r.reporter }} · {{ formatDate(r.created_at) }}</span>
          </div>
          <div class="mod-actions">
            <button class="btn btn-danger" @click="resolveReport(r, true)">Удалить пост</button>  
            <button class="btn" @click="resolveReport(r, false)">Принять</button>  
            <button class="btn-outline" @click="dismissReport(r)">Отклонить</button>  
          </div>
        </div>
      </div>
    </template>
    <template v-if="tab === 'comment_reports'">
      <p v-if="commentReportsLoading" class="muted">Загрузка...</p>
      <p v-else-if="!commentReports.length" class="empty-state"><span class="empty-icon">💬</span><span>Нет жалоб на комментарии</span></p>
      <div v-else class="mod-list">
        <div v-for="r in commentReports" :key="r.id" class="mod-card">
          <div class="mod-info" style="flex:1">
            <div class="mod-report-row">
              <router-link :to="'/user/' + r.comment_author" class="mod-author">@{{ r.comment_author }}</router-link>
              <span class="mod-report-reason">{{ r.reason_display }}</span>
            </div>
            <p class="mod-caption">«{{ r.comment_text }}»</p>  
            <router-link :to="'/post/' + r.post_id" class="muted" style="font-size:12px">Перейти к посту →</router-link>
            <span class="muted" style="font-size:12px;display:block">от @{{ r.reporter }} · {{ formatDate(r.created_at) }}</span>
          </div>
          <div class="mod-actions">
            <button class="btn btn-danger" @click="resolveCommentReport(r, true)">Удалить комментарий</button>
            <button class="btn-outline" @click="resolveCommentReport(r, false)">Отклонить</button>
          </div>
        </div>
      </div>
    </template>
    <template v-if="tab === 'user_reports'">
      <p v-if="userReportsLoading" class="muted">Загрузка...</p>
      <p v-else-if="!userReports.length" class="empty-state"><span class="empty-icon">👤</span><span>Нет жалоб на пользователей</span></p>
      <div v-else class="mod-list">
        <div v-for="r in userReports" :key="r.id" class="mod-card">
          <div class="mod-info" style="flex:1">
            <div class="mod-report-row">
              <router-link :to="'/user/' + r.reported_user" class="mod-author">@{{ r.reported_user }}</router-link>
              <span class="mod-report-reason">{{ r.reason_display }}</span>
            </div>
            <p v-if="r.detail" class="mod-caption">«{{ r.detail }}»</p>
            <span class="muted" style="font-size:12px">от @{{ r.reporter }} · {{ formatDate(r.created_at) }}</span>
          </div>
          <div class="mod-actions">
            <button class="btn btn-danger" @click="resolveUserReport(r, 'ban')">Забанить</button>  
            <button class="btn-outline" @click="resolveUserReport(r, 'dismiss')">Отклонить</button>
          </div>
        </div>
      </div>
    </template>
    <template v-if="tab === 'users'">
      <div style="display:flex;gap:10px;margin-bottom:16px">
        <input v-model="userSearch" placeholder="Поиск по имени..." @input="searchUsers" style="flex:1">
      </div>
      <p v-if="usersLoading" class="muted">Загрузка...</p>
      <template v-else>
        <div v-if="staffUsers.length" class="mod-group">
          <div class="mod-group-title">Модераторы</div>
          <div class="mod-list">
            <div v-for="u in staffUsers" :key="u.id" class="mod-card">
              <div class="mod-user-avatar">
                <img v-if="u.avatar" :src="u.avatar" alt="">
                <span v-else>{{ u.username[0].toUpperCase() }}</span>
              </div>
              <div class="mod-info" style="flex:1">
                <router-link :to="'/user/' + u.username" class="mod-author">@{{ u.username }}</router-link>
                <span class="muted" style="font-size:12px;display:block">{{ u.email }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="mod-group">
          <div v-if="staffUsers.length" class="mod-group-title">Пользователи</div>
          <div class="mod-list">
            <div v-for="u in regularUsers" :key="u.id" class="mod-card">
              <div class="mod-user-avatar">
                <img v-if="u.avatar" :src="u.avatar" alt="">
                <span v-else>{{ u.username[0].toUpperCase() }}</span>
              </div>
              <div class="mod-info" style="flex:1">
                <router-link :to="'/user/' + u.username" class="mod-author">@{{ u.username }}</router-link>
                <span class="muted" style="font-size:12px;display:block">{{ u.email }}</span>
                <span v-if="u.is_banned" class="ban-tag">Заблокирован</span>  
              </div>
              <div class="mod-actions">
                <button v-if="!u.is_banned" class="btn btn-danger" @click="openBanDialog(u)">Заблокировать</button>
                <button v-else class="btn-outline" @click="unbanUser(u)">Разблокировать</button>
              </div>
            </div>
          </div>
        </div>
      </template>
    </template>
  </div>
  <div v-if="rejectDialog" class="modal-overlay" @click.self="rejectDialog = null">
    <div class="modal" style="max-width:420px">
      <div class="modal-head">
        <h2>Причина возврата</h2>
        <button class="modal-close" @click="rejectDialog = null">✕</button>
      </div>
      <textarea v-model="rejectReason" rows="4" placeholder="Объясните, что нужно исправить..."
        style="width:100%;resize:vertical"></textarea>
      <div style="display:flex;gap:10px;margin-top:16px">
        <button class="btn btn-danger" :disabled="!rejectReason.trim() || rejecting" @click="confirmReject">
          {{ rejecting ? '...' : 'Вернуть автору' }}
        </button>
        <button class="btn-outline" @click="rejectDialog = null">Отмена</button>
      </div>
    </div>
  </div>
  <div v-if="banDialog" class="modal-overlay" @click.self="banDialog = null">
    <div class="modal" style="max-width:400px">
      <div class="modal-head">
        <h2>Заблокировать @{{ banDialog.username }}</h2>
        <button class="modal-close" @click="banDialog = null">✕</button>
      </div>
      <div class="field-wrap">
        <label>Причина (необязательно)</label>
        <textarea v-model="banReason" rows="2" style="width:100%;resize:vertical"></textarea>
      </div>
      <div style="display:flex;gap:10px;margin-top:12px">
        <button class="btn btn-danger" :disabled="banning" @click="confirmBan">
          {{ banning ? '...' : 'Заблокировать' }}
        </button>
        <button class="btn-outline" @click="banDialog = null">Отмена</button>
      </div>
    </div>
  </div>
  <Teleport to="body">
    <div v-if="lightboxImg" class="lightbox" @click="lightboxImg = null" @wheel.prevent="onWheel">
      <img :src="lightboxImg" alt="" :style="{ transform: `scale(${lightboxScale})`, transition: 'transform 0.1s' }" @click.stop>
      <button class="lightbox-close" @click.stop="lightboxImg = null">✕</button>
    </div>
  </Teleport>
</template>
<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'
import { toastSuccess, toastError } from '../toast'
const route = useRoute()
const router = useRouter()
const tab = computed(() => route.query.tab || 'queue')  
const staffUsers = computed(() => users.value.filter(u => u.is_staff))  
const regularUsers = computed(() => users.value.filter(u => !u.is_staff))  
const queue = ref([])  
const queueLoading = ref(false)
const reports = ref([])  
const reportsLoading = ref(false)
const commentReports = ref([])  
const commentReportsLoading = ref(false)
const userReports = ref([])  
const userReportsLoading = ref(false)
const users = ref([])  
const usersLoading = ref(false)
const userSearch = ref('')  
const rejectDialog = ref(null)  
const rejectReason = ref('')  
const rejecting = ref(false)  
const banDialog = ref(null)  
const banReason = ref('')  
const banning = ref(false)  
const lightboxImg = ref(null)  
const lightboxScale = ref(1)  
const loaded = { queue: false, post_reports: false, comment_reports: false, user_reports: false, users: false }
function formatDate(s) {  
  if (!s) return ''
  return new Date(s).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
}
function onWheel(e) {  
  const delta = e.deltaY > 0 ? -0.15 : 0.15
  lightboxScale.value = Math.max(0.5, Math.min(4, lightboxScale.value + delta))
}
async function loadTab(t) {  
  if (loaded[t]) return  
  if (t === 'queue') await loadQueue()
  else if (t === 'post_reports') await loadReports()
  else if (t === 'comment_reports') await loadCommentReports()
  else if (t === 'user_reports') await loadUserReports()
  else if (t === 'users') await loadUsers()
}
function switchTab(t) {  
  router.replace({ query: { tab: t } })
}
watch(tab, (t) => loadTab(t), { immediate: true })  
async function loadQueue() {  
  queueLoading.value = true
  try { queue.value = await api('/api/posts/moderation/'); loaded.queue = true }
  catch { toastError('Не удалось загрузить очередь') }
  finally { queueLoading.value = false }
}
async function loadReports() {  
  reportsLoading.value = true
  try { reports.value = await api('/api/moderation/reports/'); loaded.post_reports = true }
  catch { toastError('Не удалось загрузить жалобы') }
  finally { reportsLoading.value = false }
}
async function loadCommentReports() {
  commentReportsLoading.value = true
  try { commentReports.value = await api('/api/moderation/comment-reports/'); loaded.comment_reports = true }
  catch { toastError('Ошибка') }
  finally { commentReportsLoading.value = false }
}
async function loadUserReports() {
  userReportsLoading.value = true
  try { userReports.value = await api('/api/admin/user-reports/'); loaded.user_reports = true }
  catch { toastError('Ошибка') }
  finally { userReportsLoading.value = false }
}
async function loadUsers(q = '') {  
  usersLoading.value = true
  try { users.value = await api('/api/admin/users/' + (q ? `?q=${encodeURIComponent(q)}` : '')); loaded.users = true }
  catch { toastError('Ошибка') }
  finally { usersLoading.value = false }
}
let searchTimer = null  
function searchUsers() {  
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => loadUsers(userSearch.value), 300)
}
async function approve(post) {  
  try {
    await api(`/api/posts/${post.id}/moderate/lock/`, { method: 'POST' })  
    await api(`/api/posts/${post.id}/moderate/action/`, { method: 'POST', body: JSON.stringify({ action: 'approve' }) })  
    queue.value = queue.value.filter(p => p.id !== post.id)  
    toastSuccess('Пост одобрен')
  } catch (e) { toastError(e.detail || 'Ошибка'); await loadQueue() }  
}
function openRejectDialog(post) { rejectDialog.value = post; rejectReason.value = '' }  
async function confirmReject() {  
  const post = rejectDialog.value
  if (!post || !rejectReason.value.trim()) return
  rejecting.value = true
  try {
    await api(`/api/posts/${post.id}/moderate/lock/`, { method: 'POST' })
    await api(`/api/posts/${post.id}/moderate/action/`, { method: 'POST', body: JSON.stringify({ action: 'reject', reason: rejectReason.value.trim() }) })
    queue.value = queue.value.filter(p => p.id !== post.id)
    rejectDialog.value = null
    toastSuccess('Пост возвращён автору')
  } catch (e) { toastError(e.detail || 'Ошибка'); await loadQueue() }
  finally { rejecting.value = false }
}
async function resolveReport(report, removePost) {  
  try {
    await api(`/api/moderation/reports/${report.id}/action/`, { method: 'POST', body: JSON.stringify({ action: 'resolve', remove_post: removePost }) })
    reports.value = reports.value.filter(r => r.id !== report.id)
    toastSuccess(removePost ? 'Пост удалён' : 'Жалоба принята')
  } catch { toastError('Ошибка') }
}
async function dismissReport(report) {  
  try {
    await api(`/api/moderation/reports/${report.id}/action/`, { method: 'POST', body: JSON.stringify({ action: 'dismiss' }) })
    reports.value = reports.value.filter(r => r.id !== report.id)
    toastSuccess('Жалоба отклонена')
  } catch { toastError('Ошибка') }
}
async function resolveCommentReport(report, del) {  
  try {
    await api(`/api/moderation/comment-reports/${report.id}/action/`, { method: 'POST', body: JSON.stringify({ action: del ? 'delete' : 'dismiss' }) })
    commentReports.value = commentReports.value.filter(r => r.id !== report.id)
    toastSuccess(del ? 'Комментарий удалён' : 'Жалоба отклонена')
  } catch { toastError('Ошибка') }
}
async function resolveUserReport(report, action) {  
  try {
    await api(`/api/admin/user-reports/${report.id}/action/`, { method: 'POST', body: JSON.stringify({ action }) })
    userReports.value = userReports.value.filter(r => r.id !== report.id)
    toastSuccess(action === 'ban' ? 'Пользователь заблокирован' : 'Жалоба отклонена')
    if (action === 'ban') {
      const u = users.value.find(u => u.username === report.reported_user)  
      if (u) u.is_banned = true  
    }
  } catch { toastError('Ошибка') }
}
function openBanDialog(u) { banDialog.value = u; banReason.value = '' }  
async function confirmBan() {  
  banning.value = true
  try {
    await api(`/api/admin/users/${banDialog.value.username}/ban/`, { method: 'POST', body: JSON.stringify({ reason: banReason.value }) })
    banDialog.value.is_banned = true  
    banDialog.value = null  
    toastSuccess('Пользователь заблокирован')
  } catch (e) { toastError(e.detail || 'Ошибка') }
  finally { banning.value = false }
}
async function unbanUser(u) {  
  try {
    await api(`/api/admin/users/${u.username}/ban/`, { method: 'DELETE' })  
    u.is_banned = false
    toastSuccess('Пользователь разблокирован')
  } catch { toastError('Ошибка') }
}
onMounted(() => {  })
</script>