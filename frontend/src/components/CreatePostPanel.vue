<template>
  <div class="sp-head">  
    <h2>Новый пост</h2>
    <button class="sp-close" @click="$emit('close')">✕</button>  
  </div>
  <div class="sp-body cp-body">  
    <div class="cp-media-tabs">  
      <button :class="{ active: mediaMode === 'image' }" @click="setMode('image')">Фото</button>
      <button :class="{ active: mediaMode === 'gif' }" @click="setMode('gif')">GIF</button>
      <button :class="{ active: mediaMode === 'video' }" @click="setMode('video')">Видео</button>
    </div>
    <template v-if="mediaMode === 'image'">
      <div class="cp-images-row">  
        <div v-for="(img, i) in images" :key="i" class="cp-thumb-wrap">  
          <img :src="img.preview" class="cp-thumb" alt="">  
          <button class="cp-thumb-del" @click="removeImage(i)" title="Удалить">✕</button>  
          <span v-if="i === 0" class="cp-thumb-main">Главное</span>  
        </div>
        <label v-if="images.length < 5" class="cp-add-btn" title="Добавить фото">  
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <rect x="3" y="3" width="18" height="18" rx="3"/>
            <line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/>
          </svg>
          <input type="file" accept="image/jpeg,image/png,image/webp" hidden @change="onFileSelected">
        </label>
      </div>
      <p v-if="!images.length" class="cp-hint-empty">Добавь до 5 изображений</p>  
    </template>
    <template v-else-if="mediaMode === 'gif'">
      <div class="cp-single-media">
        <div v-if="gifFile" class="cp-thumb-wrap" style="width:100%;max-height:200px;overflow:hidden">
          <img :src="gifPreview" style="width:100%;object-fit:contain;max-height:200px" alt="">  
          <button class="cp-thumb-del" @click="gifFile=null;gifPreview=null">✕</button>  
        </div>
        <label v-else class="cp-add-btn cp-add-full" title="Загрузить GIF">  
          <span>Загрузить GIF</span>
          <input type="file" accept="image/gif" hidden @change="onGifSelected">
        </label>
      </div>
    </template>
    <template v-else-if="mediaMode === 'video'">
      <div class="cp-single-media">
        <div v-if="videoFile" class="cp-thumb-wrap" style="width:100%">
          <video :src="videoPreview" controls style="width:100%;max-height:240px;object-fit:contain" muted></video>
          <button class="cp-thumb-del" @click="videoFile=null;videoPreview=null">✕</button>
        </div>
        <label v-else class="cp-add-btn cp-add-full" title="Загрузить видео">
          <span>Загрузить видео (MP4, до 100 МБ)</span>
          <input type="file" accept="video/mp4,video/webm,video/ogg" hidden @change="onVideoSelected">
        </label>
      </div>
    </template>
    <div class="caption-wrap">
      <textarea v-model="caption" placeholder="Подпись к посту" rows="3" maxlength="500"></textarea>
      <span class="char-counter" :class="{ warn: caption.length > 450 }">{{ caption.length }}/500</span>
    </div>
    <div class="field-wrap">
      <label>Теги <span class="field-optional">(через пробел или запятую)</span></label>
      <input v-model="tagsInput" placeholder="дизайн природа архитектура">
    </div>
    <div v-if="parsedTags.length" class="tags-preview">  
      <span v-for="tag in parsedTags" :key="tag" class="tag-chip">#{{ tag }}</span>  
    </div>
    <p v-if="error" class="error">{{ error }}</p>
    <p class="hint">После публикации пост попадёт на модерацию.</p>  
    <button class="btn" style="width:100%" :disabled="!canSubmit || submitting" @click="submit">
      {{ submitting ? 'Отправляю...' : 'Отправить на модерацию' }}
    </button>
  </div>
  <Teleport to="body">
    <CropModal v-if="cropSrc" :src="cropSrc" @confirm="onCropConfirm" @cancel="cropSrc = null" />
  </Teleport>
