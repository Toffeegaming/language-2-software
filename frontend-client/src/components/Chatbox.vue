<script lang="ts" setup>
import { nextTick, onMounted, ref, watch } from 'vue'
import { useChatStore } from '@/stores/Chat.ts'
import { MessageCircle, Moon, Send, Sun } from 'lucide-vue-next'

import markdownit from 'markdown-it'
import hljs from 'highlight.js'
import markdownItTextualUml from 'markdown-it-textual-uml'
import mermaid from 'mermaid'

mermaid.initialize({ startOnLoad: false, theme: 'neutral' })

const markdown = new markdownit({
  html: true,
  breaks: true,
  linkify: true,
  typographer: true,
  highlight: function (str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(str, { language: lang }).value
      } catch (__) {}
    }

    return '' // use external default escaping
  },
}).use(markdownItTextualUml)

const renderMessage = (message: string) => {
  // replace \\n with \n
  message = message.replace(/\\n/g, '\n')

  // replace escaped " characters with actual quotes
  message = message.replace(/\\\"/g, '"')

  // render the markdown content
  return markdown.render(message || 'Bericht')
}

const chatStore = useChatStore()

const messagesContainer = ref<HTMLElement>()
const isDark = ref(false)

const formatTime = (timestamp: Date) => {
  return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const toggleTheme = () => {
  isDark.value = !isDark.value
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
  document.documentElement.classList.toggle('dark', isDark.value)
}

// Initialize theme
onMounted(async () => {
  const savedTheme = localStorage.getItem('theme')
  const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches

  isDark.value = savedTheme ? savedTheme === 'dark' : systemPrefersDark
  document.documentElement.classList.toggle('dark', isDark.value)
})

// Watch for new messages and scroll to bottom
watch(
  chatStore.messages,
  async () => {
    await nextTick()
    await mermaid.run()
    scrollToBottom()
  },
  { deep: true },
)
</script>

<template>
  <div :class="{ dark: isDark }" class="chat-app">
    <!-- Header -->
    <div class="chat-header">
      <div class="header-content">
        <div class="header-info">
          <div class="avatar">
            <MessageCircle class="avatar-icon" />
          </div>
          <div class="header-text">
            <h1 class="header-title">Language 2 Software</h1>
            <p class="header-subtitle">Voor al je oplossingen op basis van een metamodel.</p>
          </div>
        </div>
        <button class="theme-toggle" @click="toggleTheme">
          <Sun v-if="isDark" class="theme-icon" />
          <Moon v-else class="theme-icon" />
        </button>
      </div>
    </div>

    <!-- Messages Container -->
    <div ref="messagesContainer" class="messages-container">
      <div class="messages-wrapper">
        <div
          v-for="message in chatStore.messages"
          :key="message.id"
          :class="['message', message.sender === 'user' ? 'user-message' : 'bot-message']"
        >
          <div class="message-content">
            <p class="message-text" v-html="renderMessage(message.text)" />
            <span class="message-time">{{ formatTime(message.timestamp) }}</span>
          </div>
        </div>

        <div v-if="chatStore.isTyping" class="typing-indicator">
          <div class="typing-content">
            <span class="typing-text">Ik ben aan het nadenken</span>
            <div class="typing-dots">
              <span class="dot"></span>
              <span class="dot"></span>
              <span class="dot"></span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Input Form -->
    <div class="input-container">
      <div class="input-wrapper">
        <form class="message-form" @submit.prevent="chatStore.sendMessage">
          <input
            v-model="chatStore.newMessage"
            :disabled="chatStore.isTyping"
            class="message-input"
            placeholder="Type your message..."
            type="text"
          />
          <button
            :disabled="!chatStore.newMessage.trim() || chatStore.isTyping"
            class="send-button"
            type="submit"
          >
            <Send class="send-icon" />
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  position: fixed;
  top: 0;
  left: 0;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  transition: all 0.3s ease;
  margin: 0;
  padding: 0;
  overflow: hidden;
}

.chat-app.dark {
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
}

/* Header Styles */
.chat-header {
  background: white;
  border-bottom: 1px solid #e5e7eb;
  padding: 1.5rem 2rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.dark .chat-header {
  background: #111827;
  border-bottom-color: #374151;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  margin: 0;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.avatar {
  width: 2.5rem;
  height: 2.5rem;
  background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-icon {
  width: 1.25rem;
  height: 1.25rem;
  color: white;
}

.header-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #111827;
  margin: 0;
  transition: color 0.3s ease;
}

.dark .header-title {
  color: #f9fafb;
}

.header-subtitle {
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0;
  transition: color 0.3s ease;
}

.dark .header-subtitle {
  color: #9ca3af;
}

.theme-toggle {
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 50%;
  border: none;
  background: #f3f4f6;
  color: #374151;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.theme-toggle:hover {
  background: #e5e7eb;
  transform: scale(1.05);
}

.dark .theme-toggle {
  background: #374151;
  color: #d1d5db;
}

.dark .theme-toggle:hover {
  background: #4b5563;
}

.theme-icon {
  width: 1rem;
  height: 1rem;
}

/* Messages Container */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
}

.messages-container::-webkit-scrollbar {
  width: 6px;
}

.messages-container::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}

