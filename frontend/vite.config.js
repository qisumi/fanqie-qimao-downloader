import { defineConfig } from 'vite'
import { resolve } from 'path'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    vue(),
    VitePWA({
      strategies: 'injectManifest',
      srcDir: 'src',
      filename: 'sw.js',
      outDir: 'dist',
      injectManifest: {
        globDirectory: 'dist',
        globPatterns: [
          // 核心应用文件
          'index.html',
          '**/*.{js,css}',
          
          // 静态资源文件 - PWA关键资源（排除大字体文件）
          '**/*.{png,svg,ico,woff,woff2}',
          
          // 应用资源文件
          'manifest.json',
        ],
        globIgnores: [
          '**/*.map', // 排除源码映射文件
          '**/*.ttf', // 排除大字体文件，改为运行时缓存
        ],
        // 增加缓存文件大小限制以适应更多资源
        maximumFileSizeToCacheInBytes: 5 * 1024 * 1024, // 5MB
        // 为预缓存设置特殊规则
        additionalManifestEntries: [
          // 手动指定的预缓存资源（排除大字体文件）
          { url: '/', revision: null },
          { url: '/manifest.json', revision: null },
          { url: '/offline.html', revision: null },
          { url: '/favicon.svg', revision: null },
          // 字体文件改为运行时缓存，不预缓存
        ]
      },
      manifest: false,
      injectRegister: null,
      // 开发模式启用
      devOptions: {
        enabled: true,
        type: 'module',
        navigateFallback: 'index.html'
      }
    })
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:4568',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://127.0.0.1:4568',
        ws: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
})
