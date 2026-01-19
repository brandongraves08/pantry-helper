import { useState, useEffect } from 'react'
import api from './api'
import InventoryList from './components/InventoryList'
import ManualOverride from './components/ManualOverride'
import StatsWidget from './components/StatsWidget'
import ChartComponent from './components/ChartComponent'
import ImageUpload from './components/ImageUpload'
import TaskMonitor from './components/TaskMonitor'
import SettingsPanel from './components/SettingsPanel'
import DeviceDashboard from './components/DeviceDashboard'
import InventoryAnalytics from './components/InventoryAnalytics'
import { Camera, Settings, Package, BarChart3, Home } from 'lucide-react'
import './App.css'

function App() {
  const [inventory, setInventory] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [currentView, setCurrentView] = useState('inventory')
  const [stats, setStats] = useState({
    totalItems: 0,
    expiringSoon: 0,
    lastUpdated: null,
    itemsAdded: 0,
  })

  useEffect(() => {
    fetchInventory()
    const interval = setInterval(fetchInventory, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchInventory = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await api.get('/v1/inventory')
      const items = response.data.items || []
      setInventory(items)
      updateStats(items)
    } catch (err) {
      setError('Failed to load inventory: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  const updateStats = (items) => {
    const now = new Date()
    const expiringSoon = items.filter((item) => {
      if (!item.expiry_date) return false
      const expiryDate = new Date(item.expiry_date)
      const daysUntilExpiry = (expiryDate - now) / (1000 * 60 * 60 * 24)
      return daysUntilExpiry <= 3 && daysUntilExpiry > 0
    }).length

    setStats({
      totalItems: items.length,
      expiringSoon,
      lastUpdated: new Date().toLocaleTimeString(),
      itemsAdded: items.length,
    })
  }

  const handleOverride = async (itemName, count, notes) => {
    try {
      await api.post('/v1/inventory/override', {
        item_name: itemName,
        count_estimate: count,
        notes: notes,
      })
      await fetchInventory()
    } catch (err) {
      setError('Failed to update inventory: ' + err.message)
    }
  }

  const handleDeleteItem = async (itemName) => {
    if (!window.confirm(`Are you sure you want to delete "${itemName}"?`)) {
      return
    }
    try {
      await handleOverride(itemName, 0, 'deleted')
      setInventory(inventory.filter(item => item.canonical_name !== itemName))
    } catch (err) {
      setError('Failed to delete item: ' + err.message)
    }
  }

  const handleUpdateItemCount = async (itemName, newCount) => {
    try {
      await handleOverride(itemName, newCount, `count updated to ${newCount}`)
      await fetchInventory()
    } catch (err) {
      setError('Failed to update item: ' + err.message)
    }
  }

  const handleImageUpload = async (file) => {
    try {
      setUploading(true)
      setError(null)
      const formData = new FormData()
      formData.append('image', file)
      await api.post('/v1/admin/capture-manual', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setTimeout(fetchInventory, 3000)
    } catch (err) {
      setError('Failed to upload image: ' + err.message)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white shadow-sm">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-green-500 p-2">
                <Camera className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">🥫 Pantry Inventory</h1>
                <p className="text-sm text-gray-500">Smart pantry management with vision AI</p>
              </div>
            </div>
            <button
              onClick={() => setShowSettings(true)}
              className="rounded-lg bg-gray-100 px-4 py-2 font-medium text-gray-700 hover:bg-gray-200"
            >
              <Settings className="inline mr-2 h-4 w-4" />
              Settings
            </button>
          </div>
          
          {/* Navigation Tabs */}
          <nav className="mt-4 flex gap-1 border-b border-gray-200">
            <button
              onClick={() => setCurrentView('inventory')}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${
                currentView === 'inventory'
                  ? 'border-b-2 border-green-500 text-green-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Home className="h-4 w-4" />
              Inventory
            </button>
            <button
              onClick={() => setCurrentView('devices')}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${
                currentView === 'devices'
                  ? 'border-b-2 border-green-500 text-green-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Camera className="h-4 w-4" />
              Devices
            </button>
            <button
              onClick={() => setCurrentView('analytics')}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${
                currentView === 'analytics'
                  ? 'border-b-2 border-green-500 text-green-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <BarChart3 className="h-4 w-4" />
              Analytics
            </button>
          </nav>
        </div>
      </header>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 border-b border-red-200 px-4 py-3 text-red-800">
          <p className="text-sm font-medium">{error}</p>
        </div>
      )}

      {/* Main Content */}
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Inventory View */}
        {currentView === 'inventory' && (
          <>
            {/* Stats Grid */}
            <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatsWidget
                title="Total Items"
                value={stats.totalItems}
                icon={Camera}
                color="blue"
              />
              <StatsWidget
                title="Expiring Soon"
                value={stats.expiringSoon}
                icon={Camera}
                color="orange"
              />
              <StatsWidget
                title="Last Updated"
                value={stats.lastUpdated || '—'}
                icon={Camera}
                color="green"
              />
              <StatsWidget
                title="Items Added"
                value={stats.itemsAdded}
                icon={Camera}
                color="blue"
              />
            </div>

            {/* Main Grid */}
            <div className="grid gap-8 lg:grid-cols-3">
              {/* Left Column */}
              <div className="lg:col-span-2 space-y-6">
                <ChartComponent />

                <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
                  <h3 className="mb-4 text-lg font-semibold text-gray-900">📸 Manual Capture</h3>
                  <ImageUpload onUpload={handleImageUpload} isLoading={uploading} />
                </div>

                <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
                  <div className="mb-4 flex items-center justify-between">
                    <h2 className="text-lg font-semibold text-gray-900">
                      Inventory ({inventory.length} items)
                    </h2>
                    <button
                      onClick={fetchInventory}
                      className="rounded bg-blue-500 px-3 py-1 text-sm font-medium text-white hover:bg-blue-600"
                    >
                      Refresh
                    </button>
                  </div>

                  {loading ? (
                    <div className="py-12 text-center">
                      <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-blue-500"></div>
                      <p className="mt-2 text-gray-600">Loading inventory...</p>
                    </div>
                  ) : inventory.length === 0 ? (
                    <div className="py-8 text-center">
                      <p className="text-gray-500">No items in inventory yet.</p>
                      <p className="text-sm text-gray-400">Upload an image or manually add items to get started.</p>
                    </div>
                  ) : (
                    <InventoryList items={inventory} onDelete={handleDeleteItem} onUpdate={handleUpdateItemCount} />
                  )}
                </div>
              </div>

              {/* Right Column */}
              <div className="space-y-6">
                <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
                  <h3 className="mb-4 text-lg font-semibold text-gray-900">✏️ Add / Update Item</h3>
                  <ManualOverride onSubmit={handleOverride} existingItems={inventory} />
                </div>
                <TaskMonitor />
              </div>
            </div>
          </>
        )}

        {/* Devices View */}
        {currentView === 'devices' && <DeviceDashboard />}

        {/* Analytics View */}
        {currentView === 'analytics' && <InventoryAnalytics />}
      </main>

      {/* Settings Modal */}
      {showSettings && <SettingsPanel onClose={() => setShowSettings(false)} />}
    </div>
  )
}

export default App
