<script setup lang="ts">
import { en } from '@nuxt/ui/locale'

const { t, locale } = useI18n()
const { branding, fetchBranding } = useBranding()

const nuxtUILocale = computed(() => en)

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
    lang: locale.value
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
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
  </UApp>
</template>
