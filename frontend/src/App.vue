<template>
  <svg v-if="auth.isAuthenticated()" class="bg-waves" aria-hidden="true"
       xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" preserveAspectRatio="none">
    <path fill="hsl(272,12%,80%)" fill-opacity="0.50"
      d="M 0,0 L 100,0 L 100,18
         C 92,26 78,13 64,23
         C 50,33 36,16 22,27
         C 12,34 4,20 0,26 Z"/>
    <path fill="hsl(272,12%,80%)" fill-opacity="0.50"
      d="M 0,40
         C 8,32 22,44 38,37
         C 54,30 68,42 82,36
         C 92,31 98,34 100,38
         L 100,58
         C 98,64 92,67 82,62
         C 68,56 54,68 38,63
         C 22,58 8,70 0,62 Z"/>
    <path fill="hsl(272,12%,80%)" fill-opacity="0.50"
      d="M 0,72
         C 10,64 26,75 44,68
         C 62,61 78,73 96,66
         L 100,65
         L 100,100 L 0,100 Z"/>
  </svg>
  <div v-if="auth.isAuthenticated()" class="app-shell" :class="{ 'panel-open': notifPanelOpen || inboxPanelOpen || createPanelOpen }">
    <div v-if="sidebarOpen" class="sidebar-overlay open" @click="sidebarOpen = false"></div>
    <aside class="sidebar" :class="{ open: sidebarOpen }">
      <router-link to="/" class="side-logo" @click="sidebarOpen = false">P</router-link>
      <nav class="side-nav">
        <router-link to="/" class="side-link" :title="t('Главная')" @click="sidebarOpen = false"><Home :size="24" /></router-link>
        <router-link to="/collections" class="side-link" :title="t('Коллекции')" @click="sidebarOpen = false"><LayoutGrid :size="24" /></router-link>
        <router-link to="/create" class="side-link" :title="t('Создать')" @click="sidebarOpen = false"><Plus :size="24" /></router-link>
        <router-link v-if="auth.user?.is_moderator || auth.user?.is_staff"
          to="/moderation" class="side-link" :title="t('Модерация')" @click="closeAllPanels">
          <ShieldCheck :size="24" />
        </router-link>
        <button class="side-link notif-link" :class="{ 'sp-btn-active': inboxPanelOpen }" :title="t('Сообщения')" @click="toggleInboxPanel">
          <MessageCircle :size="24" />
          <span v-if="chatUnreadTotal > 0" class="notif-badge">{{ chatUnreadTotal > 99 ? '99+' : chatUnreadTotal }}</span>
        </button>
        <button class="side-link notif-link" :class="{ 'sp-btn-active': notifPanelOpen }" :title="t('Уведомления')" @click="toggleNotifPanel">
          <Bell :size="24" />
          <span v-if="unreadCount > 0" class="notif-badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
        </button>
      </nav>
      <div class="side-bottom">
        <button class="side-link" :title="isDark ? 'Светлая тема' : 'Тёмная тема'" @click="handleThemeToggle">
          <Sun v-if="isDark" :size="24" />
          <Moon v-else :size="24" />
        </button>
        <router-link :to="'/user/' + auth.user.username" class="side-link" title="Профиль" @click="sidebarOpen = false"><User :size="24" /></router-link>
        <button class="side-link" title="Выйти" @click="logout"><LogOut :size="24" /></button>
      </div>
    </aside>
    <header class="searchbar">
      <button class="hamburger" @click="sidebarOpen = !sidebarOpen" title="Меню">
        <Menu :size="22" />
      </button>
      <button v-if="canGoBack" class="back-btn searchbar-back" @click="router.go(-1)" title="Назад">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"></polyline></svg>
      </button>
      <div class="search-wrap">
        <Search :size="18" class="search-icon" />
        <input v-model="search" type="text" placeholder="Поиск" @keyup.enter="doSearch">
      </div>
      <router-link :to="'/user/' + auth.user.username" class="search-avatar">
        <img v-if="auth.user.avatar" :src="auth.user.avatar" alt="" loading="lazy">
        <span v-else>{{ auth.user.username[0].toUpperCase() }}</span>
      </router-link>
    </header>
    <main class="main">
      <div class="container">
        <router-view v-slot="{ Component }">
          <keep-alive include="Feed">
            <component :is="Component" :key="$route.fullPath" />
          </keep-alive>
        </router-view>
      </div>
    </main>
    <Teleport to="body">
      <div class="sp-wrap" :class="{ open: createPanelOpen }">
        <div class="sp">
          <CreatePostPanel @close="closeCreatePanel" />
        </div>
      </div>
      <div class="sp-wrap" :class="{ open: notifPanelOpen }">
        <div class="sp">
          <div class="sp-head">
            <h2>{{ t('Уведомления') }}</h2>
            <button class="sp-close" @click="closeNotifPanel">✕</button>
          </div>
          <div class="sp-body">
            <div v-if="notifs.length" class="notif-actions-bar">
              <button class="notif-clear-btn" @click="deleteAllNotifs">{{ t('Очистить все') }}</button>
            </div>
            <p v-if="notifsLoading" class="muted sp-empty">{{ t('Загрузка...') }}</p>
            <p v-else-if="!notifs.length" class="muted sp-empty">{{ t('Уведомлений нет') }}</p>
            <template v-else>
              <div v-for="n in notifs" :key="n.id" class="sp-item" :class="{ unread: !n.is_read }">
                <router-link :to="'/user/' + n.actor" class="sp-avatar" @click="closeNotifPanel">
                  <img v-if="n.actor_avatar" :src="n.actor_avatar" alt="" loading="lazy">
                  <span v-else>{{ n.actor[0].toUpperCase() }}</span>
                </router-link>
                <div class="sp-info">
                  <div class="sp-title">
                    <router-link :to="'/user/' + n.actor" class="sp-actor" @click="closeNotifPanel">@{{ n.actor }}</router-link>
                    {{ typeLabel(n.type) }}
                  </div>
                  <router-link v-if="n.post_id" :to="'/post/' + n.post_id" class="sp-sub" @click="closeNotifPanel">посмотреть пост →</router-link>
                </div>
                <div class="sp-item-end">
                  <span class="sp-time">{{ formatTime(n.created_at) }}</span>
                  <button class="notif-del-btn" @click.stop="deleteNotif(n.id)" title="Удалить">✕</button>
                </div>
              </div>
            </template>
          </div>
        </div>
      </div>
      <div class="sp-wrap" :class="{ open: inboxPanelOpen }">
        <div class="sp">
          <div class="sp-head">
            <button v-if="activeChatUser" class="sp-back-btn" @click="closeChatView" title="Назад">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
            </button>
            <div class="sp-head-main">
              <template v-if="!activeChatUser"><h2>{{ t('Сообщения') }}</h2></template>
              <template v-else>
                <router-link :to="'/user/' + activeChatUser.username" class="sp-partner-link" @click="closeInboxPanel">
                  <div class="sp-avatar sp-avatar-sm">
                    <img v-if="activeChatUser.avatar" :src="activeChatUser.avatar" alt="" loading="lazy">
                    <span v-else>{{ activeChatUser.username[0].toUpperCase() }}</span>
                  </div>
                  <div>
                    <div class="sp-chat-partner-name">{{ activeChatUser.first_name || activeChatUser.username }}</div>
                    <div class="sp-partner-nick">@{{ activeChatUser.username }}</div>
                    <div class="sp-partner-status">
                      <span v-if="activeChatUser.is_online" class="sp-status-online">в сети</span>
                      <span v-else-if="activeChatUser.last_online" class="sp-status-offline">{{ formatLastSeen(activeChatUser.last_online) }}</span>
                    </div>
                  </div>
                </router-link>
              </template>
            </div>
            <button class="sp-close" @click="closeInboxPanel">✕</button>
          </div>
          <div v-show="!activeChatUser" class="sp-body">
            <div class="sp-user-search-wrap">
              <input v-model="userSearch" class="sp-user-search-input" placeholder="Найти пользователя..." @input="onUserSearch">
            </div>
            <template v-if="userSearch.trim()">
              <p v-if="userSearchLoading" class="muted sp-empty">Поиск...</p>
              <p v-else-if="!userSearchResults.length" class="muted sp-empty">Не найдено</p>
              <div v-else v-for="u in userSearchResults" :key="u.username"
                class="sp-item sp-item-btn" @click="openChatByUser(u)">
                <div class="sp-avatar">
                  <img v-if="u.avatar" :src="u.avatar" alt="" loading="lazy">
                  <span v-else>{{ u.username[0].toUpperCase() }}</span>
                </div>
                <div class="sp-info">
                  <div class="sp-title">{{ u.first_name || u.username }}</div>
                  <div class="sp-sub">@{{ u.username }}</div>
                </div>
              </div>
            </template>
            <template v-else>
              <p v-if="inboxLoading" class="muted sp-empty">Загрузка...</p>
              <p v-else-if="!inbox.length" class="muted sp-empty">{{ t('Нет сообщений') }}</p>
              <template v-else>
                <div v-for="conv in inbox" :key="conv.id"
                  class="sp-item sp-item-btn" :class="{ 'sp-item-unread': chatUnreadMap[conv.username] }"
                  @click="openChat(conv)">
                  <div class="sp-avatar" style="position:relative">
                    <img v-if="conv.avatar" :src="conv.avatar" alt="" loading="lazy">
                    <span v-else>{{ conv.username[0].toUpperCase() }}</span>
                    <span v-if="conv.is_online" class="online-dot inbox-online-dot" title="Онлайн"></span>
                  </div>
                  <div class="sp-info">
                    <div class="sp-title">{{ conv.first_name || conv.username }}</div>
                    <div class="sp-sub">{{ conv.last_image ? '📷 Фото' : (conv.last_message || 'Нет сообщений') }}</div>
                  </div>
                  <div class="sp-item-end">
                    <span class="sp-time">{{ conv.last_timestamp ? formatTime(conv.last_timestamp) : '' }}</span>
                    <span v-if="chatUnreadMap[conv.username]" class="chat-unread-badge">
                      {{ chatUnreadMap[conv.username] > 99 ? '99+' : chatUnreadMap[conv.username] }}
                    </span>
                  </div>
                </div>
              </template>
            </template>
          </div>
          <div v-show="activeChatUser" class="sp-body sp-body-chat">
            <p v-if="chatLoading" class="muted sp-empty">Загрузка...</p>
            <div v-show="!chatLoading" class="sp-chat-log" ref="chatLogEl">
              <p v-if="!chatMessages.length" class="muted sp-empty">Нет сообщений</p>
              <div v-for="m in chatMessages" :key="m.id || m._k"
                class="sp-msg-row" :class="{ mine: m.sender === auth.user?.username }">
                <div class="sp-chat-msg" :class="{ mine: m.sender === auth.user?.username }">
                  <div v-if="m.reply_to" class="sp-chat-reply-quote">
                    <span class="sp-chat-reply-sender">@{{ m.reply_to.sender }}</span>
                    <span class="sp-chat-reply-text">{{ m.reply_to.text?.slice(0, 80) || '📷' }}</span>
                  </div>
                  <img v-if="m.image_url" :src="m.image_url" class="sp-chat-img" alt="">
                  <span v-else class="sp-chat-bubble">{{ m.text }}</span>
                  <span class="sp-chat-time">{{ formatChatTime(m.timestamp) }}</span>
                </div>
                <div class="chat-msg-actions">
                  <button class="sp-reply-btn" @click.stop="replyingTo = m" title="Ответить">↩</button>
                  <button v-if="m.sender === auth.user?.username && m.id" class="sp-reply-btn chat-del-btn" title="Удалить" @click.stop="deletePanelMsg(m)">✕</button>
                </div>
              </div>
              <div v-if="partnerTyping" class="sp-chat-msg sp-typing-indicator">
                <span class="sp-chat-bubble">
                  <span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>
                </span>
              </div>
            </div>
            <div v-if="replyingTo" class="sp-reply-bar">
              <div class="sp-reply-bar-content">
                <span class="sp-reply-bar-sender">↩ @{{ replyingTo.sender }}</span>
                <span class="sp-reply-bar-text">{{ replyingTo.text?.slice(0, 60) || '📷' }}</span>
              </div>
              <button class="sp-reply-bar-close" @click="replyingTo = null">✕</button>
            </div>
            <div v-show="activeChatUser" class="sp-chat-inputbar">
              <input v-model="chatText" class="sp-chat-field" placeholder="Сообщение..." autocomplete="off"
                @keyup.enter="sendPanelMsg" @input="onChatInput">
              <button class="btn sp-chat-send" @click="sendPanelMsg">→</button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
  <div v-else class="guest">
    <header class="guest-nav">
      <router-link to="/welcome" class="logo">PinGram</router-link>
      <div class="guest-actions">
        <router-link to="/login" class="btn-outline">Войти</router-link>
        <router-link to="/register" class="btn">Регистрация</router-link>
      </div>
    </header>
    <main class="container"><router-view /></main>
  </div>
  <div v-if="confirmState.visible" class="modal-overlay" @click.self="confirmNo">
    <div class="modal confirm-modal">
      <p class="confirm-msg">{{ confirmState.message }}</p>
      <div class="confirm-actions">
        <button class="btn" @click="confirmYes">Да</button>
        <button class="btn-outline" @click="confirmNo">Отмена</button>
      </div>
    </div>
  </div>
  <div class="toast-container">
    <div v-for="t in toasts" :key="t.id" class="toast" :class="'toast-' + t.type">{{ t.message }}</div>
  </div>
