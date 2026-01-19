import { useState, useEffect } from 'react'
import { BarChart3, TrendingDown, AlertTriangle, Package, Download, RefreshCw } from 'lucide-react'
import api from '../api'

const InventoryAnalytics = () => {
  const [stats, setStats] = useState(null)
  const [lowStock, setLowStock] = useState([])
  const [staleItems, setStaleItems] = useState([])
  const [recentChanges, setRecentChanges] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    fetchAnalytics()
    const interval = setInterval(fetchAnalytics, 60000) // Refresh every minute
    return () => clearInterval(interval)
  }, [])

  const fetchAnalytics = async () => {
    try {
      setLoading(true)
      setError(null)

      // Fetch all analytics data in parallel
      const [statsRes, lowStockRes, staleRes, changesRes] = await Promise.all([
        api.get('/v1/inventory/stats'),
        api.get('/v1/inventory/low-stock?threshold=2'),
        api.get('/v1/inventory/stale-items?days_threshold=7'),
        api.get('/v1/inventory/recent-changes?hours=24'),
      ])

      setStats(statsRes.data)
      setLowStock(lowStockRes.data.items || [])
      setStaleItems(staleRes.data.items || [])
      setRecentChanges(changesRes.data.changes || [])
    } catch (err) {
      setError('Failed to load analytics: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleExport = async (format) => {
    try {
      const response = await api.get(`/v1/inventory/export?format=${format}`)
      
      if (format === 'json') {
        const blob = new Blob([JSON.stringify(response.data, null, 2)], {
          type: 'application/json',
        })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `inventory-${new Date().toISOString().split('T')[0]}.json`
        a.click()
      } else if (format === 'csv') {
        const blob = new Blob([response.data.content], { type: 'text/csv' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `inventory-${new Date().toISOString().split('T')[0]}.csv`
        a.click()
      }
    } catch (err) {
      alert('Failed to export: ' + err.message)
    }
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const getEventIcon = (eventType) => {
    switch (eventType) {
      case 'seen':
        return '👁️'
      case 'manual_override':
        return '✏️'
      case 'adjusted':
        return '🔄'
      default:
        return '📝'
    }
  }

  if (loading && !stats) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading analytics...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center gap-2 text-red-800">
          <AlertTriangle className="w-5 h-5" />
          <span>{error}</span>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header with Actions */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <BarChart3 className="w-7 h-7" />
          Inventory Analytics
        </h2>
        
        <div className="flex items-center gap-2">
          <button
            onClick={fetchAnalytics}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            disabled={loading}
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          
          <div className="relative group">
            <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors">
              <Download className="w-4 h-4" />
              Export
            </button>
            <div className="absolute right-0 mt-2 w-32 bg-white rounded-lg shadow-lg border hidden group-hover:block z-10">
              <button
                onClick={() => handleExport('json')}
                className="w-full text-left px-4 py-2 hover:bg-gray-100 rounded-t-lg"
              >
                JSON
              </button>
              <button
                onClick={() => handleExport('csv')}
                className="w-full text-left px-4 py-2 hover:bg-gray-100 rounded-b-lg"
              >
                CSV
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Overview */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-600 mb-1">Total Items</div>
                <div className="text-3xl font-bold text-gray-900">{stats.total_items}</div>
              </div>
              <Package className="w-10 h-10 text-blue-500" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-600 mb-1">In Stock</div>
                <div className="text-3xl font-bold text-green-600">{stats.items_in_stock}</div>
              </div>
              <BarChart3 className="w-10 h-10 text-green-500" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-600 mb-1">Out of Stock</div>
                <div className="text-3xl font-bold text-red-600">{stats.items_out_of_stock}</div>
              </div>
              <AlertTriangle className="w-10 h-10 text-red-500" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-600 mb-1">Avg Confidence</div>
                <div className="text-3xl font-bold text-purple-600">
                  {(stats.avg_confidence * 100).toFixed(0)}%
                </div>
              </div>
              <TrendingDown className="w-10 h-10 text-purple-500" />
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow-md">
        <div className="border-b border-gray-200">
          <div className="flex gap-4 px-6">
            {[
              { id: 'overview', label: 'Overview' },
              { id: 'low-stock', label: `Low Stock (${lowStock.length})` },
              { id: 'stale', label: `Stale Items (${staleItems.length})` },
              { id: 'activity', label: 'Recent Activity' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-2 border-b-2 font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-600 hover:text-gray-900'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <div className="p-6">
          {/* Overview Tab */}
          {activeTab === 'overview' && stats && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold mb-4">Confidence Distribution</h3>
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-green-50 rounded-lg p-4">
                    <div className="text-sm text-gray-600 mb-1">High Confidence</div>
                    <div className="text-2xl font-bold text-green-600">
                      {stats.confidence_breakdown.high}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">≥80%</div>
                  </div>
                  <div className="bg-yellow-50 rounded-lg p-4">
                    <div className="text-sm text-gray-600 mb-1">Medium Confidence</div>
                    <div className="text-2xl font-bold text-yellow-600">
                      {stats.confidence_breakdown.medium}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">50-79%</div>
                  </div>
                  <div className="bg-red-50 rounded-lg p-4">
                    <div className="text-sm text-gray-600 mb-1">Low Confidence</div>
                    <div className="text-2xl font-bold text-red-600">
                      {stats.confidence_breakdown.low}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">&lt;50%</div>
                  </div>
                </div>
              </div>

              <div>
                <div className="text-sm text-gray-600">Total Quantity Tracked</div>
                <div className="text-3xl font-bold text-gray-900 mt-2">
                  {stats.total_quantity} items
                </div>
              </div>
            </div>
          )}

          {/* Low Stock Tab */}
          {activeTab === 'low-stock' && (
            <div>
              {lowStock.length === 0 ? (
                <div className="text-center text-gray-500 py-8">
                  No low stock items
                </div>
              ) : (
                <div className="space-y-3">
                  {lowStock.map((item, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-4 bg-red-50 border border-red-200 rounded-lg"
                    >
                      <div>
                        <div className="font-medium text-gray-900">{item.name}</div>
                        {item.brand && (
                          <div className="text-sm text-gray-600">{item.brand}</div>
                        )}
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-red-600">{item.count}</div>
                        <div className="text-xs text-gray-500">
                          {(item.confidence * 100).toFixed(0)}% confidence
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Stale Items Tab */}
          {activeTab === 'stale' && (
            <div>
              {staleItems.length === 0 ? (
                <div className="text-center text-gray-500 py-8">
                  No stale items
                </div>
              ) : (
                <div className="space-y-3">
                  {staleItems.map((item, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-4 bg-orange-50 border border-orange-200 rounded-lg"
                    >
                      <div>
                        <div className="font-medium text-gray-900">{item.name}</div>
                        {item.brand && (
                          <div className="text-sm text-gray-600">{item.brand}</div>
                        )}
                        <div className="text-xs text-gray-500 mt-1">
                          Last count: {item.last_count}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-orange-600">
                          {item.days_since_seen}d
                        </div>
                        <div className="text-xs text-gray-500">not seen</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Activity Tab */}
          {activeTab === 'activity' && (
            <div>
              {recentChanges.length === 0 ? (
                <div className="text-center text-gray-500 py-8">
                  No recent activity
                </div>
              ) : (
                <div className="space-y-2">
                  {recentChanges.map((change, index) => (
                    <div
                      key={index}
                      className="flex items-center gap-3 p-3 hover:bg-gray-50 rounded-lg transition-colors"
                    >
                      <div className="text-2xl">{getEventIcon(change.event_type)}</div>
                      <div className="flex-1">
                        <div className="font-medium text-gray-900">{change.item_name}</div>
                        <div className="text-sm text-gray-600">
                          {change.event_type.replace('_', ' ')}
                          {change.delta !== 0 && (
                            <span className={change.delta > 0 ? 'text-green-600' : 'text-red-600'}>
                              {' '}({change.delta > 0 ? '+' : ''}{change.delta})
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="text-xs text-gray-500">
                        {formatDate(change.timestamp)}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default InventoryAnalytics
