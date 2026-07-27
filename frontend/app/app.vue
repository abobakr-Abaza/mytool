<script setup lang="ts">
import { en } from '@nuxt/ui/locale'

const { t, locale } = useI18n()
const { branding, fetchBranding } = useBranding()

const nuxtUILocale = computed(() => en)

const rtlLocales = ['ar', 'he', 'fa', 'ur']
const dir = computed(() => (rtlLocales.includes(locale.value) ? 'rtl' : 'ltr'))

// Fetch branding on mount (public endpoint, no auth required)
if (import.meta.client) {
  fetchBranding()
}

useHead(() => ({
  meta: [
    { name: 'viewport', content: 'width=device-width, initial-scale=1' }
  ],
  link: [
    { rel: 'icon', href: '/favicon.ico' }
  ],
  htmlAttrs: {
    lang: () => locale.value,
    dir: () => dir.value
  },
  title: computed(() => branding.value?.portal_title || 'LaminarDent')
}))

useSeoMeta({
  title: () => branding.value?.portal_title || 'LaminarDent',
  description: t('app.tagline')
})
</script>

<template>
  <UApp :locale="nuxtUILocale">
    <div :dir="dir" class="min-h-screen">
      <NuxtLayout>
        <NuxtPage />
      </NuxtLayout>
    </div>
  </UApp>
</template>
