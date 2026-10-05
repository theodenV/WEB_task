<template>
  <p v-if="loading">Загрузка...</p>
  <p v-else-if="error" class="error">{{ error }}</p>
  <div v-else>
    <div class="board-head">  
      <template v-if="editing">  
        <input v-model="editName" class="board-edit-input">
        <label class="board-edit-public">
          <input type="checkbox" v-model="editPublic"> Публичная
        </label>
        <div class="board-edit-actions">
          <button class="btn" :disabled="saving" @click="saveEdit">{{ saving ? 'Сохраняю...' : 'Сохранить' }}</button>
          <button class="btn-outline" @click="editing = false">Отмена</button>
        </div>
      </template>
      <template v-else>  
        <h1>{{ collection.name }}</h1>
        <p class="board-sub">{{ collection.is_public ? 'Общая доска' : 'Приватная доска' }} · {{ collection.posts.length }} пинов · @{{ collection.owner }}</p>
        <div v-if="isOwner" class="board-owner-actions">  
          <button class="btn-outline" style="margin-top:12px" @click="startEdit">Изменить</button>
          <button class="btn-outline btn-danger" style="margin-top:12px" @click="remove">Удалить доску</button>
        </div>
      </template>
    </div>
    <div class="masonry">
      <div v-for="post in collection.posts" :key="post.id" class="pin">
        <router-link :to="'/post/' + post.id" class="card">
          <img :src="post.image" alt="" loading="lazy">
        </router-link>
        <button v-if="isOwner" class="pin-del" title="Убрать из коллекции" @click="removePost(post.id)">✕</button>
      </div>
    </div>
    <p v-if="collection.posts.length === 0">В коллекции пока нет постов.</p>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'
import { auth } from '../auth'
import { showConfirm } from '../confirm'
import { toastSuccess, toastError } from '../toast'
const route = useRoute()
const router = useRouter()
const collection = ref(null)  
const loading = ref(true)
const error = ref(null)
const editing = ref(false)  
const editName = ref('')  
const editPublic = ref(false)  
const saving = ref(false)  
const isOwner = computed(() =>
  collection.value && auth.user && collection.value.owner === auth.user.username
)
onMounted(async () => {
  try {
    collection.value = await api('/api/collections/' + route.params.id + '/')  
  } catch {
    error.value = 'Не удалось загрузить (возможно, коллекция приватная)'
  } finally {
    loading.value = false
  }
})
function startEdit() {  
  editName.value = collection.value.name
  editPublic.value = collection.value.is_public
  editing.value = true
}
async function saveEdit() {  
  if (!editName.value.trim()) return
  saving.value = true
  try {
    const updated = await api('/api/collections/' + collection.value.id + '/', {  
      method: 'PATCH',
      body: JSON.stringify({ name: editName.value, is_public: editPublic.value }),
    })
    collection.value.name = updated.name  
    collection.value.is_public = updated.is_public
    editing.value = false
    toastSuccess('Доска обновлена')
  } catch {
    toastError('Не удалось сохранить')
  } finally {
    saving.value = false
  }
}
async function removePost(postId) {  
  if (!(await showConfirm('Убрать пост из коллекции?'))) return
  await api('/api/collections/' + collection.value.id + '/add/', {
    method: 'DELETE',  
    body: JSON.stringify({ post: postId }),
  })
  collection.value.posts = collection.value.posts.filter(p => p.id !== postId)  
  toastSuccess('Убрано из коллекции')
}
async function remove() {  
  if (!(await showConfirm('Удалить эту доску? Сами посты не удалятся.'))) return
  try {
    await api('/api/collections/' + collection.value.id + '/', { method: 'DELETE' })
    toastSuccess('Доска удалена')
    router.push('/collections')  
  } catch {
    toastError('Не удалось удалить доску')
  }
}
</script>