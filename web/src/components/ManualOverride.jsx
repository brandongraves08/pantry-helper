import { useState } from 'react'
import './ManualOverride.css'

const ManualOverride = ({ onSubmit }) => {
  const [itemName, setItemName] = useState('')
  const [count, setCount] = useState('')
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!itemName.trim() || count === '') {
      alert('Please fill in item name and count')
      return
    }

    setLoading(true)
    try {
      await onSubmit(itemName, parseInt(count), notes)
      setItemName('')
      setCount('')
      setNotes('')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="card manual-override">
      <h3>Manual Entry</h3>
      <p className="form-help">Add or update an item manually</p>
      
      <div className="form-group">
        <label htmlFor="itemName">Item Name *</label>
        <input
          id="itemName"
          type="text"
          value={itemName}
          onChange={(e) => setItemName(e.target.value)}
          placeholder="e.g., peanut butter"
          disabled={loading}
        />
      </div>

      <div className="form-group">
        <label htmlFor="count">Count *</label>
        <input
          id="count"
          type="number"
          value={count}
          onChange={(e) => setCount(e.target.value)}
          min="0"
          disabled={loading}
        />
      </div>

      <div className="form-group">
        <label htmlFor="notes">Notes</label>
        <textarea
          id="notes"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Optional notes (e.g., 'refilled')"
          rows="3"
          disabled={loading}
        />
      </div>

      <button 
        type="submit" 
        className="btn-primary"
        disabled={loading}
      >
        {loading ? 'Updating...' : 'Update Inventory'}
      </button>
    </form>
  )
}

export default ManualOverride
