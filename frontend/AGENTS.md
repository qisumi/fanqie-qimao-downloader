# FRONTEND

## OVERVIEW

Vue 3 SPA with Naive UI components, Pinia state management, and comprehensive PWA support.

## STRUCTURE

```
frontend/src/
├── api/              # Axios clients (modular by resource)
├── components/       # Reusable UI (PascalCase.vue)
│   ├── reader/       # Reading-specific components
│   └── pwa/          # PWA UI (install, update banners)
├── composables/      # Shared stateful logic (use*.js)
│   └── reader/       # Reader-specific composables
├── stores/           # Pinia stores (Setup Store syntax)
├── views/            # Page components (*View.vue)
├── pwa/              # PWA lifecycle (sw, install, update, offline)
├── router/           # Vue Router config
└── styles/           # CSS variables, global styles
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add page | `views/` → `router/index.js` | Name: `*View.vue` |
| Add component | `components/` | PascalCase, `<script setup>` |
| Shared logic | `composables/` | Prefix: `use*.js` |
| Global state | `stores/` | Setup Store syntax |
| API calls | `api/` | Export individual functions |
| Styling | `styles/variables.css` | Use CSS variables |

## CONVENTIONS

### Components
- **Script setup only**: `<script setup>` for all components
- **Naming**: PascalCase files (`BookCard.vue`, `AppSidebar.vue`)
- **Props**: Minimal prop drilling; prefer stores for shared state
- **Naive UI**: Use layout system (`n-layout`, `n-grid`, `n-card`)

### Stores (Pinia)
```javascript
// Setup Store syntax (NOT Options API)
export const useBookStore = defineStore('book', () => {
  const books = ref([])
  const booksByPlatform = computed(() => /* ... */)
  async function fetchBooks() { /* ... */ }
  return { books, booksByPlatform, fetchBooks }
})
```

### API Layer
```javascript
// api/books.js - Export individual functions
import api from './index'
export function getBook(id) { return api.get(`/api/books/${id}`) }
export function deleteBook(id) { return api.delete(`/api/books/${id}`) }
```

### Composables
- Prefix: `use` (e.g., `useWebSocket.js`, `useAuth.js`)
- For shared stateful logic that doesn't belong in global store
- Reader has suite: `useReaderProgress`, `useReaderChapter`, `useReaderTts`

## PWA FEATURES

- **Service Worker**: Workbox-based caching in `pwa/sw.js`
- **Install prompt**: Custom UI in `components/pwa/`
- **Update notification**: New version detection
- **Offline fallback**: Cached resources + offline page
- **Theme color**: Dynamic via `utils/themeColorManager.js`

## ANTI-PATTERNS

| Avoid | Instead |
|-------|---------|
| Direct API calls in components | Use Pinia store actions |
| Hardcoded colors | Use CSS variables from `variables.css` |
| Complex template logic | Move to `computed` properties |
| Large single components | Extract to composables or sub-components |

## COMMANDS

```bash
npm run dev      # Dev server at :3000 (proxies to backend)
npm run build    # Production build to dist/
npm run preview  # Preview production build
```

## NOTES

- **Responsive**: Mobile-first; drawer on mobile, sider on desktop
- **Build output**: `dist/` served by FastAPI backend
- **No TypeScript**: Pure JavaScript with JSDoc where needed
- **Reader complexity**: `ReaderPageContent.vue` (644 lines) handles touch swipe physics
