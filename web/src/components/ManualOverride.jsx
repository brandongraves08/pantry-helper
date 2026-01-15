import { useState } from 'react'
import { Plus } from 'lucide-react'

const ManualOverride = ({ onSubmit }) => {
  const [itemName, setItemName] = useState('')
  const [count, setCount] = useState('')
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!itemName.trim() || count === '') {
      return
    }

    setLoading(true)
    try {
      await onSubmit(itemName, parseInt(count), notes)
      setItemName('')
      setCount('')
      setNotes('')
      setSuccess(true)
      setTimeout(() => setSuccess(false), 2000)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {success && (
        <div className="rounded bg-green-50 border border-green-200 p-3 text-green-700 text-sm font-medium">
          ✓ Item updated successfully
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Item Name *</label>
        <input
          type="text"
          value={itemName}
          onChange={(e) => setItemName(e.target.value)}
          placeholder="e.g., peanut butter"
          disabled={loading}
          className="w-full px-3 py-2 rounded border border-gray-300 text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:outline-none disabled:bg-gray-50"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Count *</label>
        <input
          type="number"
          value={count}
          onChange={(e) => setCount(e.target.value)}
          min="0"
          max="999"
          disabled={loading}
          placeholder="0"
          className="w-full px-3 py-2 rounded border border-gray-300 text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:outline-none disabled:bg-gray-50"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Optional notes (e.g., 'refilled')"
          rows="2"
          disabled={loading}
          className="w-full px-3 py-2 rounded border border-gray-300 text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:outline-none disabled:bg-gray-50"
        />
      </div>

      <button
        type="submit"
        disabled={loading}
        className="w-full flex items-center justify-center gap-2 rounded-lg bg-blue-500 px-4 py-2 font-medium text-white hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        <Plus className="h-4 w-4" />
        {loading ? 'Updating...' : 'Update Inventory'}
      </button>
    </form>
  )
}

export default ManualOverrideexport default ManualOverride
