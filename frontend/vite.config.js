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
          
          // 静态资源文件 - PWA关键资源
          '**/*.{png,svg,ico,woff,woff2,ttf}',
          
          // 应用资源文件
          'manifest.json',
          'offline.html',
          
          // 排除过大的文件
          '!**/*.{mp4,mp3,avi,mov}', // 排除音视频大文件
        ],
        globIgnores: [
          'offline.html', // 在sw.js中手动处理
          '**/*.map', // 排除源码映射文件
        ],
        // 设置缓存文件大小限制
        maximumFileSizeToCacheInBytes: 3 * 1024 * 1024, // 3MB
        // 为预缓存设置特殊规则
        additionalPrecacheEntries: [
          // 手动指定的预缓存资源
          { url: '/', revision: null },
          { url: '/manifest.json', revision: null },
          { url: '/offline.html', revision: null },
          { url: '/favicon.svg', revision: null },
          { url: '/寒蝉半圆体.ttf', revision: null },
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
