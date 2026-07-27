import type { ApiResponse, PaginatedResponse } from '~~/app/types'

interface Category {
  id: string
  name: string
  description: string | null
}

interface InventoryItem {
  id: string
  category_id: string | null
  name: string
  sku: string | null
  unit: string
  quantity: number
  min_stock: number
  unit_price: number | null
  status: string
  notes: string | null
  supplier: string | null
  category_name: string | null
  is_low_stock: boolean
}

interface Movement {
  id: string
  item_id: string
  movement_type: string
  quantity: number
  reference: string | null
  notes: string | null
  moved_at: string
}

interface Alert {
  item_id: string
  item_name: string
  quantity: number
  min_stock: number
  category_name: string | null
}

interface DashboardStats {
  total_items: number
  low_stock_count: number
  out_of_stock_count: number
  total_categories: number
  total_value: number
}

export function useInventory() {
  const api = useApi()

  async function listCategories(): Promise<Category[]> {
    const res = await api.get<PaginatedResponse<Category>>('/api/v1/inventory/categories')
    return res.data
  }

  async function createCategory(data: Partial<Category>): Promise<Category> {
    const res = await api.post<ApiResponse<Category>>('/api/v1/inventory/categories', data)
    return res.data
  }

  async function listItems(params?: { category_id?: string; status?: string }): Promise<InventoryItem[]> {
    const res = await api.get<PaginatedResponse<InventoryItem>>('/api/v1/inventory/items', undefined, params)
    return res.data
  }

  async function getItem(id: string): Promise<InventoryItem> {
    const res = await api.get<ApiResponse<InventoryItem>>(`/api/v1/inventory/items/${id}`)
    return res.data
  }

  async function createItem(data: Partial<InventoryItem>): Promise<InventoryItem> {
    const res = await api.post<ApiResponse<InventoryItem>>('/api/v1/inventory/items', data)
    return res.data
  }

  async function updateItem(id: string, data: Partial<InventoryItem>): Promise<InventoryItem> {
    const res = await api.put<ApiResponse<InventoryItem>>(`/api/v1/inventory/items/${id}`, data)
    return res.data
  }

  async function deleteItem(id: string): Promise<void> {
    await api.del(`/api/v1/inventory/items/${id}`)
  }

  async function recordMovement(data: {
    item_id: string
    movement_type: 'in' | 'out' | 'adjustment' | 'return'
    quantity: number
    reference?: string
    notes?: string
  }): Promise<Movement> {
    const res = await api.post<ApiResponse<Movement>>('/api/v1/inventory/movements', data)
    return res.data
  }

  async function listMovements(itemId?: string): Promise<Movement[]> {
    const params = itemId ? { item_id: itemId } : undefined
    const res = await api.get<PaginatedResponse<Movement>>('/api/v1/inventory/movements', undefined, params)
    return res.data
  }

  async function getAlerts(): Promise<Alert[]> {
    const res = await api.get<PaginatedResponse<Alert>>('/api/v1/inventory/alerts')
    return res.data
  }

  async function getDashboard(): Promise<DashboardStats> {
    const res = await api.get<ApiResponse<DashboardStats>>('/api/v1/inventory/dashboard')
    return res.data
  }

  return {
    listCategories, createCategory,
    listItems, getItem, createItem, updateItem, deleteItem,
    recordMovement, listMovements,
    getAlerts, getDashboard,
  }
}
