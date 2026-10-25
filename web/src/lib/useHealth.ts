import { useCallback, useEffect, useState } from 'react'
import { api } from '../lib/api'
import type { Health } from '../lib/types'

export function useHealth() {
  const [health, setHealth] = useState<Health | null>(null)
  const [error, setError] = useState<unknown>(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      setHealth(await api.health())
      setError(null)
    } catch (e) {
      setHealth(null)
      setError(e)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  return { health, error, loading, reload: load }
}
