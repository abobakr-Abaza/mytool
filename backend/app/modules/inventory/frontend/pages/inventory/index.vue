<script setup lang="ts">
import type { InventoryItem } from '../../composables/useInventory'
import { useInventory } from '../../composables/useInventory'

definePageMeta({
  title: 'nav.inventory',
  requiresAuth: true,
  permissions: ['inventory.read']
})

const { t } = useI18n()
const { can } = usePermissions()
const inventory = useInventory()

const items = ref<InventoryItem[]>([])
const loading = ref(true)
const showCreateModal = ref(false)
const showMovementModal = ref(false)
const selectedItem = ref<InventoryItem | null>(null)
const search = ref('')
const filterStatus = ref<string | null>(null)

async function load() {
  loading.value = true
  try {
    items.value = await inventory.listItems({ status: filterStatus.value || undefined })
  } finally {
    loading.value = false
  }
}

async function handleDelete(id: string) {
  await inventory.deleteItem(id)
  items.value = items.value.filter(i => i.id !== id)
}

function openMovement(item: InventoryItem) {
  selectedItem.value = item
  showMovementModal.value = true
}

const filteredItems = computed(() => {
  if (!search.value) return items.value
  const q = search.value.toLowerCase()
  return items.value.filter(
    i => i.name.toLowerCase().includes(q) || (i.sku && i.sku.toLowerCase().includes(q))
  )
})

const stockColor = (item: InventoryItem) => {
  if (item.quantity <= 0) return 'text-danger'
  if (item.is_low_stock) return 'text-warning'
  return 'text-success'
}

onMounted(load)
</script>

<template>
  <div class="p-4 space-y-4">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold">{{ t('inventory.title') }}</h1>
        <p class="text-subtle text-sm">{{ t('inventory.subtitle') }}</p>
      </div>
      <UButton
        v-if="can('inventory.write')"
        icon="i-lucide-plus"
        @click="showCreateModal = true"
      >
        {{ t('inventory.addItem') }}
      </UButton>
    </div>

    <!-- Filters -->
    <div class="flex items-center gap-3">
      <UInput
        v-model="search"
        :placeholder="t('inventory.search')"
        icon="i-lucide-search"
        class="max-w-xs"
      />
      <USelect
        v-model="filterStatus"
        :items="[
          { label: t('inventory.all'), value: null },
          { label: t('inventory.active'), value: 'active' },
          { label: t('inventory.discontinued'), value: 'discontinued' },
        ]"
        class="w-40"
      />
    </div>

    <!-- Items list -->
    <UCard v-if="loading">
      <div class="flex items-center justify-center py-12">
        <UIcon name="i-lucide-loader-2" class="w-6 h-6 animate-spin text-subtle" />
      </div>
    </UCard>

    <template v-else>
      <div v-if="filteredItems.length === 0" class="text-center py-16 text-subtle">
        <UIcon name="i-lucide-package" class="w-12 h-12 mx-auto mb-3" />
        <p>{{ t('inventory.empty') }}</p>
      </div>

      <div v-else class="grid gap-3">
        <UCard
          v-for="item in filteredItems"
          :key="item.id"
          class="hover:shadow-md transition-shadow"
        >
          <div class="flex items-center justify-between">
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2">
                <span class="font-medium truncate">{{ item.name }}</span>
                <UBadge v-if="item.quantity <= 0" color="error" variant="solid" size="xs">
                  {{ t('inventory.outOfStock') }}
                </UBadge>
                <UBadge v-else-if="item.is_low_stock" color="warning" variant="solid" size="xs">
                  {{ t('inventory.lowStock') }}
                </UBadge>
              </div>
              <div class="flex items-center gap-3 text-sm text-subtle mt-1">
                <span v-if="item.sku">SKU: {{ item.sku }}</span>
                <span v-if="item.category_name">{{ item.category_name }}</span>
                <span v-if="item.supplier">{{ item.supplier }}</span>
              </div>
            </div>
            <div class="flex items-center gap-4 flex-shrink-0 ml-4">
              <div class="text-right">
                <p class="text-lg font-bold" :class="stockColor(item)">
                  {{ item.quantity }}
                </p>
                <p class="text-xs text-subtle">{{ item.unit }}</p>
              </div>
              <div class="flex gap-1">
                <UButton
                  v-if="can('inventory.write')"
                  icon="i-lucide-plus"
                  size="sm"
                  color="neutral"
                  variant="ghost"
                  :title="t('inventory.stockIn')"
                  @click="openMovement(item)"
                />
                <UButton
                  v-if="can('inventory.delete')"
                  icon="i-lucide-trash-2"
                  size="sm"
                  color="neutral"
                  variant="ghost"
                  class="text-subtle hover:text-danger"
                  @click="handleDelete(item.id)"
                />
              </div>
            </div>
          </div>
        </UCard>
      </div>
    </template>

    <!-- Create modal -->
    <UModal v-model="showCreateModal">
      <template #title>{{ t('inventory.addItem') }}</template>
      <InventoryCreateForm @created="load(); showCreateModal = false" @cancel="showCreateModal = false" />
    </UModal>

    <!-- Movement modal -->
    <UModal v-model="showMovementModal">
      <template #title>{{ t('inventory.stockMovement') }}</template>
      <InventoryMovementForm
        v-if="selectedItem"
        :item="selectedItem"
        @done="load(); showMovementModal = false"
        @cancel="showMovementModal = false"
      />
    </UModal>
  </div>
</template>
