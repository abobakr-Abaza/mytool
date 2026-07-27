export function useOnlineStatus() {
  const isOnline = ref(true)
  const wasOffline = ref(false)

  function handleOnline() {
    isOnline.value = true
    wasOffline.value = true
  }

  function handleOffline() {
    isOnline.value = false
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

  return { isOnline, wasOffline }
}
