import { AlertTriangle, Trash2, Check, X } from 'lucide-react'
import { useState } from 'react'

const InventoryList = ({ items, onDelete, onUpdate }) => {
  const [searchTerm, setSearchTerm] = useState('')
  const [sortBy, setSortBy] = useState('name')
  const [editingItem, setEditingItem] = useState(null)
  const [editCount, setEditCount] = useState('')

  const filteredItems = items.filter((item) =>
    item.canonical_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (item.brand && item.brand.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  const sortedItems = [...filteredItems].sort((a, b) => {
    switch (sortBy) {
      case 'name':
        return a.canonical_name.localeCompare(b.canonical_name)
      case 'count':
        return b.count_estimate - a.count_estimate
      case 'confidence':
        return b.confidence - a.confidence
      case 'recent':
        return new Date(b.last_seen_at || 0) - new Date(a.last_seen_at || 0)
      default:
        return 0
    }
  })

  const isExpiringSoon = (expiryDate) => {
    if (!expiryDate) return false
    const now = new Date()
    const expiry = new Date(expiryDate)
    const daysUntilExpiry = (expiry - now) / (1000 * 60 * 60 * 24)
    return daysUntilExpiry <= 3 && daysUntilExpiry > 0
  }

  const isLowStock = (count) => count <= 1

  const handleEditStart = (item) => {
    setEditingItem(item.canonical_name)
    setEditCount(item.count_estimate.toString())
  }

  const handleEditSave = async () => {
    if (editingItem && editCount !== '' && onUpdate) {
      const newCount = parseInt(editCount)
      if (!isNaN(newCount)) {
        await onUpdate(editingItem, newCount)
        setEditingItem(null)
        setEditCount('')
      }
    }
  }

  const handleEditCancel = () => {
    setEditingItem(null)
    setEditCount('')
  }

  return (
    <div className="space-y-4">
      {/* Search and Filter */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex-1">
          <input
            type="text"
            placeholder="Search items by name or brand..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-3 py-2 rounded border border-gray-300 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:outline-none"
          />
        </div>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="px-3 py-2 rounded border border-gray-300 text-sm text-gray-900 focus:border-blue-500 focus:outline-none"
        >
          <option value="name">Sort by Name</option>
          <option value="count">Sort by Count</option>
          <option value="confidence">Sort by Confidence</option>
          <option value="recent">Sort by Recent</option>
        </select>
      </div>

      {/* Results Count */}
      {searchTerm && (
        <p className="text-xs text-gray-500">
          Showing {sortedItems.length} of {items.length} items
        </p>
      )}

      {/* Inventory Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="border-b border-gray-200 bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left font-semibold text-gray-700">Item</th>
              <th className="px-4 py-3 text-left font-semibold text-gray-700">Brand</th>
              <th className="px-4 py-3 text-center font-semibold text-gray-700">Count</th>
              <th className="px-4 py-3 text-center font-semibold text-gray-700">Confidence</th>
              <th className="px-4 py-3 text-left font-semibold text-gray-700">Last Seen</th>
              <th className="px-4 py-3 text-left font-semibold text-gray-700">Status</th>
              <th className="px-4 py-3 text-center font-semibold text-gray-700">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {sortedItems.map((item) => (
              <tr key={item.canonical_name} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3 font-medium text-gray-900">{item.canonical_name}</td>
                <td className="px-4 py-3 text-gray-600">{item.brand || '—'}</td>
                <td className="px-4 py-3 text-center">
                  {editingItem === item.canonical_name ? (
                    <div className="flex items-center justify-center gap-2">
                      <input
                        type="number"
                        value={editCount}
                        onChange={(e) => setEditCount(e.target.value)}
                        min="0"
                        className="w-12 px-2 py-1 rounded border border-blue-300 text-center text-sm font-semibold"
                        autoFocus
                      />
                      <button
                        onClick={handleEditSave}
                        className="p-1 text-green-600 hover:bg-green-50 rounded transition-colors"
                        title="Save"
                      >
                        <Check className="h-4 w-4" />
                      </button>
                      <button
                        onClick={handleEditCancel}
                        className="p-1 text-red-600 hover:bg-red-50 rounded transition-colors"
                        title="Cancel"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => handleEditStart(item)}
                      className={`inline-flex items-center justify-center h-8 w-8 rounded-full font-semibold cursor-pointer hover:opacity-80 transition-opacity ${
                        isLowStock(item.count_estimate)
                          ? 'bg-red-100 text-red-700'
                          : 'bg-blue-100 text-blue-700'
                      }`}
                      title="Click to edit count"
                    >
                      {item.count_estimate}
                    </button>
                  )}
                </td>
                <td className="px-4 py-3 text-center">
                  <div className="flex items-center justify-center">
                    <div className="w-16 bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all ${
                          item.confidence >= 0.8
                            ? 'bg-green-500'
                            : item.confidence >= 0.5
                            ? 'bg-yellow-500'
                            : 'bg-red-500'
                        }`}
                        style={{ width: `${item.confidence * 100}%` }}
                      ></div>
                    </div>
                    <span className="ml-2 text-xs font-medium text-gray-600">
                      {(item.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                </td>
                <td className="px-4 py-3 text-gray-600">
                  {item.last_seen_at
                    ? new Date(item.last_seen_at).toLocaleDateString()
                    : '—'}
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-1 flex-wrap">
                    {isLowStock(item.count_estimate) && (
                      <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-red-100 text-red-700 text-xs font-medium">
                        Low Stock
                      </span>
                    )}
                    {isExpiringSoon(item.expiry_date) && (
                      <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-orange-100 text-orange-700 text-xs font-medium">
                        <AlertTriangle className="h-3 w-3" />
                        Expiring
                      </span>
                    )}
                    {item.is_manual && (
                      <span className="inline-flex px-2 py-1 rounded-full bg-purple-100 text-purple-700 text-xs font-medium">
                        Manual
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3 text-center">
                  {onDelete && (
                    <button
                      onClick={() => onDelete(item.canonical_name)}
                      className="p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                      title="Delete item"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default InventoryList
