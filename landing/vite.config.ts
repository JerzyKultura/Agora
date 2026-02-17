import { defineConfig, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'

function blockSensitiveFiles(): Plugin {
  return {
    name: 'block-sensitive-files',
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const url = decodeURIComponent(req.url || '').split('?')[0]

        const allowed =
          url === '/' ||
          url === '/index.html' ||
          url.startsWith('/src/') ||
          url.startsWith('/node_modules/') ||
          url.startsWith('/@') ||
          url.startsWith('/api/') ||
          url === '/agora-logo.svg'

        if (!allowed) {
          res.statusCode = 403
          res.end('Forbidden')
          return
        }

        next()
      })
    },
  }
}

export default defineConfig({
  plugins: [blockSensitiveFiles(), react()],
  server: {
    port: 5174,
    proxy: {
      '/api': {
        target: 'http://localhost:3001',
        changeOrigin: true,
      },
    },
  },
})
