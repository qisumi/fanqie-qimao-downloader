import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'

// Global styles
import './styles/variables.css'
import './styles/responsive.css'

// PWA modules (optional - can be used later)
// import { PWAInstall } from './pwa/install.js'
// import { PWAUpdate } from './pwa/update.js'
// import { PWAOffline } from './pwa/offline.js'
// import { PWASkeleton } from './pwa/skeleton.js'
// import './styles/pwa.css'

// Create Vue app
const app = createApp(App)

// Use Pinia for state management
const pinia = createPinia()
app.use(pinia)

// Use Vue Router
app.use(router)

// Mount app
app.mount('#app')

// Initialize PWA modules (optional)
// window.pwaInstall = new PWAInstall()
// window.pwaUpdate = new PWAUpdate()
// window.pwaOffline = new PWAOffline()
// window.pwaSkeleton = new PWASkeleton()
