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
  // const axios = inject<AxiosInstance>('axios')

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
    try {
      if (!newMessage.value.trim() || isTyping.value) return

      isTyping.value = true

      // if (!axios) {
      //   throw new Error('Axios unavailable')
      // }

      const messageText = newMessage.value.trim()
      addMessage(messageText, 'user')
      newMessage.value = ''

      const { postQuestion } = useApiClient()

      const botMessage = await postQuestion(axios, messageText)

      addMessage(botMessage, 'bot')
    } catch {
      addMessage('Er ging iets mis, probeer het later opnieuw', 'bot')
    } finally {
      isTyping.value = false
    }
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
    sendMessage,
    availableModels,
    getModels,
  }
})
