<template>
  <div class="modal-overlay" @click.self="$emit('cancel')">  
    <div class="modal crop-modal-wrap">
      <div class="modal-head">
        <h2>Обрезать фото</h2>
        <button class="modal-close" @click="$emit('cancel')">✕</button>
      </div>
      <div class="crop-viewport" ref="viewport">  
        <img ref="imgEl" :src="src" alt="" draggable="false" class="crop-img"
          :style="{ left: imgX + 'px', top: imgY + 'px', width: imgW + 'px', height: imgH + 'px' }"
          @load="onLoad">
        <div class="crop-dark" :style="{ top: 0, left: 0, right: 0, height: cropY + 'px' }"></div>  
        <div class="crop-dark" :style="{ top: (cropY + cropH) + 'px', left: 0, right: 0, bottom: 0 }"></div>  
        <div class="crop-dark" :style="{ top: cropY + 'px', left: 0, width: cropX + 'px', height: cropH + 'px' }"></div>  
        <div class="crop-dark" :style="{ top: cropY + 'px', left: (cropX + cropW) + 'px', right: 0, height: cropH + 'px' }"></div>  
        <div class="crop-box"
          :style="{ left: cropX + 'px', top: cropY + 'px', width: cropW + 'px', height: cropH + 'px' }"
          @mousedown.prevent="startMove" @touchstart.prevent="startMoveTouch">
          <div class="crop-grid-overlay"></div>  
          <svg class="crop-corners" viewBox="0 0 100 100" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M 0,20 L 0,0 L 20,0"     stroke="white" stroke-width="4" fill="none" stroke-linecap="round"/>  
            <path d="M 80,0 L 100,0 L 100,20"  stroke="white" stroke-width="4" fill="none" stroke-linecap="round"/>  
            <path d="M 0,80 L 0,100 L 20,100"  stroke="white" stroke-width="4" fill="none" stroke-linecap="round"/>  
            <path d="M 80,100 L 100,100 L 100,80" stroke="white" stroke-width="4" fill="none" stroke-linecap="round"/>  
          </svg>
        </div>
        <div v-for="h in handles" :key="h.dir"
          class="crop-handle" :class="'crop-handle-' + h.dir" :style="h.style"
          @mousedown.prevent.stop="startResize($event, h.dir)"
          @touchstart.prevent.stop="startResizeTouch($event, h.dir)">
        </div>
      </div>
      <p class="crop-hint muted">Перемещай рамку · Тяни за углы и края для изменения размера</p>
      <div style="display:flex;gap:10px;margin-top:12px">
        <button class="btn" @click="confirm">Готово</button>  
        <button class="btn-outline" @click="$emit('cancel')">Отмена</button>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
