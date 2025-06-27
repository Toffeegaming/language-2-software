import axios, { type AxiosInstance } from 'axios'
import type { App } from 'vue'

export default {
  async install(app: App) {
    const axiosClient: AxiosInstance = axios.create({
      baseURL: 'http://localhost:7999',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    app.provide('axios', axiosClient)
  },
}