</template>
<script setup>
import { ref, computed } from 'vue'
import { api } from '../api'
import { toastSuccess, toastError } from '../toast'
import CropModal from './CropModal.vue'  
const emit = defineEmits(['close'])  
const mediaMode = ref('image')  
const images = ref([])  
const gifFile = ref(null)  
const gifPreview = ref(null)  
const videoFile = ref(null)  
const videoPreview = ref(null)  
const caption = ref('')  
const tagsInput = ref('')  
const error = ref(null)  
const submitting = ref(false)  
const cropSrc = ref(null)  
let pendingFileURL = null  
const parsedTags = computed(() => {  
  const raw = tagsInput.value.replace(/[,;]+/g, ' ')  
  return raw.split(/\s+/).filter(Boolean).map(t => t.replace(/^#/, ''))  
})
const canSubmit = computed(() => {  
  if (mediaMode.value === 'image') return images.value.length > 0  
  if (mediaMode.value === 'gif') return !!gifFile.value  
  if (mediaMode.value === 'video') return !!videoFile.value  
  return false
})
function setMode(mode) {  
  mediaMode.value = mode
  images.value.forEach(img => URL.revokeObjectURL(img.preview))  
  images.value = []
  if (gifPreview.value) { URL.revokeObjectURL(gifPreview.value); gifFile.value = null; gifPreview.value = null }
  if (videoPreview.value) { URL.revokeObjectURL(videoPreview.value); videoFile.value = null; videoPreview.value = null }
  error.value = null
}
function onFileSelected(e) {  
  const f = e.target.files[0]  
  e.target.value = ''  
  if (!f) return
  pendingFileURL = URL.createObjectURL(f)  
  cropSrc.value = pendingFileURL  
}
function onCropConfirm(croppedFile) {  
  cropSrc.value = null  
  const preview = URL.createObjectURL(croppedFile)  
  images.value.push({ file: croppedFile, preview })  
  if (pendingFileURL) { URL.revokeObjectURL(pendingFileURL); pendingFileURL = null }  
}
function removeImage(i) {  
  URL.revokeObjectURL(images.value[i].preview)  
  images.value.splice(i, 1)  
}
function onGifSelected(e) {  
  const f = e.target.files[0]
  e.target.value = ''
  if (!f) return
  if (gifPreview.value) URL.revokeObjectURL(gifPreview.value)  
  gifFile.value = f
  gifPreview.value = URL.createObjectURL(f)
}
function onVideoSelected(e) {  
  const f = e.target.files[0]
  e.target.value = ''
  if (!f) return
  if (f.size > 100 * 1024 * 1024) { toastError('Файл слишком большой (максимум 100 МБ)'); return }  
  if (videoPreview.value) URL.revokeObjectURL(videoPreview.value)
  videoFile.value = f
  videoPreview.value = URL.createObjectURL(f)
}
async function submit() {  
  error.value = null
  submitting.value = true
  const form = new FormData()  
  const tagStr = parsedTags.value.map(t => '#' + t).join(' ')  
  const fullCaption = (caption.value + (tagStr ? ' ' + tagStr : '')).trim()  
  form.append('caption', fullCaption)  
  if (mediaMode.value === 'image') {
    form.append('image', images.value[0].file)  
    for (let i = 1; i < images.value.length; i++) form.append('images', images.value[i].file)  
  } else if (mediaMode.value === 'gif') {
    form.append('image', gifFile.value)  
  } else if (mediaMode.value === 'video') {
    form.append('video', videoFile.value)  
  }
  try {
    await api('/api/posts/', { method: 'POST', body: form })  
    toastSuccess('Пост отправлен на модерацию')
    images.value.forEach(img => URL.revokeObjectURL(img.preview))
    images.value = []
    if (gifPreview.value) { URL.revokeObjectURL(gifPreview.value); gifFile.value = null; gifPreview.value = null }
    if (videoPreview.value) { URL.revokeObjectURL(videoPreview.value); videoFile.value = null; videoPreview.value = null }
    caption.value = ''
    tagsInput.value = ''
    emit('close')  
  } catch (e) {
    error.value = e.detail || Object.values(e).flat().join(' ') || 'Ошибка'  
    toastError(error.value)
  } finally { submitting.value = false }
}
</script>