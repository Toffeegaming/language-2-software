<script lang="ts" setup>
import { defineAsyncComponent, onMounted } from 'vue'
import { useChatStore } from '@/stores/Chat.ts'

const chatStore = useChatStore()

const Chatbox = defineAsyncComponent(() => import('@/components/Chatbox.vue'))

onMounted(() => {
  chatStore.getModels()
})
</script>

<template>
  <Chatbox />
</template>
