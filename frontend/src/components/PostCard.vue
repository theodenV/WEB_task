<template>
  <div class="pin-card" @click="$router.push('/post/' + post.id)" @mouseleave="closeAll">
    <div v-if="post.media_type === 'video'" class="pin-card-media pin-card-video-wrap">
      <video :src="post.video" class="pin-card-img" muted loop preload="metadata"
        @mouseenter="e => e.target.play()" @mouseleave="e => { e.target.pause(); e.target.currentTime=0 }"></video>
      <div class="pin-video-badge">  
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
      </div>
    </div>
    <div v-else-if="post.image" class="pin-card-media">
      <img :src="post.image" :alt="post.caption || ''" loading="lazy" class="pin-card-img">
    </div>
    <div v-else-if="post.quoted_post && post.quoted_post.image" class="pin-card-media">
      <img :src="post.quoted_post.image" :alt="post.caption || ''" loading="lazy" class="pin-card-img pin-card-img-quoted">
    </div>
    <div v-else class="pin-card-text-only">
      <p>{{ post.caption || '' }}</p>
    </div>
    <div v-if="post.media_type !== 'video' && post.extra_images && post.extra_images.length" class="pin-multi-badge">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="2" y="7" width="15" height="15" rx="2"/><path d="M7 2h13a2 2 0 012 2v13"/>
      </svg>
    </div>
    <div v-if="post.quoted_post" class="pin-quote-badge">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 014-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 01-4 4H3"/></svg>
      Репост
    </div>
    <div class="pin-card-overlay">
      <div class="pin-card-top">  
        <router-link :to="'/user/' + post.author" class="pin-card-author" @click.stop>
          <div class="pin-card-avatar">  
            <img v-if="post.author_avatar" :src="post.author_avatar" alt="">  
            <span v-else>{{ post.author[0].toUpperCase() }}</span>  
          </div>
          <span>@{{ post.author }}</span>  
        </router-link>
      </div>
      <div class="pin-card-actions">  
        <button v-if="isOwn" class="pin-action-btn pin-del-btn" title="Удалить" @click.stop="$emit('delete', post)">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"></path><path d="M10 11v6M14 11v6"></path><path d="M9 6V4a1 1 0 011-1h4a1 1 0 011 1v2"></path></svg>
        </button>
        <div v-if="auth.isAuthenticated()" class="pin-save-wrap" @click.stop>
          <button class="pin-action-btn" title="Поделиться" @click.stop="copyLink">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
          </button>
        </div>
        <div v-if="auth.isAuthenticated()" class="pin-save-wrap" @click.stop>
          <button class="pin-action-btn pin-save-btn" title="Сохранить" @click.stop="saveOpen = !saveOpen">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2z"></path></svg>
          </button>
          <div v-if="saveOpen" class="pin-save-dropdown">  
            <p v-if="!collections.length" class="pin-save-empty">Нет коллекций</p>  
            <button v-for="c in collections" :key="c.id" class="pin-save-option" @click.stop="saveToCollection(c.id)">
              {{ c.name }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, computed } from 'vue'  
import { api } from '../api'  
import { auth } from '../auth'  
import { toastSuccess, toastError } from '../toast'  
const props = defineProps({
  post: Object,  
  collections: { type: Array, default: () => [] },  
})
defineEmits(['delete'])  
const saveOpen = ref(false)  
const isOwn = computed(() => auth.user && props.post.author === auth.user.username)  
function closeAll() {  
  saveOpen.value = false
}
async function copyLink() {  
  try {
    await navigator.clipboard.writeText(`${location.origin}/post/${props.post.id}`)  
    toastSuccess('Ссылка скопирована')
  } catch { toastError('Не удалось скопировать') }  
}
async function saveToCollection(collectionId) {  
  try {
    await api(`/api/collections/${collectionId}/add/`, {  
      method: 'POST',
      body: JSON.stringify({ post: props.post.id }),  
    })
    toastSuccess('Сохранено')
  } catch { toastError('Не удалось сохранить') }
  saveOpen.value = false  
}
</script>