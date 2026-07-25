<script setup lang="ts">
/**
 * ReactivatePlanModal — closed → draft. Shows the previous closure
 * date + reason for context.
 */

const props = defineProps<{
  open: boolean
  loading?: boolean
  closedAt?: string | null
  previousReason?: string | null
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  confirm: []
  cancel: []
}>()

const { t, locale } = useI18n()

const formattedDate = computed(() => {
  if (!props.closedAt) return '—'
  try {
    return new Date(props.closedAt).toLocaleDateString(locale.value, {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    })
  } catch {
    return props.closedAt
  }
})

const reasonLabel = computed(() => {
  if (!props.previousReason) return '—'
  return t(`treatmentPlans.closureReason.${props.previousReason}`)
})
</script>

<template>
  <UModal :open="open" @update:open="(v) => emit('update:open', v)">
    <template #content>
      <UCard :ui="{ root: 'max-h-[90vh] flex flex-col', header: { base: 'shrink-0' }, body: 'flex-1 min-h-0 overflow-y-auto', footer: { base: 'shrink-0' } }">
        <template #header>
          <h2 class="text-lg font-semibold">
            {{ t('treatmentPlans.modals.reactivate.title') }}
          </h2>
        </template>

        <p class="text-sm">
          {{
            t('treatmentPlans.modals.reactivate.description', {
              date: formattedDate,
              reason: reasonLabel,
            })
          }}
        </p>

        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton color="neutral" variant="ghost" :disabled="loading" @click="emit('cancel')">
              {{ t('common.cancel') }}
            </UButton>
            <UButton color="primary" :loading="loading" @click="emit('confirm')">
              {{ t('treatmentPlans.modals.reactivate.submit') }}
            </UButton>
          </div>
        </template>
      </UCard>
    </template>
  </UModal>
</template>
