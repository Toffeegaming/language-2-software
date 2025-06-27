import type { AxiosInstance, AxiosResponse } from 'axios'

/**
 * Singleton ApiClient Class
 * used to get easier logging of API requests
 */
class ApiClient {
  static #instance: ApiClient

  private constructor() {}

  public static get Instance(): ApiClient {
    if (!ApiClient.#instance) {
      ApiClient.#instance = new ApiClient()
    }
    return ApiClient.#instance
  }

  async get<T = any>(axios: AxiosInstance, endpoint: string): Promise<AxiosResponse<T>> {
    return await axios.get<T>(endpoint)
  }

  async post<T = any>(
    axios: AxiosInstance,
    endpoint: string,
    data: any,
  ): Promise<AxiosResponse<T>> {
    return await axios.post<T>(endpoint, data)
  }

  async put<T = any>(axios: AxiosInstance, endpoint: string, data: any): Promise<AxiosResponse<T>> {
    return await axios.put<T>(endpoint, data)
  }

  async delete<T = any>(axios: AxiosInstance, endpoint: string): Promise<AxiosResponse<T>> {
    return await axios.delete<T>(endpoint)
  }
}

export const useApiClient = () => ({
  // Version
  async getModels(axios: AxiosInstance) {
    const response = await ApiClient.Instance.get(axios, '/models')
    return response.data.available_models
  },

  async postQuestion(axios: AxiosInstance, question: string) {
    const response = await ApiClient.Instance.post(axios, '/route', { text: question })
    console.log('Response from API:', response)
    return response.data
  },
})
