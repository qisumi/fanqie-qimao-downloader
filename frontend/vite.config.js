import { defineConfig } from 'vite';
import { resolve } from 'path';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  build: {
    outDir: '../app/web/static',
    emptyOutDir: false,
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'src/main.js'),
      },
      output: {
        entryFileNames: '[name].js',
        assetFileNames: 'assets/[name].[ext]',
        chunkFileNames: 'chunks/[name].[hash].js'
      }
    }
  },
  plugins: [
    VitePWA({
      strategies: 'injectManifest',
      srcDir: 'src',
      filename: 'sw.js',
      outDir: '../app/web/static',
      injectManifest: {
        globDirectory: '../app/web/static',
        globPatterns: [
          'main.js',
          'assets/*.css',
          'images/*.{png,svg}',
          'manifest.json'
        ],
        // We can refine globPatterns to only include what we want to precache
      },
      manifest: false, // We manage manifest.json manually in public/
      injectRegister: null, // We register SW manually in base.html
      devOptions: {
        enabled: true
      }
    })
  ]
});
