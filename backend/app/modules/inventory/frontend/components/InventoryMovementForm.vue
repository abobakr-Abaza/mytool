<script setup lang="ts">
import type { InventoryItem } from '../composables/useInventory'
import { useInventory } from '../composables/useInventory'

const props = defineProps<{
  item: InventoryItem
}>()

const emit = defineEmits<{
  done: []
  cancel: []
}>()

const { t } = useI18n()
const inventory = useInventory()

const movementType = ref<'in' | 'out'>('in')
const quantity = ref(0)
const notes = ref('')
const saving = ref(false)

async function submit() {
  if (quantity.value <= 0) return
  saving.value = true
  try {
    await inventory.recordMovement({
      item_id: props.item.id,
      movement_type: movementType.value,
      quantity: quantity.value,
      notes: notes.value || undefined,
    })
    emit('done')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <form class="space-y-4 p-4" @submit.prevent="submit">
    <div class="text-sm text-subtle mb-2">
      <span class="font-medium">{{ item.name }}</span>
      &mdash; {{ t('inventory.currentStock') }}: <strong>{{ item.quantity }}</strong> {{ item.unit }}
    </div>

    <div class="flex gap-2">
      <UButton
        :color="movementType === 'in' ? 'primary' : 'neutral'"
        variant="solid"
        @click="movementType = 'in'"
      >
        {{ t('inventory.stockIn') }}
      </UButton>
      <UButton
        :color="movementType === 'out' ? 'primary' : 'neutral'"
        variant="solid"
        @click="movementType = 'out'"
      >
        {{ t('inventory.stockOut') }}
      </UButton>
    </div>

    <UFormField :label="t('inventory.quantity')" required>
      <UInput
        v-model.number="quantity"
        type="number"
        min="1"
        :max="movementType === 'out' ? item.quantity : undefined"
        class="w-full"
      />
    </UFormField>

    <UFormField :label="t('inventory.notes')">
      <UTextarea v-model="notes" class="w-full" />
    </UFormField>

    <div class="flex justify-end gap-2 pt-2">
      <UButton color="neutral" variant="ghost" @click="emit('cancel')">
        {{ t('common.cancel') }}
      </UButton>
      <UButton type="submit" :loading="saving" :disabled="quantity <= 0">
        {{ t('common.save') }}
      </UButton>
    </div>
  </form>
</template>
