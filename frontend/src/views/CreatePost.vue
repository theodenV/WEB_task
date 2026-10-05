<template>
  <div class="create-post-page">  
    <div class="create-post-card">  
      <h1 class="create-post-title">Новый пост</h1>
      <div class="cp-media-tabs">
        <button :class="{ active: mediaMode === 'image' }" @click="setMode('image')">Фото</button>
        <button :class="{ active: mediaMode === 'video' }" @click="setMode('video')">Видео</button>
      </div>
      <template v-if="mediaMode === 'image'">
        <div class="cp-images-row">
          <div v-for="(img, i) in images" :key="i" class="cp-thumb-wrap">
            <img :src="img.preview" class="cp-thumb" alt="">
            <button class="cp-thumb-del" @click="removeImage(i)">✕</button>
            <span v-if="i === 0" class="cp-thumb-main">Главное</span>  
          </div>
          <label v-if="images.length < 5" class="cp-add-btn">  
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <rect x="3" y="3" width="18" height="18" rx="3"/>
              <line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/>
            </svg>
            <input type="file" accept="image/jpeg,image/png,image/webp,image/gif" multiple hidden @change="onFilesSelected">
          </label>
        </div>
        <p v-if="!images.length" class="cp-hint-empty">Добавь до 5 изображений (макс. 15 МБ каждое)</p>
      </template>
      <template v-else-if="mediaMode === 'video'">
        <div class="cp-single-media">
          <div v-if="videoFile" class="cp-thumb-wrap" :style="{ width: '100%', maxWidth: '100%', height: 'auto', overflow: 'visible' }">
            <video :src="videoPreview" controls style="width:100%;border-radius:10px" muted @loadedmetadata="onVideoMeta"></video>
            <button class="cp-thumb-del" @click="videoFile=null;videoPreview=null;videoNaturalW=null">✕</button>
          </div>
          <label v-else class="cp-add-btn cp-add-full">
            <span>Загрузить видео (MP4, до 100 МБ)</span>
            <input type="file" accept="video/mp4,video/webm,video/ogg" hidden @change="onVideoSelected">
          </label>
        </div>
      </template>
      <div class="caption-wrap" style="margin-top:14px">
        <textarea
          ref="captionRef"  
          v-model="caption"
          placeholder="Подпись к посту"
          maxlength="500"
          class="caption-auto"
          @input="autoResize"  
        ></textarea>
        <span class="char-counter" :class="{ warn: caption.length > 450 }">{{ caption.length }}/500</span>
      </div>
      <div class="field-wrap">
        <label>Теги <span class="field-optional">(через пробел или запятую)</span></label>
        <input v-model="tagsInput" placeholder="дизайн природа архитектура">
      </div>
      <div v-if="parsedTags.length" class="tags-preview">
        <span v-for="tag in parsedTags" :key="tag" class="tag-chip">#{{ tag }}</span>
      </div>
      <div class="field-wrap" v-if="collections.length">
        <label>Добавить в коллекцию <span class="field-optional">(необязательно)</span></label>
        <select v-model="selectedCollection">
          <option :value="null">— не добавлять —</option>  
          <option v-for="c in collections" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <p class="hint">После публикации пост попадёт на модерацию.</p>
      <div style="display:flex;gap:10px">
        <button class="btn" style="flex:1" :disabled="!canSubmit || submitting" @click="submit">
          {{ submitting ? 'Отправляю...' : 'Отправить на модерацию' }}
        </button>
        <button class="btn-outline" @click="router.push('/')">Отмена</button>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { toastSuccess, toastError } from '../toast'
const router = useRouter()
const mediaMode = ref('image')  
const images = ref([])  
const videoFile = ref(null), videoPreview = ref(null), videoNaturalW = ref(null)
const caption = ref('')
const captionRef = ref(null)  
const tagsInput = ref('')
const error = ref(null)
const submitting = ref(false)
const collections = ref([])  
const selectedCollection = ref(null)  
const parsedTags = computed(() =>
  tagsInput.value.replace(/[,;]+/g, ' ').split(/\s+/).filter(Boolean).map(t => t.replace(/^#/, ''))
)
const canSubmit = computed(() => {  
  if (mediaMode.value === 'image') return images.value.length > 0
  if (mediaMode.value === 'video') return !!videoFile.value
  return false
})
function autoResize(e) {  
  const el = e?.target ?? captionRef.value  
  if (!el) return
  el.style.height = 'auto'  
  el.style.height = el.scrollHeight + 'px'  
}
function setMode(mode) {  
  mediaMode.value = mode
  images.value.forEach(img => URL.revokeObjectURL(img.preview))  
  images.value = []
  if (videoPreview.value) { URL.revokeObjectURL(videoPreview.value); videoFile.value = null; videoPreview.value = null }
  error.value = null
}
function onFilesSelected(e) {  
  const files = Array.from(e.target.files); e.target.value = ''  
  for (const f of files) {
    if (images.value.length >= 5) break  
    if (f.size > 15 * 1024 * 1024) { toastError(`${f.name}: файл больше 15 МБ`); continue }  
    images.value.push({ file: f, preview: URL.createObjectURL(f) })  
  }
}
function removeImage(i) {  
  URL.revokeObjectURL(images.value[i].preview)  
  images.value.splice(i, 1)
}
function onVideoSelected(e) {  
  const f = e.target.files[0]; e.target.value = ''
  if (!f) return
  if (f.size > 100 * 1024 * 1024) { toastError('Файл слишком большой (максимум 100 МБ)'); return }
  if (videoPreview.value) URL.revokeObjectURL(videoPreview.value)
  videoNaturalW.value = null  
  videoFile.value = f; videoPreview.value = URL.createObjectURL(f)
}
function onVideoMeta(e) {  
  videoNaturalW.value = e.target.videoWidth || null  
}
async function submit() {  
  error.value = null
  submitting.value = true
  const form = new FormData()
  form.append('caption', caption.value.trim())
  if (parsedTags.value.length) form.append('tags', JSON.stringify(parsedTags.value))
  if (mediaMode.value === 'image') {
    form.append('image', images.value[0].file)  
    for (let i = 1; i < images.value.length; i++) form.append('images', images.value[i].file)  
  } else if (mediaMode.value === 'video') {
    form.append('video', videoFile.value)
  }
  try {
    const post = await api('/api/posts/', { method: 'POST', body: form })  
    if (selectedCollection.value && post?.id) {  
      try {
        await api(`/api/collections/${selectedCollection.value}/add/`, {
          method: 'POST',
          body: JSON.stringify({ post: post.id }),
        })
      } catch {  }
    }
    toastSuccess('Пост отправлен на модерацию')
    router.push('/')  
  } catch (e) {
    error.value = e.detail || Object.values(e).flat().join(' ') || 'Ошибка'
    toastError(error.value)
  } finally { submitting.value = false }
}
onMounted(async () => {
  try { collections.value = await api('/api/collections/') } catch {  }
})
</script>