.dark .messages-container::-webkit-scrollbar-track {
  background: #1e293b;
}

.messages-container::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.dark .messages-container::-webkit-scrollbar-thumb {
  background: #475569;
}

.messages-wrapper {
  width: 100%;
  margin: 0;
  display: flex;
  flex-direction: column;
}

.message {
  display: flex;
  margin-bottom: 1rem;
  width: 100%;
}

.user-message {
  justify-content: flex-end;
}

.bot-message {
  justify-content: flex-start;
}

.message-content {
  padding: 0.75rem 1rem;
  border-radius: 1.125rem;
  word-wrap: break-word;
  transition: all 0.3s ease;
  max-width: 90%;
}

.user-message .message-content {
  background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
  color: white;
  border-bottom-right-radius: 0.25rem;
}

.bot-message .message-content {
  background: #e3e3e3;
  color: #1e293b;
  border-bottom-left-radius: 0.25rem;
}

.dark .bot-message .message-content {
  background: #1e293b;
  color: #f1f5f9;
}

.message-text {
  margin: 0 0 0.25rem 0;
  line-height: 1.4;
  font-size: 0.875rem;
}

.message-time {
  font-size: 0.6875rem;
  opacity: 0.7;
}

/* Typing Indicator */
.typing-indicator {
  display: flex;
  margin-bottom: 1rem;
  max-width: 70%;
}

.typing-content {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: #f1f5f9;
  border-radius: 1.125rem;
  border-bottom-left-radius: 0.25rem;
}

.dark .typing-content {
  background: #1e293b;
}

.typing-dots {
  display: flex;
  gap: 0.1875rem;
}

.dot {
  width: 0.375rem;
  height: 0.375rem;
  background: #94a3b8;
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out;
}

.dark .dot {
  background: #64748b;
}

.dot:nth-child(1) {
  animation-delay: -0.32s;
}

.dot:nth-child(2) {
  animation-delay: -0.16s;
}

.typing-text {
  font-size: 0.75rem;
  color: #64748b;
}

.dark .typing-text {
  color: #94a3b8;
}

@keyframes typing {
  0%,
  80%,
  100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

/* Input Container */
.input-container {
  background: white;
  border-top: 1px solid #e5e7eb;
  padding: 1.5rem 2rem;
  transition: all 0.3s ease;
}

.dark .input-container {
  background: #111827;
  border-top-color: #374151;
}

.input-wrapper {
  width: 100%;
  margin: 0;
}

.message-form {
  display: flex;
  gap: 1rem;
}

.message-input {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 1.5rem;
  outline: none;
  font-size: 0.875rem;
  background: white;
  color: #111827;
  transition: all 0.3s ease;
}

.message-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.message-input:disabled {
  background: #f9fafb;
  cursor: not-allowed;
  opacity: 0.6;
}

.dark .message-input {
  background: #1f2937;
  border-color: #4b5563;
  color: #f9fafb;
}

.dark .message-input::placeholder {
  color: #9ca3af;
}

.dark .message-input:disabled {
  background: #111827;
}

.send-button {
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
  color: white;
  border: none;
  border-radius: 1.5rem;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.send-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.send-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.send-icon {
  width: 1rem;
  height: 1rem;
}
</style>
