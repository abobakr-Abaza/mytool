// https://nuxt.com/docs/api/configuration/nuxt-config
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

/**
 * Load Nuxt Layer paths from `modules.json`.
 *
 * The backend writes this file whenever a module with a declared
 * `manifest.frontend.layer_path` is installed. When absent (fresh
 * checkout, no community modules yet), returns an empty array.
 */
function loadModuleLayers(): string[] {
  const path = resolve(__dirname, 'modules.json')
  try {
    const raw = readFileSync(path, 'utf-8')
    const payload = JSON.parse(raw) as { layers?: string[] }
    return Array.isArray(payload.layers) ? payload.layers : []
  } catch (err: unknown) {
    const code = (err as { code?: string }).code
    if (code !== 'ENOENT') {
      console.warn('[nuxt.config] modules.json is malformed, using empty layers:', err)
    }
    return []
  }
}

const moduleLayers = loadModuleLayers()
const modulesJsonPath = resolve(__dirname, 'modules.json')

export default defineNuxtConfig({

  extends: moduleLayers,

  modules: [
    '@nuxt/eslint',
    '@nuxt/ui',
    '@nuxtjs/i18n',
    '@vite-pwa/nuxt'
  ],

  components: [
    {
      path: '~/components',
      pathPrefix: false
    }
  ],

  devtools: {
    enabled: true
  },
  app: {
    head: {
      title: 'LaminarDent',
      link: [
        { rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' }
      ]
    }
  },

  css: ['~/assets/css/main.css'],

  // Default to light mode; users can opt into dark via the toggle. Both
  // ``preference`` and ``fallback`` are set so SSR + first-paint render
  // light without a flash even before client hydration reads OS prefs.
  colorMode: {
    preference: 'light',
    fallback: 'light'
  },

  runtimeConfig: {
    // Server-side only (for SSR inside Docker)
    apiBaseUrlServer: process.env.API_BASE_URL_SERVER || 'http://backend:8000',
    public: {
      // Client-side (browser) — empty = same origin; dev proxy forwards to backend
      apiBaseUrl: process.env.API_BASE_URL || '',
      demoMode: process.env.NUXT_PUBLIC_DEMO_MODE === 'true',
      // Documentation portal origin used by the in-app help drawer
      // (Fase 5 of issue #75). Empty disables the help button.
      docsUrl: process.env.NUXT_PUBLIC_DOCS_URL || 'https://docs.dentalpin.com'
    }
  },
  srcDir: 'app',

  // Restart dev server when the backend rewrites `modules.json` on
  // module install/uninstall. `extends` is evaluated once at config
  // boot, so a layer added after Nuxt started is invisible until
  // restart. Watching the file makes the round-trip automatic.
  watch: [modulesJsonPath],

  compatibilityDate: '2025-01-15',

  nitro: {
    devProxy: {
      '/api': {
        target: process.env.API_PROXY_TARGET || 'http://backend:8000',
        changeOrigin: true
      }
    }
  },

  vite: {
    optimizeDeps: {
      // Pre-bundle deps that Vite otherwise discovers at runtime. Runtime
      // discovery triggers a full page reload, which in CI races Playwright's
      // `goto` and causes net::ERR_ABORTED on the very first visit to any
      // route that uses these packages.
      include: [
        'nprogress',
        '@vueuse/core',
        '@vue/devtools-core',
        '@vue/devtools-kit'
      ]
    }
  },

  eslint: {
    config: {
      stylistic: {
        commaDangle: 'never',
        braceStyle: '1tbs'
      }
    }
  },

  i18n: {
    locales: [
      { code: 'ar', name: 'العربية', file: 'ar.json', dir: 'rtl' },
      { code: 'en', name: 'English', file: 'en.json', dir: 'ltr' }
    ],
    defaultLocale: 'ar',
    lazy: true,
    langDir: 'locales',
    strategy: 'no_prefix',
    compilation: {
      strictMessage: false,
      escapeHtml: true
    },
    detectBrowserLanguage: { useCookie: true, cookieKey: 'i18n_locale', alwaysRedirect: false, fallbackLocale: 'ar' }
  },

  pwa: {
    registerType: 'autoUpdate',
    includeAssets: ['favicon.svg'],
    manifest: {
      name: 'DentalPin',
      short_name: 'DentalPin',
      description: 'Clinic management made simple',
      theme_color: '#0F172A',
      background_color: '#FFFFFF',
      display: 'standalone',
      orientation: 'portrait-primary',
      lang: 'ar',
      dir: 'rtl',
      icons: [
        { src: '/pwa-192x192.png', sizes: '192x192', type: 'image/png' },
        { src: '/pwa-512x512.png', sizes: '512x512', type: 'image/png' },
        { src: '/pwa-512x512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' }
      ]
    },
    workbox: {
      globPatterns: ['**/*.{js,css,html,svg,png,ico,woff2}'],
      runtimeCaching: [
        {
          urlPattern: /^https?:\/\/.*\/api\/v1\//,
          handler: 'NetworkFirst',
          method: 'GET',
          options: {
            cacheName: 'api-cache',
            expiration: { maxEntries: 100, maxAgeSeconds: 60 * 60 },
            cacheableResponse: { statuses: [200] }
          }
        }
      ]
    },
    client: {
      installPrompt: true,
      periodicSyncForUpdates: 3600
    }
  },

  // Pre-bundle every `i-lucide-*` icon referenced in source into the client
  // bundle. Without this, @nuxt/icon fetches icons lazily per-name on client
  // navigation, which causes the sidebar to briefly render a stale / wrong
  // icon (e.g. the settings cog showing up next to "Pacientes") until the
  // real icon resolves.
  icon: {
    clientBundle: {
      scan: true,
      sizeLimitKb: 512
    }
  }
})
