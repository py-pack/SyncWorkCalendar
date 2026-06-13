import { fileURLToPath, URL } from 'node:url'

import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

// Dev-сервер розрахований на доступ через host-nginx (кастомні домени
// sync.loc / sync.dev) АБО напряму через localhost:10332.
//
// - VITE_API_PROXY_TARGET — ціль Vite-проксі для /api (фолбек на випадок
//   прямого :10332; за nginx маршрут /api обробляє сам nginx).
// - VITE_USE_POLLING — увімкнути polling файлвотчингу (потрібно в Docker
//   bind-mount на macOS, інакше HMR не реагує на зміни).
// - HMR за реверс-проксі задається ДВОМА змінними:
//     VITE_HMR_HOST   — домен (напр. sync.dev). Без нього — дефолт Vite
//                       (прямий localhost), HMR-override не вмикається.
//     VITE_HMR_HTTPS  — "true"/"false": з нього виводяться protocol (wss/ws)
//                       і clientPort (443/80).
//   Опційно можна перевизначити явно: VITE_HMR_PROTOCOL, VITE_HMR_CLIENT_PORT.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '')

  const proxyTarget = env.VITE_API_PROXY_TARGET || 'http://localhost:10331'
  const port = Number(env.VITE_PORT) || 10332
  const usePolling = env.VITE_USE_POLLING === 'true' || env.VITE_USE_POLLING === '1'

  const hmrHttps = env.VITE_HMR_HTTPS === 'true' || env.VITE_HMR_HTTPS === '1'
  const hmr = env.VITE_HMR_HOST
    ? {
        host: env.VITE_HMR_HOST,
        protocol: env.VITE_HMR_PROTOCOL || (hmrHttps ? 'wss' : 'ws'),
        clientPort: Number(env.VITE_HMR_CLIENT_PORT) || (hmrHttps ? 443 : 80),
      }
    : undefined

  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    server: {
      host: true,
      port,
      strictPort: true,
      // дозволяємо кастомні локальні домени (інакше Vite блокує Host)
      allowedHosts: ['sync.loc', 'sync.dev', 'localhost'],
      watch: usePolling ? { usePolling: true } : undefined,
      hmr,
      proxy: {
        '/api': {
          target: proxyTarget,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
      },
    },
  }
})
