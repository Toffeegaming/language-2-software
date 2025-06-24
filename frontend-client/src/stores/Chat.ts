import { inject, ref, computed } from 'vue'
import { type AxiosInstance } from "axios";
import { useApiClient } from "@/services/apiClient";
import { defineStore } from 'pinia'

export const useChatStore = defineStore('chat', () => {
  const axios = inject<AxiosInstance>("axios");

  const availableModels = ref<string[]>([])

  const getModels = async () => {
    try {
      if (!axios) {
        throw new Error("Axios unavailable");
      }

      const { getModels } = useApiClient();

      const models = await getModels(
        axios,
      );

      console.log("Available models:", models);

      availableModels.value = models;
    } catch (error) {
      console.error("Failed to get available models:", error);
      availableModels.value = [];
    }
  };

  return { availableModels, getModels }
})
