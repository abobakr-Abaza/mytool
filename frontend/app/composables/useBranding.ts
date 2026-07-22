export interface BrandingData {
  logo_url: string | null
  favicon_url: string | null
  primary_color: string | null
  secondary_color: string | null
  accent_color: string | null
  portal_title: string | null
  custom_css: string | null
}

export function useBranding() {
  const branding = useState<BrandingData | null>('branding:data', () => null)
  const loading = useState<boolean>('branding:loading', () => false)

  async function fetchBranding(): Promise<void> {
    if (loading.value) return
    loading.value = true
    try {
      const response = await $fetch<{ data: BrandingData }>('/api/v1/branding', {
        headers: {
          'X-Tenant-Domain': window.location.hostname
        }
      })
      branding.value = response.data
      applyBranding(response.data)
    } catch {
      branding.value = null
    } finally {
      loading.value = false
    }
  }

  function applyBranding(b: BrandingData): void {
    const root = document.documentElement

    if (b.primary_color) {
      root.style.setProperty('--brand-primary', b.primary_color)
    }
    if (b.secondary_color) {
      root.style.setProperty('--brand-secondary', b.secondary_color)
    }
    if (b.accent_color) {
      root.style.setProperty('--brand-accent', b.accent_color)
    }
    if (b.favicon_url) {
      let link = document.querySelector<HTMLLinkElement>('link[rel="icon"]')
      if (!link) {
        link = document.createElement('link')
        link.rel = 'icon'
        document.head.appendChild(link)
      }
      link.href = b.favicon_url
    }
    if (b.portal_title) {
      document.title = b.portal_title
    }
    if (b.custom_css) {
      let style = document.querySelector<HTMLStyleElement>('#brand-custom-css')
      if (!style) {
        style = document.createElement('style')
        style.id = 'brand-custom-css'
        document.head.appendChild(style)
      }
      style.textContent = b.custom_css
    }
  }

  return {
    branding: readonly(branding),
    loading: readonly(loading),
    fetchBranding,
    applyBranding
  }
}
