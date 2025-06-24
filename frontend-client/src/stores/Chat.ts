import { inject, ref } from 'vue'
import { type AxiosInstance } from 'axios'
import { useApiClient } from '@/services/apiClient'
import { defineStore } from 'pinia'

interface Message {
  id: string
  text: string
  sender: 'user' | 'bot'
  timestamp: Date
}

export const useChatStore = defineStore('chat', () => {
  const axios = inject<AxiosInstance>('axios')

  const newMessage = ref('')
  const messages = ref<Message[]>([
    {
      id: '1',
      text: 'Hoi! Wat kan ik voor je doen?',
      sender: 'bot',
      timestamp: new Date(),
    },
  ])

  const isTyping = ref(false)

  const sendMessage = async () => {
    if (!newMessage.value.trim() || isTyping.value) return

    const messageText = newMessage.value.trim()
    addMessage(messageText, 'user')
    newMessage.value = ''

    await simulateBotResponse(messageText)
  }

  function addMessage(text: string, sender: 'user' | 'bot') {
    const message: Message = {
      id: Date.now().toString(),
      text,
      sender,
      timestamp: new Date(),
    }
    messages.value.push(message)
  }

  const simulateBotResponse = async (userMessage: string) => {
    isTyping.value = true

    // Simulate thinking time
    await new Promise((resolve) => setTimeout(resolve, 1000 + Math.random() * 2000))

    // Simple bot responses
    const responses = [
      "That's interesting! Tell me more.",
      'I understand. How can I help you with that?',
      'Thanks for sharing that with me.',
      'Let me think about that for a moment...',
      "That's a great question! Here's what I think...",
    ]

    const randomResponse = responses[Math.floor(Math.random() * responses.length)]

    addMessage(randomResponse, 'bot')
    isTyping.value = false
  }

  const availableModels = ref<string[]>([])

  const getModels = async () => {
    try {
      isTyping.value = true
      if (!axios) {
        throw new Error('Axios unavailable')
      }

      const { getModels } = useApiClient()

      const models = await getModels(axios)

      console.log('Available models:', models)

      availableModels.value = models
    } catch (error) {
      console.error('Failed to get available models:', error)
      availableModels.value = []
    } finally {
      isTyping.value = false
    }
  }

  return {
    newMessage,
    messages,
    isTyping,
    simulateBotResponse,
    sendMessage,
    availableModels,
    getModels,
  }
})
