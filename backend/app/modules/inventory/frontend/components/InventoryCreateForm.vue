<script setup lang="ts">
import { useInventory } from '../composables/useInventory'

const emit = defineEmits<{
  created: []
  cancel: []
}>()

const { t } = useI18n()
const inventory = useInventory()

const categories = ref<{ id: string; name: string }[]>([])
const form = reactive({
  name: '',
  category_id: null as string | null,
  sku: '',
  unit: 'unit',
  quantity: 0,
  min_stock: 5,
  unit_price: null as number | null,
  supplier: '',
  notes: '',
})
const saving = ref(false)

async function submit() {
  saving.value = true
  try {
    await inventory.createItem({ ...form })
    emit('created')
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  categories.value = await inventory.listCategories()
})
</script>

<template>
  <form class="space-y-4 p-4" @submit.prevent="submit">
    <UFormField :label="t('inventory.name')" required>
      <UInput v-model="form.name" class="w-full" />
    </UFormField>

    <div class="grid grid-cols-2 gap-4">
      <UFormField :label="t('inventory.category')">
        <USelect
          v-model="form.category_id"
          :items="categories.map(c => ({ label: c.name, value: c.id }))"
          clearable
          class="w-full"
        />
      </UFormField>
      <UFormField :label="t('inventory.sku')">
        <UInput v-model="form.sku" class="w-full" />
      </UFormField>
    </div>

    <div class="grid grid-cols-3 gap-4">
      <UFormField :label="t('inventory.unit')">
        <USelect
          v-model="form.unit"
          :items="[
            { label: t('inventory.units.unit'), value: 'unit' },
            { label: t('inventory.units.box'), value: 'box' },
            { label: t('inventory.units.pack'), value: 'pack' },
            { label: t('inventory.units.liter'), value: 'liter' },
            { label: t('inventory.units.kilogram'), value: 'kg' },
          ]"
          class="w-full"
        />
      </UFormField>
      <UFormField :label="t('inventory.initialStock')">
        <UInput v-model.number="form.quantity" type="number" min="0" class="w-full" />
      </UFormField>
      <UFormField :label="t('inventory.minStock')">
        <UInput v-model.number="form.min_stock" type="number" min="0" class="w-full" />
      </UFormField>
    </div>

    <UFormField :label="t('inventory.unitPrice')">
      <UInput v-model.number="form.unit_price" type="number" min="0" step="0.01" class="w-full" />
    </UFormField>

    <UFormField :label="t('inventory.supplier')">
      <UInput v-model="form.supplier" class="w-full" />
    </UFormField>

    <div class="flex justify-end gap-2 pt-2">
      <UButton color="neutral" variant="ghost" @click="emit('cancel')">
        {{ t('common.cancel') }}
      </UButton>
      <UButton type="submit" :loading="saving" :disabled="!form.name">
        {{ t('common.save') }}
      </UButton>
    </div>
  </form>
</template>
