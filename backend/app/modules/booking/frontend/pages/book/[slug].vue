<script setup lang="ts">
import type { Slot, Professional } from '../../composables/useBooking'
import { useBooking } from '../../composables/useBooking'

const { slug } = useRoute<'book-slug'>().params
const booking = useBooking()
const { t } = useI18n()

definePageMeta({
  title: 'Book Appointment',
  requiresAuth: false,
  layout: false,
})

const step = ref<'select' | 'info' | 'confirm'>('select')
const loading = ref(false)
const error = ref('')
const success = ref(false)

const professionals = ref<Professional[]>([])
const slots = ref<Slot[]>([])
const selectedDate = ref('')
const selectedSlot = ref<Slot | null>(null)
const availableDates = ref<string[]>([])

const form = reactive({
  professional_id: '',
  patient_name: '',
  patient_phone: '',
  patient_email: '',
  notes: '',
})

const filteredSlots = computed(() => {
  if (!selectedDate.value) return []
  return slots.value.filter(s => s.date === selectedDate.value && s.professional_id === form.professional_id)
})

async function loadProfessionals() {
  loading.value = true
  try {
    professionals.value = await booking.getProfessionals(slug)
  } catch {
    error.value = 'Failed to load clinic data'
  } finally {
    loading.value = false
  }
}

async function selectProfessional(id: string) {
  form.professional_id = id
  selectedDate.value = ''
  selectedSlot.value = null
  loading.value = true
  try {
    const today = new Date().toISOString().split('T')[0]
    slots.value = await booking.getSlots(slug, { professional_id: id, date_from: today })
    const dates = [...new Set(slots.value.map(s => s.date))].sort()
    availableDates.value = dates
    step.value = 'select'
  } catch {
    error.value = 'Failed to load available slots'
  } finally {
    loading.value = false
  }
}

function selectSlot(slot: Slot) {
  selectedSlot.value = slot
  selectedDate.value = slot.date
  step.value = 'info'
}

async function submit() {
  loading.value = true
  error.value = ''
  try {
    await booking.createBooking(slug, {
      clinic_slug: slug,
      professional_id: form.professional_id,
      date: selectedSlot.value!.date,
      start_time: selectedSlot.value!.start_time,
      patient_name: form.patient_name,
      patient_phone: form.patient_phone,
      patient_email: form.patient_email || undefined,
      notes: form.notes || undefined,
    })
    success.value = true
  } catch (e: any) {
    error.value = e?.message || t('app.error')
  } finally {
    loading.value = false
  }
}

onMounted(loadProfessionals)
</script>

<template>
  <div class="min-h-screen bg-surface flex items-start justify-center p-4 pt-12">
    <div class="w-full max-w-lg">
      <!-- Header -->
      <div class="text-center mb-8">
        <h1 class="text-2xl font-bold">{{ t('booking.title') }}</h1>
        <p class="text-subtle">{{ t('booking.subtitle') }}</p>
      </div>

      <!-- Success -->
      <UCard v-if="success" class="text-center py-8">
        <UIcon name="i-lucide-check-circle-2" class="w-16 h-16 text-success mx-auto mb-4" />
        <h2 class="text-xl font-semibold mb-2">{{ t('booking.successTitle') }}</h2>
        <p class="text-subtle">{{ t('booking.successMessage') }}</p>
      </UCard>

      <!-- Loading -->
      <UCard v-else-if="loading && professionals.length === 0">
        <div class="flex items-center justify-center py-8">
          <UIcon name="i-lucide-loader-2" class="w-6 h-6 animate-spin text-subtle" />
        </div>
      </UCard>

      <!-- Error -->
      <UAlert v-else-if="error" color="error" :title="error" class="mb-4" />

      <!-- Professional selection -->
      <div v-else-if="!form.professional_id" class="space-y-3">
        <h2 class="text-lg font-medium">{{ t('booking.selectProfessional') }}</h2>
        <UCard
          v-for="prof in professionals"
          :key="prof.id"
          class="cursor-pointer hover:shadow-md transition-shadow"
          @click="selectProfessional(prof.id)"
        >
          <div class="flex items-center gap-3">
            <UAvatar :alt="prof.name" />
            <div>
              <p class="font-medium">{{ prof.name }}</p>
              <p v-if="prof.specialty" class="text-sm text-subtle">{{ prof.specialty }}</p>
            </div>
          </div>
        </UCard>
      </div>

      <!-- Date & slot selection -->
      <div v-else-if="!selectedSlot" class="space-y-4">
        <UButton variant="ghost" size="sm" @click="form.professional_id = ''">
          &larr; {{ t('booking.changeProfessional') }}
        </UButton>
        <h2 class="text-lg font-medium">{{ t('booking.selectDate') }}</h2>

        <div v-if="availableDates.length === 0" class="text-center py-8 text-subtle">
          {{ t('booking.noSlots') }}
        </div>

        <template v-else>
          <div class="flex gap-2 flex-wrap">
            <UButton
              v-for="d in availableDates"
              :key="d"
              :color="selectedDate === d ? 'primary' : 'neutral'"
              variant="solid"
              size="sm"
              @click="selectedDate = d"
            >
              {{ new Date(d).toLocaleDateString(t('code') === 'ar' ? 'ar-EG' : 'en-US', {
                weekday: 'short', month: 'short', day: 'numeric'
              }) }}
            </UButton>
          </div>

          <div v-if="selectedDate" class="grid grid-cols-3 gap-2">
            <UButton
              v-for="slot in filteredSlots"
              :key="slot.start_time"
              color="neutral"
              variant="outline"
              size="sm"
              @click="selectSlot(slot)"
            >
              {{ slot.start_time }}
            </UButton>
          </div>
        </template>
      </div>

      <!-- Patient info form -->
      <div v-else class="space-y-4">
        <UButton variant="ghost" size="sm" @click="selectedSlot = null">
          &larr; {{ t('booking.changeSlot') }}
        </UButton>

        <UCard class="bg-primary/5 border-primary/20">
          <p class="text-sm">
            <strong>{{ selectedSlot.professional_name }}</strong> &mdash;
            {{ new Date(selectedSlot.date).toLocaleDateString() }} {{ selectedSlot.start_time }}
          </p>
        </UCard>

        <UFormField :label="t('booking.yourName')" required>
          <UInput v-model="form.patient_name" class="w-full" />
        </UFormField>
        <UFormField :label="t('booking.yourPhone')" required>
          <UInput v-model="form.patient_phone" class="w-full" />
        </UFormField>
        <UFormField :label="t('booking.yourEmail')">
          <UInput v-model="form.patient_email" type="email" class="w-full" />
        </UFormField>
        <UFormField :label="t('booking.notes')">
          <UTextarea v-model="form.notes" class="w-full" />
        </UFormField>

        <UAlert v-if="error" color="error" :title="error" />

        <UButton
          class="w-full"
          :loading="loading"
          :disabled="!form.patient_name || !form.patient_phone"
          @click="submit"
        >
          {{ t('booking.confirmBooking') }}
        </UButton>
      </div>
    </div>
  </div>
</template>
