<template>
  <span>
    <template v-for="(part, i) in parts" :key="i">
      <router-link v-if="part.type === 'mention'" :to="'/user/' + part.value" class="mention">@{{ part.value }}</router-link>
      <router-link v-else-if="part.type === 'tag'" :to="'/tag/' + part.value.toLowerCase()" class="tag-inline">#{{ part.value }}</router-link>
      <span v-else>{{ part.value }}</span>
    </template>
  </span>
</template>
<script setup>
import { computed } from 'vue'  
const props = defineProps({ text: { type: String, default: '' } })  
const parts = computed(() => {  
  if (!props.text) return []  
  const result = []  
  const regex = /(@\w+|#\w+)/gu  
  let last = 0, m  
  while ((m = regex.exec(props.text)) !== null) {  
    if (m.index > last) result.push({ type: 'text', value: props.text.slice(last, m.index) })  
    if (m[0][0] === '@') result.push({ type: 'mention', value: m[0].slice(1) })  
    else result.push({ type: 'tag', value: m[0].slice(1) })  
    last = m.index + m[0].length  
  }
  if (last < props.text.length) result.push({ type: 'text', value: props.text.slice(last) })  
  return result  
})
</script>