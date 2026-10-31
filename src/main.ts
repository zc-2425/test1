import { createApp } from 'vue'
import { createPinia } from 'pinia'

// 顺序有讲究：先 Vuetify 样式，再图标，最后项目令牌与基础样式，保证令牌能覆盖组件默认值
import vuetify from '@/plugins/vuetify'
import '@mdi/font/css/materialdesignicons.css'
import '@/styles/index.css'

import App from './App.vue'
import router from '@/app/router'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(vuetify)

app.mount('#app')
