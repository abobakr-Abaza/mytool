import { openDB, type IDBPDatabase } from 'idb'

const DB_NAME = 'dentalpin'
const DB_VERSION = 1

let _dbPromise: Promise<IDBPDatabase> | null = null

function getDb(): Promise<IDBPDatabase> | null {
  if (typeof window === 'undefined' || !('indexedDB' in window)) return null
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
    }).catch(() => {
      _dbPromise = null
      return null
    }) as Promise<IDBPDatabase> | null
  }
  return _dbPromise
}

export function useOfflineStorage() {
  async function cacheList<T>(store: string, items: T[]): Promise<void> {
    try {
      const db = await getDb()
      if (!db) return
      const tx = db.transaction(store, 'readwrite')
      for (const item of items) {
        await tx.store.put(item)
      }
      await tx.done
    } catch {
      // IndexedDB unavailable or quota exceeded — skip caching gracefully
    }
  }

  async function getCached<T>(store: string, id: string): Promise<T | undefined> {
    try {
      const db = await getDb()
      if (!db) return undefined
      return db.get(store, id) as Promise<T | undefined>
    } catch {
      return undefined
    }
  }

  async function getAllCached<T>(store: string): Promise<T[]> {
    try {
      const db = await getDb()
      if (!db) return []
      return db.getAll(store) as Promise<T[]>
    } catch {
      return []
    }
  }

  async function removeCached(store: string, id: string): Promise<void> {
    try {
      const db = await getDb()
      if (!db) return
      await db.delete(store, id)
    } catch {
      // silently ignore
    }
  }

  async function clearStore(store: string): Promise<void> {
    try {
      const db = await getDb()
      if (!db) return
      await db.clear(store)
    } catch {
      // silently ignore
    }
  }

  async function queuePendingOp(op: { method: string; path: string; body?: object }): Promise<void> {
    try {
      const db = await getDb()
      if (!db) return
      await db.add('pending_ops', { ...op, timestamp: Date.now() })
    } catch {
      // offline queue unavailable — mutation will be lost
    }
  }

  async function getPendingOps(): Promise<Array<{ id: number; method: string; path: string; body?: object; timestamp: number }>> {
    try {
      const db = await getDb()
      if (!db) return []
      return db.getAll('pending_ops')
    } catch {
      return []
    }
  }

  async function removePendingOp(id: number): Promise<void> {
    try {
      const db = await getDb()
      if (!db) return
      await db.delete('pending_ops', id)
    } catch {
      // silently ignore
    }
  }

  async function setMetadata(key: string, value: string): Promise<void> {
    try {
      const db = await getDb()
      if (!db) return
      await db.put('metadata', { key, value })
    } catch {
      // silently ignore
    }
  }

  async function getMetadata(key: string): Promise<string | undefined> {
    try {
      const db = await getDb()
      if (!db) return undefined
      const entry = await db.get('metadata', key)
      return entry?.value
    } catch {
      return undefined
    }
  }

  async function replayPendingOps(apiCall: (op: { method: string; path: string; body?: object }) => Promise<any>): Promise<number> {
    const ops = await getPendingOps()
    let replayed = 0
    for (const op of ops) {
      try {
        await apiCall(op)
        await removePendingOp(op.id)
        replayed++
      } catch {
        break
      }
    }
    return replayed
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
    getMetadata,
    replayPendingOps
  }
}