const props = defineProps({
  src: String,  
  square: { type: Boolean, default: false },  
})
const emit = defineEmits(['confirm', 'cancel'])  
const VP = 380  
const MIN_CROP = 60  
const HANDLE = 10  
const viewport = ref(null)  
const imgEl = ref(null)  
const imgX = ref(0), imgY = ref(0), imgW = ref(0), imgH = ref(0)
const cropX = ref(0), cropY = ref(0), cropW = ref(0), cropH = ref(0)
function onLoad() {  
  const nat = imgEl.value  
  const ratio = nat.naturalWidth / nat.naturalHeight  
  let w, h
  if (ratio >= 1) { w = VP; h = VP / ratio }  
  else             { h = VP; w = VP * ratio }  
  imgX.value = (VP - w) / 2  
  imgY.value = (VP - h) / 2  
  imgW.value = w
  imgH.value = h
  cropX.value = imgX.value
  cropY.value = imgY.value
  cropW.value = imgW.value
  cropH.value = props.square ? Math.min(imgW.value, imgH.value) : imgH.value  
  if (props.square) {  
    cropX.value = imgX.value + (imgW.value - cropW.value) / 2
    cropY.value = imgY.value + (imgH.value - cropH.value) / 2
  }
}
const handles = computed(() => {  
  const cx = cropX.value, cy = cropY.value, cw = cropW.value, ch = cropH.value
  const H = HANDLE  
  return [
    { dir: 'nw', style: { left: (cx - H) + 'px',        top: (cy - H) + 'px' } },  
    { dir: 'n',  style: { left: (cx + cw/2 - H) + 'px', top: (cy - H) + 'px' } },  
    { dir: 'ne', style: { left: (cx + cw - H) + 'px',   top: (cy - H) + 'px' } },  
    { dir: 'e',  style: { left: (cx + cw - H) + 'px',   top: (cy + ch/2 - H) + 'px' } },  
    { dir: 'se', style: { left: (cx + cw - H) + 'px',   top: (cy + ch - H) + 'px' } },  
    { dir: 's',  style: { left: (cx + cw/2 - H) + 'px', top: (cy + ch - H) + 'px' } },  
    { dir: 'sw', style: { left: (cx - H) + 'px',        top: (cy + ch - H) + 'px' } },  
    { dir: 'w',  style: { left: (cx - H) + 'px',        top: (cy + ch/2 - H) + 'px' } },  
  ]
})
let dragMode = null  
let startMX = 0, startMY = 0  
let startCX = 0, startCY = 0, startCW = 0, startCH = 0  
function beginDrag(clientX, clientY, mode) {  
  dragMode = mode
  startMX = clientX; startMY = clientY
  startCX = cropX.value; startCY = cropY.value
  startCW = cropW.value; startCH = cropH.value
}
function startMove(e) { beginDrag(e.clientX, e.clientY, 'move') }  
function startResize(e, dir) { beginDrag(e.clientX, e.clientY, dir) }  
function startMoveTouch(e) { beginDrag(e.touches[0].clientX, e.touches[0].clientY, 'move') }  
function startResizeTouch(e, dir) { beginDrag(e.touches[0].clientX, e.touches[0].clientY, dir) }  
function applyDrag(clientX, clientY) {  
  if (!dragMode) return  
  const dx = clientX - startMX  
  const dy = clientY - startMY  
  if (dragMode === 'move') {  
    cropX.value = clamp(startCX + dx, imgX.value, imgX.value + imgW.value - startCW)  
    cropY.value = clamp(startCY + dy, imgY.value, imgY.value + imgH.value - startCH)
    return
  }
  let nx = startCX, ny = startCY, nw = startCW, nh = startCH  
  if (dragMode.includes('n')) {  
    const newTop = clamp(startCY + dy, imgY.value, startCY + startCH - MIN_CROP)  
    nh = startCY + startCH - newTop  
    ny = newTop
  }
  if (dragMode.includes('s')) {  
    nh = clamp(startCH + dy, MIN_CROP, imgY.value + imgH.value - startCY)
  }
  if (dragMode.includes('w')) {  
    const newLeft = clamp(startCX + dx, imgX.value, startCX + startCW - MIN_CROP)
    nw = startCX + startCW - newLeft
    nx = newLeft
  }
  if (dragMode.includes('e')) {  
    nw = clamp(startCW + dx, MIN_CROP, imgX.value + imgW.value - startCX)
  }
  if (props.square) {  
    const size = Math.min(nw, nh)
    if (dragMode.includes('n')) ny = startCY + startCH - size  
    if (dragMode.includes('w')) nx = startCX + startCW - size  
    nw = size; nh = size  
  }
  cropX.value = nx; cropY.value = ny; cropW.value = nw; cropH.value = nh  
}
function stopDrag() { dragMode = null }  
const onMouseMove = e => applyDrag(e.clientX, e.clientY)  
const onTouchMove = e => { if (dragMode) { e.preventDefault(); applyDrag(e.touches[0].clientX, e.touches[0].clientY) } }
onMounted(() => {  
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', stopDrag)
  window.addEventListener('touchmove', onTouchMove, { passive: false })  
  window.addEventListener('touchend', stopDrag)
})
onUnmounted(() => {  
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mouseup', stopDrag)
  window.removeEventListener('touchmove', onTouchMove)
  window.removeEventListener('touchend', stopDrag)
})
function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)) }  
function confirm() {  
  const nat = imgEl.value  
  const scaleX = nat.naturalWidth / imgW.value  
  const scaleY = nat.naturalHeight / imgH.value  
  const sx = (cropX.value - imgX.value) * scaleX  
  const sy = (cropY.value - imgY.value) * scaleY  
  const sw = cropW.value * scaleX  
  const sh = cropH.value * scaleY  
  const canvas = document.createElement('canvas')  
  if (props.square) {  
    canvas.width = 800; canvas.height = 800
  } else {  
    const MAX = 1200
    const r = sw / sh  
    if (r >= 1) { canvas.width = Math.min(MAX, Math.round(sw)); canvas.height = Math.round(canvas.width / r) }
    else        { canvas.height = Math.min(MAX, Math.round(sh)); canvas.width = Math.round(canvas.height * r) }
  }
  const ctx = canvas.getContext('2d')  
  ctx.drawImage(nat, sx, sy, sw, sh, 0, 0, canvas.width, canvas.height)
  canvas.toBlob(blob => {  
    emit('confirm', new File([blob], 'crop.jpg', { type: 'image/jpeg' }))  
  }, 'image/jpeg', 0.92)  
}
</script>