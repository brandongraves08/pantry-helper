import { useState, useEffect } from 'react'
import api from './api'
import InventoryList from './components/InventoryList'
import ManualOverride from './components/ManualOverride'
import './App.css'

function App() {
  const [inventory, setInventory] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchInventory()
  }, [])

  const fetchInventory = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await api.get('/v1/inventory')
      setInventory(response.data.items)
    } catch (err) {
      setError('Failed to load inventory: ' + err.message)
    } finally {
      setLoading(false)
    }
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

  return (
    <div className="app">
      <header className="header">
        <h1>🥫 Pantry Inventory</h1>
        <p>Event-driven pantry management with ESP32 camera</p>
      </header>

      <main className="container">
        <div className="sidebar">
          <ManualOverride onSubmit={handleOverride} />
        </div>

        <div className="content">
          {error && <div className="error-banner">{error}</div>}
          
          {loading ? (
            <div className="loading">Loading inventory...</div>
          ) : (
            <>
              <div className="inventory-header">
                <h2>Current Inventory ({inventory.length} items)</h2>
                <button onClick={fetchInventory} className="btn-secondary">
                  Refresh
                </button>
              </div>
              
              {inventory.length === 0 ? (
                <div className="empty-state">
                  <p>No items in inventory yet.</p>
                  <p>Trigger a capture or manually add items to get started.</p>
                </div>
              ) : (
                <InventoryList items={inventory} />
              )}
            </>
          )}
        </div>
      </main>
    </div>
  )
}

export default App
