export function useOnlineStatus() {
  const isOnline = ref(true)
  const wasOffline = ref(false)
  const hasEverBeenOffline = ref(false)

  function handleOnline() {
    if (hasEverBeenOffline.value) {
      wasOffline.value = true
    }
    isOnline.value = true
  }

  function handleOffline() {
    isOnline.value = false
    hasEverBeenOffline.value = true
  }

  onMounted(() => {
    isOnline.value = navigator.onLine
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
  })

  onUnmounted(() => {
    window.removeEventListener('online', handleOnline)
    window.removeEventListener('offline', handleOffline)
  })

  return { isOnline, wasOffline, hasEverBeenOffline }
}
