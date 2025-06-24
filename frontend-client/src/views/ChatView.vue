<script setup lang="ts">
import {useChatStore} from '@/stores/Chat.ts'
import {onMounted} from 'vue'

const chatStore = useChatStore()

onMounted(() => {
  chatStore.getModels()
})
</script>

<template>
  <p>The available models are {{chatStore.availableModels}}</p>
</template>