<script setup lang="ts">
import type { Alert } from '../composables/useInventory'

const props = defineProps<{
  alerts: Alert[]
  loading?: boolean
}>()

const emit = defineEmits<{
  navigate: [itemId: string]
}>()

const { t } = useI18n()
</script>

<template>
  <div class="space-y-2">
    <div v-if="loading" class="flex items-center gap-2 text-subtle p-4">
      <UIcon name="i-lucide-loader-2" class="w-4 h-4 animate-spin" />
      <span class="text-sm">{{ t('inventory.loading') }}</span>
    </div>
    <template v-else-if="alerts.length === 0">
      <div class="text-center py-6 text-subtle">
        <UIcon name="i-lucide-check-circle-2" class="w-8 h-8 mx-auto mb-2 text-green-500" />
        <p class="text-sm">{{ t('inventory.allStocked') }}</p>
      </div>
    </template>
    <template v-else>
      <div
        v-for="alert in alerts"
        :key="alert.item_id"
        class="flex items-center justify-between p-3 rounded-lg border border-warning/20 bg-warning/5 cursor-pointer hover:bg-warning/10 transition-colors"
        @click="emit('navigate', alert.item_id)"
      >
        <div class="min-w-0 flex-1">
          <p class="text-sm font-medium truncate">{{ alert.item_name }}</p>
          <p v-if="alert.category_name" class="text-xs text-subtle">{{ alert.category_name }}</p>
        </div>
        <div class="text-right flex-shrink-0 ml-3">
          <p class="text-sm font-semibold text-warning">{{ alert.quantity }} / {{ alert.min_stock }}</p>
          <p class="text-xs text-subtle">{{ t('inventory.minStock') }}</p>
        </div>
      </div>
    </template>
  </div>
</template>
