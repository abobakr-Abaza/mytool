interface Professional {
  id: string
  name: string
  specialty: string | null
}

interface Slot {
  professional_id: string
  professional_name: string
  date: string
  start_time: string
  end_time: string
}

interface BookingResponse {
  appointment_id: string
  date: string
  start_time: string
  end_time: string
  professional_name: string
}

export function useBooking() {
  const api = useApi()

  async function getProfessionals(slug: string): Promise<Professional[]> {
    const res = await api.get<{ data: Professional[] }>(`/api/v1/public/booking/clinics/${slug}/professionals`)
    return res.data
  }

  async function getSlots(
    slug: string,
    params?: { professional_id?: string; date_from?: string; date_to?: string }
  ): Promise<Slot[]> {
    const res = await api.get<{ data: Slot[] }>(
      `/api/v1/public/booking/clinics/${slug}/slots`,
      undefined,
      params as Record<string, string | number | boolean | undefined | null>
    )
    return res.data
  }

  async function createBooking(slug: string, data: {
    clinic_slug: string
    professional_id: string
    date: string
    start_time: string
    patient_name: string
    patient_phone: string
    patient_email?: string
    notes?: string
  }): Promise<BookingResponse> {
    const res = await api.post<{ data: BookingResponse }>(
      `/api/v1/public/booking/clinics/${slug}/book`,
      data,
      { skipAuth: true }
    )
    return res.data
  }

  return { getProfessionals, getSlots, createBooking }
}
