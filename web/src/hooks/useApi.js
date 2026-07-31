import { useState, useEffect, useCallback } from 'react'

export const useApi = (apiFn, immediate = false, ...args) => {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(immediate)
  const [error, setError] = useState(null)

  const execute = useCallback(async (...callArgs) => {
    setLoading(true)
    setError(null)
    try {
      const result = await apiFn(...(callArgs.length ? callArgs : args))
      setData(result)
      return result
    } catch (err) {
      setError(err)
      throw err
    } finally {
      setLoading(false)
    }
  }, [apiFn, args])

  const refetch = useCallback(() => execute(...args), [execute, args])

  useEffect(() => {
    if (immediate) {
      execute(...args)
    }
  }, [execute, immediate, ...args.map(JSON.stringify)])

  return { data, loading, error, execute, refetch }
}

export const useMutation = (apiFn) => {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const mutate = useCallback(async (...args) => {
    setLoading(true)
    setError(null)
    try {
      const result = await apiFn(...args)
      setData(result)
      return result
    } catch (err) {
      setError(err)
      throw err
    } finally {
      setLoading(false)
    }
  }, [apiFn])

  const reset = () => {
    setData(null)
    setError(null)
  }

  return { data, loading, error, mutate, reset }
}

export default useApi
