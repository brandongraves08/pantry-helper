import { useEffect, useState } from 'react';
import { Package, Search, Filter, Plus, ArrowUpDown, AlertTriangle, Apple, X, Check, Loader } from 'lucide-react';
import * as api from '../api/client';

export default function Inventory() {
  const [items, setItems] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);

  // Nutrition state
  const [nutritionItem, setNutritionItem] = useState(null); // item object
  const [nutritionData, setNutritionData] = useState(null);
  const [nutritionSearch, setNutritionSearch] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [savingNutrition, setSavingNutrition] = useState(false);
  const [nutritionSaved, setNutritionSaved] = useState(false);

  useEffect(() => {
    loadInventory();
  }, []);

  const loadInventory = async () => {
    setLoading(true);
    try {
      const data = await api.listInventory();
      const loaded = (data.items || []).map((item, idx) => ({
        id: item.item_id || item.canonical_name || String(idx),
        item_id: item.item_id,
        name: item.canonical_name || 'Unknown',
        brand: item.brand || null,
        category: item.category || 'Uncategorized',
        package_type: item.package_type || 'other',
        count: item.count_estimate || 0,
        par_level: item.par_level || 0,
        expires_at: item.expires_at || new Date(Date.now() + 365 * 86400000).toISOString().split('T')[0],
        image_url: item.image_url || null,
      }));
      setItems(loaded);
    } catch {
      setItems([
        { id: '1', name: 'Tomatoes', brand: 'Del Monte', category: 'Canned Goods', package_type: 'can', count: 4, par_level: 2, expires_at: '2026-06-15' },
        { id: '2', name: 'Black Beans', brand: null, category: 'Canned Goods', package_type: 'can', count: 3, par_level: 2, expires_at: '2027-01-10' },
        { id: '3', name: 'Cereal', brand: 'Cheerios', category: 'Breakfast', package_type: 'box', count: 1, par_level: 1, expires_at: '2026-04-20' },
        { id: '4', name: 'Peanut Butter', brand: 'Jif', category: 'Pantry', package_type: 'jar', count: 1, par_level: 0, expires_at: '2026-08-30' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const filteredItems = items.filter(item =>
    item.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const lowStockItems = items.filter(item => item.count <= item.par_level);

  // ── Nutrition handlers ──────────────────────────────────────────

  const openNutrition = async (item) => {
    setNutritionItem(item);
    setNutritionData(null);
    setSearchResults([]);
    setNutritionSearch('');
    setNutritionSaved(false);

    try {
      const nut = await api.getItemNutrition(item.id);
      if (nut?.has_nutrition) {
        setNutritionData(nut);
      }
    } catch {}
  };

  const closeNutrition = () => {
    setNutritionItem(null);
    setNutritionData(null);
    setSearchResults([]);
    setNutritionSaved(false);
  };

  const handleNutritionSearch = async () => {
    if (!nutritionSearch.trim()) return;
    setSearching(true);
    try {
      const res = await api.lookupNutrition(nutritionSearch);
      setSearchResults(res.results || []);
    } catch {
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  const handleSelectNutrition = async (result) => {
    if (!nutritionItem) return;
    setSavingNutrition(true);
    try {
      const n = result.nutrition || {};
      await api.saveItemNutrition(nutritionItem.id, {
        source: 'openfoodfacts',
        serving_size: result.serving_size || null,
        calories_per_serving: n.energy_kcal ? Math.round(n.energy_kcal) : null,
        protein_g: n.protein_g || null,
        carbs_g: n.carbs_g || null,
        fat_g: n.fat_g || null,
        fiber_g: n.fiber_g || null,
        sodium_mg: n.sodium_g ? n.sodium_g * 1000 : null,
        sugar_g: n.sugars_g || null,
      });
      setNutritionSaved(true);
      // Refresh
      const nut = await api.getItemNutrition(nutritionItem.id);
      setNutritionData(nut);
    } catch (err) {
      console.error('Failed to save nutrition:', err);
    } finally {
      setSavingNutrition(false);
    }
  };

  // ── Render ──────────────────────────────────────────────────────

  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Inventory</h2>
        <button className="flex items-center gap-2 px-3 sm:px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700">
          <Plus size={16} />
          <span className="hidden sm:inline">Add Item</span>
        </button>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 sm:gap-4">
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
        <div className="flex gap-3">
          <button className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border rounded-lg hover:bg-gray-50 flex-1 sm:flex-none justify-center">
            <Filter size={16} />
            Filter
          </button>
          <button className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border rounded-lg hover:bg-gray-50 flex-1 sm:flex-none justify-center">
            <ArrowUpDown size={16} />
            Sort
          </button>
        </div>
      </div>

      {/* Low Stock Alert */}
      {lowStockItems.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-center gap-3">
          <AlertTriangle size={20} className="text-yellow-600 shrink-0" />
          <div className="min-w-0">
            <p className="font-medium text-yellow-800">Low Stock Alert</p>
            <p className="text-sm text-yellow-700">
              {lowStockItems.length} items at or below par level
            </p>
          </div>
        </div>
      )}

      {/* Inventory Table */}
      <div className="bg-white rounded-xl border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[600px]">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-4 sm:px-6 py-3 text-left text-sm font-medium text-gray-500">Item</th>
                <th className="px-4 sm:px-6 py-3 text-left text-sm font-medium text-gray-500 hidden sm:table-cell">Category</th>
                <th className="px-4 sm:px-6 py-3 text-left text-sm font-medium text-gray-500 hidden md:table-cell">Type</th>
                <th className="px-4 sm:px-6 py-3 text-center text-sm font-medium text-gray-500">Stock</th>
                <th className="px-4 sm:px-6 py-3 text-left text-sm font-medium text-gray-500 hidden sm:table-cell">Expiry</th>
                <th className="px-4 sm:px-6 py-3 text-left text-sm font-medium text-gray-500 hidden sm:table-cell">Nutrition</th>
                <th className="px-4 sm:px-6 py-3 text-left text-sm font-medium text-gray-500">Edit</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {filteredItems.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="px-4 sm:px-6 py-4">
                    <div className="flex items-center gap-3">
                      {item.image_url ? (
                        <img
                          src={item.image_url}
                          alt={item.name}
                          className="w-10 h-10 object-cover rounded-lg shrink-0"
                          onError={(e) => {
                            e.target.onerror = null;
                            e.target.style.display = 'none';
                            e.target.nextSibling.style.display = 'flex';
                          }}
                        />
                      ) : null}
                      <div className={"w-10 h-10 bg-gray-100 rounded-lg items-center justify-center shrink-0" + (item.image_url ? ' hidden' : ' flex')}>
                        <Package size={20} className="text-gray-500" />
                      </div>
                      <div className="min-w-0">
                        <p className="font-medium text-gray-900 truncate">{item.name}</p>
                        {item.brand && (
                          <p className="text-sm text-gray-500 truncate">{item.brand}</p>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-4 sm:px-6 py-4 text-sm text-gray-600 hidden sm:table-cell">{item.category}</td>
                  <td className="px-4 sm:px-6 py-4 hidden md:table-cell">
                    <span className="px-2 py-1 text-xs font-medium text-gray-600 bg-gray-100 rounded">
                      {item.package_type}
                    </span>
                  </td>
                  <td className="px-4 sm:px-6 py-4 text-center whitespace-nowrap">
                    <span className={`text-lg font-semibold ${
                      item.count <= item.par_level ? 'text-red-600' : 'text-gray-900'
                    }`}>
                      {item.count}
                    </span>
                    <span className="text-gray-400 text-sm"> / {item.par_level}</span>
                  </td>
                  <td className="px-4 sm:px-6 py-4 text-sm text-gray-600 hidden sm:table-cell whitespace-nowrap">
                    {new Date(item.expires_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 sm:px-6 py-4 hidden sm:table-cell">
                    <button
                      onClick={() => openNutrition(item)}
                      className="flex items-center gap-1 text-sm font-medium text-green-600 hover:text-green-800"
                    >
                      <Apple size={14} />
                      <span className="hidden sm:inline">Nutrition</span>
                    </button>
                  </td>
                  <td className="px-4 sm:px-6 py-4">
                    <button className="text-blue-600 hover:text-blue-800 text-sm font-medium whitespace-nowrap">
                      Edit
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Summary */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 text-sm text-gray-500">
        <p>Showing {filteredItems.length} of {items.length} items</p>
        <div className="flex flex-wrap gap-4">
          {lowStockItems.length > 0 && <span className="text-red-600 font-medium">{lowStockItems.length} low stock</span>}
        </div>
      </div>

      {/* ── Nutrition Modal ────────────────────────────────────────── */}
      {nutritionItem && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl w-full max-w-lg max-h-[80vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between z-10">
              <h3 className="text-lg font-semibold text-gray-900">{nutritionItem.name}</h3>
              <button onClick={closeNutrition} className="p-1 rounded hover:bg-gray-100">
                <X size={20} className="text-gray-500" />
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Existing nutrition data */}
              {nutritionData?.has_nutrition && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Apple size={18} className="text-green-600" />
                    <h4 className="font-medium text-green-800">Nutrition Facts</h4>
                    {nutritionData.source && (
                      <span className="text-xs text-green-600">({nutritionData.source})</span>
                    )}
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    {nutritionData.calories_per_serving != null && (
                      <div className="bg-white rounded p-2">
                        <span className="text-gray-500">Calories</span>
                        <p className="font-semibold text-gray-900">{nutritionData.calories_per_serving}</p>
                      </div>
                    )}
                    {nutritionData.protein_g != null && (
                      <div className="bg-white rounded p-2">
                        <span className="text-gray-500">Protein</span>
                        <p className="font-semibold text-gray-900">{nutritionData.protein_g}g</p>
                      </div>
                    )}
                    {nutritionData.carbs_g != null && (
                      <div className="bg-white rounded p-2">
                        <span className="text-gray-500">Carbs</span>
                        <p className="font-semibold text-gray-900">{nutritionData.carbs_g}g</p>
                      </div>
                    )}
                    {nutritionData.fat_g != null && (
                      <div className="bg-white rounded p-2">
                        <span className="text-gray-500">Fat</span>
                        <p className="font-semibold text-gray-900">{nutritionData.fat_g}g</p>
                      </div>
                    )}
                    {nutritionData.fiber_g != null && (
                      <div className="bg-white rounded p-2">
                        <span className="text-gray-500">Fiber</span>
                        <p className="font-semibold text-gray-900">{nutritionData.fiber_g}g</p>
                      </div>
                    )}
                    {nutritionData.sodium_mg != null && (
                      <div className="bg-white rounded p-2">
                        <span className="text-gray-500">Sodium</span>
                        <p className="font-semibold text-gray-900">{nutritionData.sodium_mg}mg</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {nutritionSaved && (
                <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg">
                  <Check size={16} className="text-green-600" />
                  <p className="text-green-700 text-sm">Nutrition data saved!</p>
                </div>
              )}

              {/* Search for nutrition data */}
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Look Up Nutrition</h4>
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Search Open Food Facts..."
                    value={nutritionSearch}
                    onChange={(e) => setNutritionSearch(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleNutritionSearch()}
                    className="flex-1 px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    onClick={handleNutritionSearch}
                    disabled={searching || !nutritionSearch.trim()}
                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                  >
                    {searching ? <Loader size={14} className="animate-spin" /> : 'Search'}
                  </button>
                </div>
              </div>

              {/* Search results */}
              {searchResults.length > 0 && (
                <div className="space-y-3">
                  <h4 className="font-medium text-gray-700 text-sm">Results ({searchResults.length})</h4>
                  {searchResults.map((result, idx) => (
                    <div key={idx} className="border rounded-lg p-4 hover:border-blue-400 transition-colors">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <p className="font-medium text-gray-900">{result.product_name || 'Unknown'}</p>
                          {result.brand && <p className="text-sm text-gray-500">{result.brand}</p>}
                          {result.category && <p className="text-xs text-gray-400 mt-0.5">{result.category}</p>}
                          {result.nutrition?.energy_kcal && (
                            <p className="text-sm text-gray-600 mt-1">
                              {Math.round(result.nutrition.energy_kcal)} kcal &middot; 
                              {result.nutrition.protein_g ? ` ${result.nutrition.protein_g}g protein` : ''}
                              {result.nutrition.carbs_g ? ` ${result.nutrition.carbs_g}g carbs` : ''}
                              {result.nutrition.fat_g ? ` ${result.nutrition.fat_g}g fat` : ''}
                            </p>
                          )}
                        </div>
                        <button
                          onClick={() => handleSelectNutrition(result)}
                          disabled={savingNutrition}
                          className="shrink-0 px-3 py-1.5 text-xs font-medium text-green-700 bg-green-100 rounded-lg hover:bg-green-200 disabled:opacity-50"
                        >
                          {savingNutrition ? <Loader size={12} className="animate-spin" /> : 'Use'}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {searchResults.length === 0 && nutritionSearch && !searching && (
                <p className="text-sm text-gray-400 text-center py-4">
                  No results found. Try a different search term.
                </p>
              )}
            </div>

            <div className="border-t px-6 py-4">
              <button onClick={closeNutrition} className="w-full px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200">
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
