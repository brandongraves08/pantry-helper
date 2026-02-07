import { useEffect, useState } from 'react'
import api from '../api'
import { RefreshCw, ShoppingCart } from 'lucide-react'

const ShoppingList = () => {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchList = async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await api.get('/v1/shopping-list')
      setItems(res.data.items || [])
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const recompute = async () => {
    try {
      setError(null)
      await api.post('/v1/shopping-list/recompute')
      await fetchList()
    } catch (e) {
      setError(e.message)
    }
  }

  useEffect(() => {
    fetchList()
  }, [])

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <ShoppingCart className="h-5 w-5" /> Shopping List
        </h2>
        <div className="flex gap-2">
          <button
            onClick={recompute}
            className="rounded bg-green-500 px-3 py-1 text-sm font-medium text-white hover:bg-green-600"
          >
            Recompute
          </button>
          <button
            onClick={fetchList}
            className="rounded bg-blue-500 px-3 py-1 text-sm font-medium text-white hover:bg-blue-600"
            title="Refresh"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {error && <div className="mb-4 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}

      {loading ? (
        <div className="py-8 text-center text-gray-600">Loading…</div>
      ) : items.length === 0 ? (
        <div className="py-8 text-center text-gray-500">Nothing on the list. (Set par levels to auto-generate.)</div>
      ) : (
        <ul className="divide-y divide-gray-200">
          {items.map((it) => (
            <li key={`${it.item_name}-${it.location || ''}`} className="py-3 flex items-center justify-between">
              <div>
                <div className="font-medium text-gray-900">{it.item_name}</div>
                <div className="text-xs text-gray-500">
                  {it.reason || 'needed'}{it.location ? ` • ${it.location}` : ''}
                </div>
              </div>
              <div className="font-semibold text-gray-900">x{it.needed}</div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default ShoppingList
