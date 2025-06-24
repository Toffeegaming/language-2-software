<script lang="ts" setup>
import { defineAsyncComponent } from 'vue'

const Chatbox = defineAsyncComponent(() => import('@/components/Chatbox.vue'))
</script>

<template>
  <Chatbox />
</template>
