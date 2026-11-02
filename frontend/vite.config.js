import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

export default defineConfig(({ mode }) => {
  const isDevelopment = mode === 'development'

  return {
    // The dashboard lives under /dashboard/; the landing page has / (see landing/)
    base: '/dashboard/',
    plugins: [
      // /chat and /share keep their addresses (nginx does the same in production)
      {
        name: 'public-chat-paths',
        configureServer(server) {
          server.middlewares.use((req, res, next) => {
            if (/^\/(chat|share)\//.test(req.url)) req.url = `/dashboard${req.url}`;
            next();
          });
        },
      },
      vue(),
      isDevelopment && vueDevTools(), // Prevents build error on render (because no browser API exists)
    ],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      },
    },
    server: {
      proxy: {
        // Forward /api/* to Flask — same origin, no CORS needed in local dev
        '/api': {
          target: 'http://backend:5000',
          changeOrigin: true,
        },
      },
    },
  }
})