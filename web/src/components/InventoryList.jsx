import { AlertTriangle } from 'lucide-react'

const InventoryList = ({ items }) => {
  const sortedItems = [...items].sort((a, b) =>
    a.canonical_name.localeCompare(b.canonical_name)
  )

  const isExpiringSoon = (expiryDate) => {
    if (!expiryDate) return false
    const now = new Date()
    const expiry = new Date(expiryDate)
    const daysUntilExpiry = (expiry - now) / (1000 * 60 * 60 * 24)
    return daysUntilExpiry <= 3 && daysUntilExpiry > 0
  }

  return (
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
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {sortedItems.map((item) => (
            <tr key={item.canonical_name} className="hover:bg-gray-50 transition-colors">
              <td className="px-4 py-3 font-medium text-gray-900">{item.canonical_name}</td>
              <td className="px-4 py-3 text-gray-600">{item.brand || '—'}</td>
              <td className="px-4 py-3 text-center">
                <span className="inline-flex items-center justify-center h-8 w-8 rounded-full bg-blue-100 text-blue-700 font-semibold">
                  {item.count_estimate}
                </span>
              </td>
              <td className="px-4 py-3 text-center">
                <div className="flex items-center justify-center">
                  <div className="w-16 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-green-500 h-2 rounded-full transition-all"
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
                {isExpiringSoon(item.expiry_date) && (
                  <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-orange-100 text-orange-700 text-xs font-medium">
                    <AlertTriangle className="h-3 w-3" />
                    Expiring
                  </span>
                )}
                {item.is_manual && (
                  <span className="inline-flex ml-1 px-2 py-1 rounded-full bg-purple-100 text-purple-700 text-xs font-medium">
                    Manual
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default InventoryList
