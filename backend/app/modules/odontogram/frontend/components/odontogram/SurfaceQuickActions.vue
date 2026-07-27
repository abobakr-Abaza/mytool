<script setup lang="ts">
import type { Surface } from '~~/app/types'

const props = defineProps<{
  selectedSurfaces: Surface[]
  disabled?: boolean
  compact?: boolean
}>()

const emit = defineEmits<{
  toggle: [surface: Surface]
  clear: []
}>()

const { t } = useI18n()

const allSurfaces: Surface[] = ['M', 'O', 'D', 'B', 'L']

const surfaceColors: Record<Surface, string> = {
  M: '#3B82F6',
  O: '#10B981',
  D: '#F59E0B',
  B: '#8B5CF6',
  L: '#EF4444'
}

function isSelected(surface: Surface): boolean {
  return props.selectedSurfaces.includes(surface)
}

function handleToggle(surface: Surface) {
  if (!props.disabled) {
    emit('toggle', surface)
  }
}
</script>

<template>
  <div
    class="flex items-center gap-1"
    :class="compact ? 'flex-nowrap' : 'flex-wrap'"
  >
    <button
      v-for="surface in allSurfaces"
      :key="surface"
      type="button"
      :disabled="disabled"
      class="flex items-center justify-center font-semibold rounded-md transition-all duration-150 select-none focus:outline-none focus-visible:ring-2 focus-visible:ring-primary"
      :class="[
        compact ? 'w-7 h-7 text-xs' : 'w-9 h-9 text-sm',
        isSelected(surface)
          ? 'text-white shadow-sm'
          : 'text-muted hover:text-default hover:bg-surface-muted border border-default',
      ]"
      :style="isSelected(surface) ? { backgroundColor: surfaceColors[surface], borderColor: surfaceColors[surface] } : {}"
      :title="t(`odontogram.surfaces.${surface}`)"
      @click="handleToggle(surface)"
    >
      {{ surface }}
    </button>
    <button
      v-if="selectedSurfaces.length > 0"
      type="button"
      class="flex items-center justify-center w-7 h-7 text-xs text-subtle hover:text-danger rounded-md hover:bg-danger/10 transition-colors focus:outline-none"
      :title="t('common.clear')"
      @click="emit('clear')"
    >
      <UIcon name="i-lucide-x" class="w-3.5 h-3.5" />
    </button>
  </div>
</template>
