import { PWAInstall } from './pwa/install.js';
import { PWAUpdate } from './pwa/update.js';
import { PWAOffline } from './pwa/offline.js';
import { PWASkeleton } from './pwa/skeleton.js';
import './styles/pwa.css';

// Initialize PWA modules
window.pwaInstall = new PWAInstall();
window.pwaUpdate = new PWAUpdate();
window.pwaOffline = new PWAOffline();
window.pwaSkeleton = new PWASkeleton();
