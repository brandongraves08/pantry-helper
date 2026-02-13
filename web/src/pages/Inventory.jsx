import { useEffect, useState } from 'react';
import { Package, Search, Filter, Plus, ArrowUpDown, AlertTriangle } from 'lucide-react';

export default function Inventory() {
  const [items, setItems] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Mock data for demo
    setItems([
      {
        id: '1',
        name: 'Tomatoes',
        brand: 'Del Monte',
        category: 'Canned Goods',
        package_type: 'can',
        count: 4,
        par_level: 2,
        expires_at: '2026-06-15',
      },
      {
        id: '2',
        name: 'Black Beans',
        brand: null,
        category: 'Canned Goods',
        package_type: 'can',
        count: 3,
        par_level: 2,
        expires_at: '2027-01-10',
      },
      {
        id: '3',
        name: 'Cereal',
        brand: "Cheerios",
        category: 'Breakfast',
        package_type: 'box',
        count: 1,
        par_level: 1,
        expires_at: '2026-04-20',
      },
      {
        id: '4',
        name: 'Peanut Butter',
        brand: "Jif",
        category: 'Pantry',
        package_type: 'jar',
        count: 1,
        par_level: 0,
        expires_at: '2026-08-30',
      },
    ]);
  }, []);

  const filteredItems = items.filter(item =>
    item.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const lowStockItems = items.filter(item => item.count <= item.par_level);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Inventory</h2>
        <button className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700">
          <Plus size={16} />
          Add Item
        </button>
      </div>

      {/* Filters & Search */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search size={20} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search items..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <button className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border rounded-lg hover:bg-gray-50">
          <Filter size={16} />
          Filter
        </button>
        <button className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border rounded-lg hover:bg-gray-50">
          <ArrowUpDown size={16} />
          Sort
        </button>
      </div>

      {/* Low Stock Alert */}
      {lowStockItems.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-center gap-3">
          <AlertTriangle size={20} className="text-yellow-600" />
          <div>
            <p className="font-medium text-yellow-800">Low Stock Alert</p>
            <p className="text-sm text-yellow-700">
              {lowStockItems.length} items at or below par level
            </p>
          </div>
        </div>
      )}

      {/* Inventory Table */}
      <div className="bg-white rounded-xl border overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-6 py-3 text-left text-sm font-medium text-gray-500">Item</th>
              <th className="px-6 py-3 text-left text-sm font-medium text-gray-500">Category</th>
              <th className="px-6 py-3 text-left text-sm font-medium text-gray-500">Type</th>
              <th className="px-6 py-3 text-center text-sm font-medium text-gray-500">Stock</th>
              <th className="px-6 py-3 text-left text-sm font-medium text-gray-500">Expiry</th>
              <th className="px-6 py-3 text-left text-sm font-medium text-gray-500">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {filteredItems.map((item) => (
              <tr key={item.id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                      <Package size={20} className="text-gray-500" />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{item.name}</p>
                      {item.brand && (
                        <p className="text-sm text-gray-500">{item.brand}</p>
                      )}
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 text-sm text-gray-600">{item.category}</td>
                <td className="px-6 py-4">
                  <span className="px-2 py-1 text-xs font-medium text-gray-600 bg-gray-100 rounded">
                    {item.package_type}
                  </span>
                </td>
                <td className="px-6 py-4 text-center">
                  <span className={`text-lg font-semibold ${
                    item.count <= item.par_level ? 'text-red-600' : 'text-gray-900'
                  }`}>
                    {item.count}
                  </span>
                  <span className="text-gray-400 text-sm"> / {item.par_level}</span>
                </td>
                <td className="px-6 py-4 text-sm text-gray-600">
                  {new Date(item.expires_at).toLocaleDateString()}
                </td>
                <td className="px-6 py-4">
                  <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                    Edit
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Summary */}
      <div className="flex items-center justify-between text-sm text-gray-500">
        <p>Showing {filteredItems.length} of {items.length} items</p>
        <div className="flex gap-4">
          <span>{lowStockItems.length} low stock</span>
          <span>{items.filter(i => new Date(i.expires_at) < new Date('2026-03-01')).length} expiring soon</span>
        </div>
      </div>
    </div>
  );
}