</template>
<script setup>
import { ref, computed, watch, watchEffect, onMounted, onUnmounted, nextTick } from 'vue'  
import { useRouter, useRoute } from 'vue-router'  
import { Home, LayoutGrid, Plus, MessageCircle, User, LogOut, Search, Bell, Menu, Sun, Moon, ShieldCheck } from 'lucide-vue-next'  
import { auth } from './auth'  
import { api } from './api'  
import { toasts, toastInfo } from './toast'  
import { confirmState, confirmYes, confirmNo, showConfirm } from './confirm'  
import { isDark, toggleTheme } from './theme'  
import { banState } from './ban'  
import { t } from './i18n'  
import { pendingChatUser } from './openChat'  
import CreatePostPanel from './components/CreatePostPanel.vue'  
const router = useRouter()  
const route = useRoute()  
const search = ref('')  
const unreadCount = ref(0)  
const sidebarOpen = ref(false)  
watchEffect(() => { if (banState.value) router.push('/banned') })
watch(pendingChatUser, async (u) => {  
  if (!u) return  
  pendingChatUser.value = null  
  closeNotifPanel()  
  inboxPanelOpen.value = true  
  await openChatByUser(u)  
})
const createPanelOpen = ref(false)  
function toggleCreatePanel() {  
  if (createPanelOpen.value) { createPanelOpen.value = false; return }  
  notifPanelOpen.value = false  
  inboxPanelOpen.value = false
  createPanelOpen.value = true  
}
function closeCreatePanel() { createPanelOpen.value = false }  
const notifPanelOpen = ref(false)  
const notifs = ref([])  
const notifsLoading = ref(false)  
const inboxPanelOpen = ref(false)  
const inbox = ref([])  
const inboxLoading = ref(false)  
const activeChatUser = ref(null)  
const chatMessages = ref([])  
const chatText = ref('')  
const chatLoading = ref(false)  
const chatLogEl = ref(null)  
const replyingTo = ref(null)  
const partnerTyping = ref(false)  
const chatUnreadMap = ref({})  
const chatUnreadTotal = computed(() => Object.values(chatUnreadMap.value).reduce((a, b) => a + b, 0))
const userSearch = ref('')  
const userSearchResults = ref([])  
const userSearchLoading = ref(false)  
let userSearchTimer = null  
let notifWs = null  
let panelChatWs = null  
let typingTimeout = null  
let typingThrottleTimer = null  
const canGoBack = computed(() => route.path !== '/')
watch(() => route.path, (path) => {  
  if (path !== '/search') search.value = ''  
  const m = path.match(/^\/messages\/(.+)$/)  
  if (m) {  
    const username = m[1]
    if (chatUnreadMap.value[username]) {  
      const updated = { ...chatUnreadMap.value }  
      delete updated[username]  
      chatUnreadMap.value = updated  
    }
  }
})
const NOTIF_LABELS = {  
  like: 'лайкнул(а) ваш пост',
  comment: 'прокомментировал(а) ваш пост',
  follow: 'подписался(ась) на вас',
  repost: 'сделал(а) репост вашего поста',
  mention: 'упомянул(а) вас',
  message: 'написал(а) вам сообщение',
  moderation_new: 'новый пост на модерации',
}
function typeLabel(t) { return NOTIF_LABELS[t] || t }  
function formatTime(s) {  
  if (!s) return ''
  const d = new Date(s)  
  const diff = Math.floor((Date.now() - d) / 1000)  
  if (diff < 60) return 'только что'  
  if (diff < 3600) return Math.floor(diff / 60) + ' мин'  
  if (diff < 86400) return Math.floor(diff / 3600) + ' ч'  
  return d.toLocaleDateString('ru-RU')  
}
function formatChatTime(ts) {  
  if (!ts) return ''
  return new Date(ts).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
}
function formatLastSeen(iso) {  
  if (!iso) return null
  const diff = Math.floor((Date.now() - new Date(iso)) / 60000)  
  if (diff < 2) return 'был(а) только что'  
  if (diff < 60) return `был(а) ${diff} мин назад`  
  if (diff < 1440) return `был(а) ${Math.floor(diff / 60)} ч назад`  
  return 'был(а) давно'  
}
async function fetchUnread() {  
  if (!auth.isAuthenticated()) return  
  try { const d = await api('/api/notifications/count/'); unreadCount.value = d.count } catch {  }
}
async function toggleNotifPanel() {  
  if (notifPanelOpen.value) { closeNotifPanel(); return }  
  closeInboxPanel()  
  notifPanelOpen.value = true  
  notifsLoading.value = true
  try {
    notifs.value = await api('/api/notifications/')  
    await api('/api/notifications/read/', { method: 'POST' })  
    unreadCount.value = 0  
  } finally { notifsLoading.value = false }
}
function closeNotifPanel() { notifPanelOpen.value = false }  
async function deleteNotif(id) {  
  try {
    await api(`/api/notifications/${id}/`, { method: 'DELETE' })  
    notifs.value = notifs.value.filter(n => n.id !== id)  
  } catch {  }
}
async function deleteAllNotifs() {  
  try {
    await api('/api/notifications/delete-all/', { method: 'DELETE' })  
    notifs.value = []  
    unreadCount.value = 0  
  } catch {  }
}
function onUserSearch() {  
  clearTimeout(userSearchTimer)  
  if (!userSearch.value.trim()) { userSearchResults.value = []; return }  
  userSearchLoading.value = true
  userSearchTimer = setTimeout(async () => {  
    try {
      userSearchResults.value = await api('/api/users/search/?q=' + encodeURIComponent(userSearch.value.trim()))
    } catch { userSearchResults.value = [] }
    finally { userSearchLoading.value = false }
  }, 300)  
}
async function openChatByUser(u) {  
  userSearch.value = ''  
  userSearchResults.value = []  
  await openChat({  
    username: u.username,
    avatar: u.avatar || null,
    first_name: u.first_name || '',
    is_online: u.is_online || false,
    last_online: u.last_online || null,
  })
}
async function toggleInboxPanel() {  
  if (inboxPanelOpen.value) { closeInboxPanel(); return }  
  closeNotifPanel()  
  activeChatUser.value = null  
  userSearch.value = ''
  userSearchResults.value = []
  inboxPanelOpen.value = true
  inboxLoading.value = true
  try { inbox.value = await api('/api/chat/') }  
  catch { inbox.value = [] }
  finally { inboxLoading.value = false }
}
function closeInboxPanel() {  
  inboxPanelOpen.value = false
  closeChatView()  
}
async function openChat(conv) {  
  activeChatUser.value = conv  
  if (chatUnreadMap.value[conv.username]) {  
    const updated = { ...chatUnreadMap.value }
    delete updated[conv.username]  
    chatUnreadMap.value = updated
  }
  chatMessages.value = []  
  chatLoading.value = true
  try {
    chatMessages.value = await api('/api/chat/' + conv.username + '/')  
    scrollChatDown()  
  } catch {  }
  finally { chatLoading.value = false }
  connectPanelChat(conv.username)  
}
function closeChatView() {  
  if (panelChatWs) { panelChatWs.close(); panelChatWs = null }  
  activeChatUser.value = null  
  replyingTo.value = null  
  partnerTyping.value = false  
  userSearch.value = ''
  userSearchResults.value = []
  clearTimeout(typingTimeout)  
  clearTimeout(typingThrottleTimer)  
  typingTimeout = null
  typingThrottleTimer = null
}
async function connectPanelChat(username) {  
  if (panelChatWs) panelChatWs.close()  
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'  
  try {
    const { ticket } = await api('/api/ws-ticket/')  
    panelChatWs = new WebSocket(`${proto}://${location.hostname}:8000/ws/chat/${username}/?ws_ticket=${ticket}`)
  } catch {
    panelChatWs = new WebSocket(`${proto}://${location.hostname}:8000/ws/chat/${username}/?token=${auth.token}`)
  }
  panelChatWs.onmessage = (e) => {  
    try {
      const data = JSON.parse(e.data)  
      if (data.type === 'typing') {  
        partnerTyping.value = true  
        clearTimeout(typingTimeout)  
        typingTimeout = setTimeout(() => { partnerTyping.value = false }, 3000)  
        return
      }
      partnerTyping.value = false  
      clearTimeout(typingTimeout)
      chatMessages.value.push({  
        id: data.msg_id,  
        _k: Date.now() + Math.random(),  
        sender: data.sender,  
        text: data.message,  
        image_url: data.image_url || null,  
        timestamp: data.timestamp,  
        reply_to: data.reply_to || null,  
      })
      scrollChatDown()  
      if (data.sender !== auth.user?.username && !inboxPanelOpen.value) {
        unreadCount.value++
        toastInfo(`Новое сообщение от @${data.sender}`)
      }
    } catch {  }
  }
}
async function scrollChatDown() {  
  await nextTick()  
  if (chatLogEl.value) chatLogEl.value.scrollTop = chatLogEl.value.scrollHeight  
}
function sendPanelMsg() {  
  const text = chatText.value.trim()
  if (!text || !panelChatWs || panelChatWs.readyState !== WebSocket.OPEN) return  
  clearTimeout(typingThrottleTimer)  
  typingThrottleTimer = null
  const payload = { message: text }  
  if (replyingTo.value?.id) payload.reply_to_id = replyingTo.value.id  
  panelChatWs.send(JSON.stringify(payload))  
  chatText.value = ''  
  replyingTo.value = null  
}
async function deletePanelMsg(m) {  
  try {
    await api(`/api/chat/message/${m.id}/`, { method: 'DELETE' })  
    chatMessages.value = chatMessages.value.filter(x => x.id !== m.id)  
  } catch {  }
}
function onChatInput() {  
  if (!panelChatWs || panelChatWs.readyState !== WebSocket.OPEN) return  
  if (typingThrottleTimer) return  
  panelChatWs.send(JSON.stringify({ type: 'typing' }))  
  typingThrottleTimer = setTimeout(() => { typingThrottleTimer = null }, 2000)  
}
function closeAllPanels() {  
  closeNotifPanel()
  closeInboxPanel()
  closeCreatePanel()
}
async function connectNotifications() {  
  if (!auth.isAuthenticated() || !auth.token) return  
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  let wsUrl
  try {
    const { ticket } = await api('/api/ws-ticket/')  
    wsUrl = `${proto}://${location.hostname}:8000/ws/notifications/?ws_ticket=${ticket}`
  } catch {
    wsUrl = `${proto}://${location.hostname}:8000/ws/notifications/?token=${auth.token}`  
  }
  notifWs = new WebSocket(wsUrl)  
  notifWs.onmessage = (e) => {  
    try {
      const data = JSON.parse(e.data)
      if (data.notif_type === 'moderation_new') {  
        toastInfo('Новый пост на модерации')
        return
      }
      if (data.notif_type === 'chat_message') {  
        const sender = data.sender
        const inPanel = activeChatUser.value?.username === sender  
        const inChatRoom = route.path === `/messages/${sender}`  
        if (!inPanel && !inChatRoom) {  
          chatUnreadMap.value = { ...chatUnreadMap.value, [sender]: (chatUnreadMap.value[sender] || 0) + 1 }
          toastInfo(`Новое сообщение от @${sender}`)
        }
        return
      }
      if (!notifPanelOpen.value) {  
        unreadCount.value++  
      }
      if (notifPanelOpen.value) {  
        notifs.value.unshift({  
          id: data.id,
          actor: data.actor,  
          actor_avatar: data.actor_avatar,
          type: data.notif_type,
          post_id: data.post_id,
          is_read: true,  
          created_at: data.created_at,
        })
      }
    } catch {  }
  }
  notifWs.onerror = () => {  }  
  notifWs.onclose = (e) => {  
    if (e.code !== 1000 && auth.isAuthenticated()) setTimeout(() => connectNotifications(), 5000)
  }
}
function disconnectAll() {  
  if (notifWs) { notifWs.close(); notifWs = null }  
  if (panelChatWs) { panelChatWs.close(); panelChatWs = null }  
}
async function logout() {  
  if (!(await showConfirm('Выйти из аккаунта?'))) return  
  disconnectAll()  
  auth.logout()  
  router.push('/welcome')  
}
function doSearch() {  
  if (search.value.trim()) router.push({ path: '/search', query: { q: search.value.trim() } })
}
function handleThemeToggle() { toggleTheme() }  
onMounted(async () => {  
  if (auth.isAuthenticated()) {  
    try {
      const me = await api('/api/me/')  
      auth.setUser(me)  
    } catch {
      auth.logout()  
      router.push('/login')
      return
    }
    fetchUnread()  
    connectNotifications()  
  }
})
onUnmounted(disconnectAll)  
</script>