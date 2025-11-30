# Frontend Development

This directory contains the source code for the frontend assets (PWA, Service Worker, Styles).

## Directory Structure

- `src/`
  - `main.js`: Entry point for the frontend application.
  - `sw.js`: Service Worker source code (using Workbox).
  - `pwa/`: PWA related modules (Install, Update, Offline, Skeleton).
  - `styles/`: CSS source files.
- `public/`: Static assets that are copied to the output directory (e.g., manifest.json).
- `vite.config.js`: Vite configuration file.

## Development

1. Install dependencies:
   ```bash
   npm install
   ```

2. Build for production:
   ```bash
   npm run build
   ```
   The output files will be generated in `../app/web/static/`.

3. Watch mode (for development):
   ```bash
   npm run build -- --watch
   ```

## PWA Features

- **Service Worker**: Caching strategies for static resources, images, API requests, and pages.
- **Install Prompt**: Custom installation UI.
- **Update Notification**: Notifies users when a new version is available.
- **Offline Support**: Offline fallback page and cached resources.
- **Skeleton Screens**: Loading placeholders for better UX.
