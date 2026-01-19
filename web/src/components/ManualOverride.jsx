import { useState } from 'react'
import { Plus, Minus } from 'lucide-react'

const ManualOverride = ({ onSubmit, existingItems = [] }) => {
  const [itemName, setItemName] = useState('')
  const [brand, setBrand] = useState('')
  const [packageType, setPackageType] = useState('other')
  const [count, setCount] = useState('')
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [adjustment, setAdjustment] = useState('set') // 'set', 'add', 'subtract'

  const filteredSuggestions = itemName.trim()
    ? existingItems.filter((item) =>
        item.canonical_name.toLowerCase().includes(itemName.toLowerCase())
      )
    : []

  const handleSelectSuggestion = (suggestion) => {
    setItemName(suggestion.canonical_name)
    setBrand(suggestion.brand || '')
    setPackageType(suggestion.package_type || 'other')
    setShowSuggestions(false)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!itemName.trim() || count === '') {
      alert('Please enter item name and count')
      return
    }

    setLoading(true)
    try {
      const countValue = parseInt(count)
      let finalCount = countValue

      if (adjustment === 'add') {
        const existing = existingItems.find(
          (item) => item.canonical_name.toLowerCase() === itemName.toLowerCase()
        )
        finalCount = (existing?.count_estimate || 0) + countValue
      } else if (adjustment === 'subtract') {
        const existing = existingItems.find(
          (item) => item.canonical_name.toLowerCase() === itemName.toLowerCase()
        )
        finalCount = Math.max(0, (existing?.count_estimate || 0) - countValue)
      }

      await onSubmit(itemName, finalCount, notes || `${adjustment}: ${countValue}`)
      setItemName('')
      setBrand('')
      setPackageType('other')
      setCount('')
      setNotes('')
      setAdjustment('set')
      setSuccess(true)
      setTimeout(() => setSuccess(false), 2000)
    } catch (error) {
      alert('Failed to update inventory: ' + error.message)
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

      {/* Item Name with Suggestions */}
      <div className="relative">
        <label className="block text-sm font-medium text-gray-700 mb-1">Item Name *</label>
        <input
          type="text"
          value={itemName}
          onChange={(e) => {
            setItemName(e.target.value)
            setShowSuggestions(true)
          }}
          onFocus={() => setShowSuggestions(itemName.length > 0)}
          placeholder="e.g., peanut butter"
          disabled={loading}
          className="w-full px-3 py-2 rounded border border-gray-300 text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:outline-none disabled:bg-gray-50"
        />
        {showSuggestions && filteredSuggestions.length > 0 && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded shadow-lg z-10">
            {filteredSuggestions.slice(0, 5).map((suggestion) => (
              <button
                key={suggestion.canonical_name}
                type="button"
                onClick={() => handleSelectSuggestion(suggestion)}
                className="w-full text-left px-3 py-2 hover:bg-blue-50 flex justify-between items-center text-sm"
              >
                <span className="font-medium">{suggestion.canonical_name}</span>
                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                  {suggestion.count_estimate}
                </span>
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Brand</label>
          <input
            type="text"
            value={brand}
            onChange={(e) => setBrand(e.target.value)}
            placeholder="Optional"
            disabled={loading}
            className="w-full px-3 py-2 rounded border border-gray-300 text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:outline-none disabled:bg-gray-50"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Package Type</label>
          <select
            value={packageType}
            onChange={(e) => setPackageType(e.target.value)}
            disabled={loading}
            className="w-full px-3 py-2 rounded border border-gray-300 text-gray-900 focus:border-blue-500 focus:outline-none disabled:bg-gray-50"
          >
            <option value="box">Box</option>
            <option value="can">Can</option>
            <option value="jar">Jar</option>
            <option value="bag">Bag</option>
            <option value="bottle">Bottle</option>
            <option value="other">Other</option>
          </select>
        </div>
      </div>

      {/* Adjustment Type */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Operation</label>
        <div className="grid grid-cols-3 gap-2">
          <button
            type="button"
            onClick={() => setAdjustment('set')}
            disabled={loading}
            className={`py-2 px-3 rounded border text-sm font-medium transition-colors ${
              adjustment === 'set'
                ? 'border-blue-500 bg-blue-50 text-blue-700'
                : 'border-gray-300 text-gray-600 hover:border-gray-400'
            }`}
          >
            Set Count
          </button>
          <button
            type="button"
            onClick={() => setAdjustment('add')}
            disabled={loading}
            className={`py-2 px-3 rounded border text-sm font-medium transition-colors flex items-center justify-center gap-1 ${
              adjustment === 'add'
                ? 'border-green-500 bg-green-50 text-green-700'
                : 'border-gray-300 text-gray-600 hover:border-gray-400'
            }`}
          >
            <Plus className="h-4 w-4" />
            Add
          </button>
          <button
            type="button"
            onClick={() => setAdjustment('subtract')}
            disabled={loading}
            className={`py-2 px-3 rounded border text-sm font-medium transition-colors flex items-center justify-center gap-1 ${
              adjustment === 'subtract'
                ? 'border-red-500 bg-red-50 text-red-700'
                : 'border-gray-300 text-gray-600 hover:border-gray-400'
            }`}
          >
            <Minus className="h-4 w-4" />
            Subtract
          </button>
        </div>
      </div>

      {/* Count Input */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {adjustment === 'set' ? 'New Count' : 'Amount'} *
        </label>
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

      {/* Notes */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="e.g., 'Just restocked', 'Expiry: 2026-12-31'"
          rows="2"
          disabled={loading}
          className="w-full px-3 py-2 rounded border border-gray-300 text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:outline-none disabled:bg-gray-50"
        />
      </div>

      {/* Submit Button */}
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

export default ManualOverride
