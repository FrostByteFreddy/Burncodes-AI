import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router' // We will create this file next

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')
