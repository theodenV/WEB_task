<template>
  <div class="chat-page">
    <div class="chat-header">  
      <router-link to="/messages" class="back-btn" title="Назад">←</router-link>
      <div class="chat-header-avatar" style="position:relative">  
        <img v-if="partnerAvatar" :src="partnerAvatar" alt="">
        <span v-else>{{ username[0].toUpperCase() }}</span>
        <span v-if="partnerOnline" class="online-dot" title="Онлайн"></span>  
      </div>
      <div class="chat-header-info">
        <div class="chat-header-username">@{{ username }}</div>
        <div class="chat-header-status">
          <span v-if="partnerOnline" class="status-online">в сети</span>  
          <span v-else-if="lastSeen" class="status-offline">{{ lastSeen }}</span>  
        </div>
      </div>
    </div>
    <div class="chat-log" ref="logEl">  
      <div v-for="m in messages" :key="m.id || m._k" class="chat-msg-wrap" :class="{ mine: m.sender === myUsername }">
        <div class="chat-msg" :class="{ mine: m.sender === myUsername }">
          <span class="chat-author">@{{ m.sender }}</span>  
          <div v-if="m.reply_to" class="chat-reply-quote">  
            <span class="chat-reply-sender">@{{ m.reply_to.sender }}</span>
            <span class="chat-reply-text">{{ m.reply_to.text || 'Фото' }}</span>  
          </div>
          <img v-if="m.image_url" :src="m.image_url" class="chat-img-msg" alt="фото" @click="lightboxImg = m.image_url">
          <span v-else class="chat-text">{{ m.text }}</span>  
          <span class="chat-time">{{ formatTime(m.timestamp) }}</span>  
        </div>
        <div class="chat-msg-actions">  
          <button class="chat-reply-hover-btn" title="Ответить" @click="replyTo = m">↩</button>  
          <button v-if="m.sender === myUsername && m.id" class="chat-del-btn" title="Удалить" @click="deleteMsg(m)">✕</button>
        </div>
      </div>
    </div>
    <div class="chat-input-area">  
      <div v-if="replyTo" class="sp-reply-bar">
        <div class="sp-reply-bar-content">
          <span class="sp-reply-bar-sender">@{{ replyTo.sender }}</span>
          <span class="sp-reply-bar-text">{{ replyTo.text || 'Фото' }}</span>
        </div>
        <button class="sp-reply-btn" @click="replyTo = null">✕</button>  
      </div>
      <div v-if="emojiOpen" class="emoji-picker">
        <button v-for="e in EMOJIS" :key="e" class="emoji-btn" @click="insertEmoji(e)">{{ e }}</button>
      </div>
      <div class="chat-form">  
        <button class="chat-tool-btn" title="Эмодзи" @click="emojiOpen = !emojiOpen">😊</button>  
        <label class="chat-tool-btn" title="Отправить фото">  
          📷
          <input type="file" accept="image/*" hidden @change="sendImage">  
        </label>
        <input v-model="text" placeholder="Сообщение..." autocomplete="off" @keyup.enter="send" class="chat-text-input">
        <button class="btn" @click="send">→</button>  
      </div>
    </div>
  </div>
  <div v-if="lightboxImg" class="lightbox" @click="lightboxImg = null">
    <img :src="lightboxImg" alt="">
    <button class="lightbox-close" @click.stop="lightboxImg = null">✕</button>
  </div>
</template>
<script setup>
import { ref, watch, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'
import { auth } from '../auth'
import { toastError } from '../toast'
const route = useRoute()
const myUsername = auth.user?.username  
const username = ref('')  
const messages = ref([])  
const text = ref('')  
const logEl = ref(null)  
const emojiOpen = ref(false)  
const lightboxImg = ref(null)  
const partnerAvatar = ref(null)  
const partnerOnline = ref(false)  
const lastSeen = ref(null)  
const replyTo = ref(null)  
let socket = null  
const EMOJIS = ['😀','😂','❤️','👍','🔥','😊','🎉','😎','🙏','💯',
                 '😢','😡','🤔','😍','👏','✨','🌟','💪','🥳','😴',
                 '🤣','😅','😬','🤗','😏','🙄','😇','🤩','😮','💀']  
function formatTime(ts) {  
  if (!ts) return ''
  return new Date(ts).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
}
async function scrollDown() {  
  await nextTick()  
  if (logEl.value) logEl.value.scrollTop = logEl.value.scrollHeight  
}
function insertEmoji(e) { text.value += e; emojiOpen.value = false }  
function cleanup() {  
  if (socket) { socket.close(); socket = null }
}
async function init(uname) {  
  cleanup()  
  username.value = uname
  messages.value = []  
  partnerAvatar.value = null
  partnerOnline.value = false
  lastSeen.value = null
  replyTo.value = null
  emojiOpen.value = false
  try { messages.value = await api('/api/chat/' + uname + '/') } catch {  }
  scrollDown()  
  try {
    const partner = await api('/api/users/' + uname + '/')
    partnerAvatar.value = partner.avatar || null
    partnerOnline.value = partner.is_online || false
    if (!partner.is_online && partner.last_online) {  
      const diff = Math.floor((Date.now() - new Date(partner.last_online)) / 60000)  
      if (diff < 2) lastSeen.value = 'был(а) только что'
      else if (diff < 60) lastSeen.value = `был(а) ${diff} мин назад`
      else if (diff < 1440) lastSeen.value = `был(а) ${Math.floor(diff / 60)} ч назад`
      else lastSeen.value = 'был(а) давно'
    }
  } catch {  }
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'  
  try {
    const { ticket } = await api('/api/ws-ticket/')  
    socket = new WebSocket(`${proto}://${location.hostname}:8000/ws/chat/${uname}/?ws_ticket=${ticket}`)
  } catch {
    socket = new WebSocket(`${proto}://${location.hostname}:8000/ws/chat/${uname}/?token=${auth.token}`)
  }
  socket.onmessage = (e) => {  
    try {
      const data = JSON.parse(e.data)
      if (data.type === 'typing') return  
      messages.value.push({  
        id: data.msg_id,
        _k: Date.now() + Math.random(),  
        sender: data.sender,
        text: data.message,
        image_url: data.image_url || null,
        timestamp: data.timestamp,
        reply_to: data.reply_to || null,  
      })
      scrollDown()
    } catch {  }
  }
  socket.onerror = () => toastError('Соединение с чатом прервано')
  socket.onclose = (ev) => { if (ev.code !== 1000) toastError('Чат отключён') }
}
watch(() => route.params.username, (uname) => { if (uname) init(uname) }, { immediate: true })
onUnmounted(cleanup)  
function send() {  
  const t = text.value.trim()
  if (t && socket && socket.readyState === WebSocket.OPEN) {  
    socket.send(JSON.stringify({ message: t, reply_to: replyTo.value?.id || null }))
    text.value = ''  
    replyTo.value = null  
  }
}
async function deleteMsg(m) {  
  try {
    await api(`/api/chat/message/${m.id}/`, { method: 'DELETE' })  
    messages.value = messages.value.filter(x => x.id !== m.id)  
  } catch { toastError('Не удалось удалить сообщение') }
}
async function sendImage(e) {  
  const file = e.target.files[0]
  if (!file) return
  e.target.value = ''  
  const form = new FormData()
  form.append('image', file)
  try {
    const msg = await api('/api/chat/' + username.value + '/image/', { method: 'POST', body: form })
    messages.value.push({ ...msg, _k: Date.now() })  
    scrollDown()
  } catch { toastError('Не удалось отправить фото') }
}
</script>