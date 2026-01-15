import './App.css'

const InventoryList = ({ items }) => {
  const sortedItems = [...items].sort((a, b) => 
    a.canonical_name.localeCompare(b.canonical_name)
  )

  return (
    <div className="card inventory-list">
      <table>
        <thead>
          <tr>
            <th>Item</th>
            <th>Brand</th>
            <th>Count</th>
            <th>Confidence</th>
            <th>Last Seen</th>
          </tr>
        </thead>
        <tbody>
          {sortedItems.map((item) => (
            <tr key={item.canonical_name} className={item.is_manual ? 'manual-entry' : ''}>
              <td className="item-name">{item.canonical_name}</td>
              <td>{item.brand || '—'}</td>
              <td className="count">{item.count_estimate}</td>
              <td>
                <span className="confidence-badge" style={{opacity: item.confidence}}>
                  {(item.confidence * 100).toFixed(0)}%
                </span>
              </td>
              <td className="last-seen">
                {item.last_seen_at ? new Date(item.last_seen_at).toLocaleDateString() : '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default InventoryList
