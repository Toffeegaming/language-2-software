import './assets/main.css'
import axiosPlugin from '@/plugins/axios'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(router).use(createPinia()).use(axiosPlugin)

app.mount('#app')
