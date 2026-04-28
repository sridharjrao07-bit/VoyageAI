import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    target: 'es2020',
    outDir: 'dist',
    minify: 'esbuild',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          charts: ['chart.js', 'react-chartjs-2'],
          icons: ['react-icons'],
        },
      },
      // suppress Rollup warnings for dynamic imports from chart.js / react-icons
      onwarn(warning, warn) {
        if (warning.code === 'CIRCULAR_DEPENDENCY') return
        warn(warning)
      },
    },
    // Exclude chart.js internals from dynamic import var analysis  
    dynamicImportVarsOptions: {
      exclude: [/chart\.js/, /react-icons/],
      warnOnError: false,
    },
  },
  esbuild: {
    target: 'es2020',
  },
  server: {
    port: 5173,
    proxy: {
      // /auth/* → backend /auth/* (direct passthrough, no rewrite)
      '/auth': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      // /api/* → backend (strips /api prefix so /api/destinations → /destinations)
      // Group routes: /api/groups → /groups, /api/admin → /admin
      '/api': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})

