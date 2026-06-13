import { createPinia } from 'pinia'
import { createApp } from 'vue'

// Глобальні стилі дизайн-системи (порядок: токени → теми → база → класи).
import '@/styles/tokens.css'
import '@/styles/themes.css'
import '@/styles/base.css'
import '@/styles/primitives.css'
import '@/styles/shell.css'
import '@/styles/auth.css'
import '@/styles/data.css'
import '@/styles/calendar.css'

import { setTokenProvider, setUnauthorizedHandler } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'

import App from './App.vue'
import { router } from './router'

const app = createApp(App)
app.use(createPinia())
app.use(router)

// Інстанціюємо ui-store одразу → застосовує data-theme і токени акценту.
useUiStore()

const auth = useAuthStore()

// Джерело токена для клієнта — жива ref зі store (синхронно, без storage).
setTokenProvider(() => auth.token)

// 401 на authed-запиті → очистити сесію (App.vue покаже екран входу).
setUnauthorizedHandler(() => auth.logout())

// Персист поточного маршруту (для відновлення останнього екрана на «/»).
router.afterEach((to) => {
  if (typeof to.name === 'string') useUiStore().setRoute(to.name)
})

// Є збережений токен → підвантажити користувача; невалідний → logout.
if (auth.token) {
  void auth.fetchMe().catch(() => auth.logout())
}

app.mount('#app')
