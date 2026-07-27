import { openDB, type IDBPDatabase } from 'idb'

const DB_NAME = 'dentalpin'
const DB_VERSION = 1

let _dbPromise: Promise<IDBPDatabase> | null = null

function getDb(): Promise<IDBPDatabase> {
  if (!_dbPromise) {
    _dbPromise = openDB(DB_NAME, DB_VERSION, {
      upgrade(db) {
        if (!db.objectStoreNames.contains('patients')) {
          db.createObjectStore('patients', { keyPath: 'id' })
        }
        if (!db.objectStoreNames.contains('appointments')) {
          db.createObjectStore('appointments', { keyPath: 'id' })
        }
        if (!db.objectStoreNames.contains('pending_ops')) {
          db.createObjectStore('pending_ops', { keyPath: 'id', autoIncrement: true })
        }
        if (!db.objectStoreNames.contains('metadata')) {
          db.createObjectStore('metadata', { keyPath: 'key' })
        }
      }
    })
  }
  return _dbPromise
}

export function useOfflineStorage() {
  async function cacheList<T>(store: string, items: T[]): Promise<void> {
    const db = await getDb()
    const tx = db.transaction(store, 'readwrite')
    for (const item of items) {
      await tx.store.put(item)
    }
    await tx.done
  }

  async function getCached<T>(store: string, id: string): Promise<T | undefined> {
    const db = await getDb()
    return db.get(store, id) as Promise<T | undefined>
  }

  async function getAllCached<T>(store: string): Promise<T[]> {
    const db = await getDb()
    return db.getAll(store) as Promise<T[]>
  }

  async function removeCached(store: string, id: string): Promise<void> {
    const db = await getDb()
    await db.delete(store, id)
  }

  async function clearStore(store: string): Promise<void> {
    const db = await getDb()
    await db.clear(store)
  }

  function queuePendingOp(op: { method: string; path: string; body?: object }): Promise<void> {
    return getDb().then(db => db.add('pending_ops', { ...op, timestamp: Date.now() }))
  }

  async function getPendingOps(): Promise<Array<{ id: number; method: string; path: string; body?: object; timestamp: number }>> {
    const db = await getDb()
    return db.getAll('pending_ops')
  }

  async function removePendingOp(id: number): Promise<void> {
    const db = await getDb()
    await db.delete('pending_ops', id)
  }

  async function setMetadata(key: string, value: string): Promise<void> {
    const db = await getDb()
    await db.put('metadata', { key, value })
  }

  async function getMetadata(key: string): Promise<string | undefined> {
    const db = await getDb()
    const entry = await db.get('metadata', key)
    return entry?.value
  }

  return {
    cacheList,
    getCached,
    getAllCached,
    removeCached,
    clearStore,
    queuePendingOp,
    getPendingOps,
    removePendingOp,
    setMetadata,
    getMetadata
  }
}
