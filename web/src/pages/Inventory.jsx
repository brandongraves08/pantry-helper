import { useEffect, useState } from 'react';
import { Package, Search, Filter, Plus, ArrowUpDown, AlertTriangle, Apple, X, Check, Loader, Pencil, MapPin, Star, Heart } from 'lucide-react';
import * as api from '../api/client';

export default function Inventory() {
  const [items, setItems] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);

  // Filter / sort state
  const [filterOpen, setFilterOpen] = useState(false);
  const [stockFilter, setStockFilter] = useState('all'); // all | low | out
  const [sortField, setSortField] = useState('name');
  const [sortDir, setSortDir] = useState('asc');

  // Edit / add modal state
  const [editingItem, setEditingItem] = useState(null); // null = closed
  const [editForm, setEditForm] = useState({ item_name: '', count_estimate: 1, par_level: 0, location: '', notes: '' });
  const [savingItem, setSavingItem] = useState(false);
  const [itemError, setItemError] = useState('');
  const [itemSuccess, setItemSuccess] = useState('');

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
        rating: item.rating || null,
        is_favorite: item.is_favorite || false,
        category: item.category || 'Uncategorized',
        package_type: item.package_type || 'other',
        count: item.count_estimate || 0,
        par_level: item.par_level || 0,
        expires_at: item.expires_at || new Date(Date.now() + 365 * 86400000).toISOString().split('T')[0],
        image_url: item.image_url ? `${import.meta.env.VITE_API_URL ?? ''}${item.image_url}` : null,
        location: item.location || null,
        notes: item.notes || null,
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

  const lowStockItems = items.filter(item => item.count <= item.par_level);

  // Apply search + stock filter + sort
  const filteredItems = items
    .filter(item => item.name.toLowerCase().includes(searchQuery.toLowerCase()))
    .filter(item => {
      if (stockFilter === 'low') return item.count <= item.par_level;
      if (stockFilter === 'out') return item.count <= 0;
      return true;
    })
    .sort((a, b) => {
      let cmp = 0;
      const af = a[sortField], bf = b[sortField];
      if (typeof af === 'number' && typeof bf === 'number') cmp = af - bf;
      else cmp = String(af ?? '').localeCompare(String(bf ?? ''));
      return sortDir === 'asc' ? cmp : -cmp;
    });

  // ── Edit / add handlers ──────────────────────────────────────────
  const openAdd = () => {
    setEditingItem({ id: null, isNew: true });
    setEditForm({ item_name: '', count_estimate: 1, par_level: 0, location: '', notes: '' });
    setItemError('');
    setItemSuccess('');
  };

  const openEdit = (item) => {
    setEditingItem({ id: item.id, isNew: false, itemId: item.item_id });
    setEditForm({
      item_name: item.name,
      count_estimate: item.count,
      par_level: item.par_level,
      location: item.location || '',
      notes: item.notes || '',
      brand: item.brand || '',
      rating: item.rating || null,
      is_favorite: item.is_favorite || false,
    });
    setItemError('');
    setItemSuccess('');
  };

  const closeEdit = () => {
    setEditingItem(null);
    setSavingItem(false);
  };

  const handleEditField = (key) => (e) =>
    setEditForm((f) => ({ ...f, [key]: key === 'count_estimate' || key === 'par_level' ? Number(e.target.value) : e.target.value }));

  const handleSaveItem = async () => {
    if (!editForm.item_name.trim()) {
      setItemError('Item name is required.');
      return;
    }
    setSavingItem(true);
    setItemError('');
    setItemSuccess('');
    try {
      await api.overrideInventory({
        item_name: editForm.item_name.trim(),
        count_estimate: Math.max(0, Number(editForm.count_estimate) || 0),
        par_level: editForm.par_level === '' ? null : Math.max(0, Number(editForm.par_level) || 0),
        location: editForm.location.trim() || null,
        notes: editForm.notes.trim() || null,
        brand: editForm.brand?.trim() || null,
        rating: editForm.rating || null,
        is_favorite: editForm.is_favorite || false,
      });
      setItemSuccess('Saved.');
      await loadInventory();
      setTimeout(closeEdit, 700);
    } catch (err) {
      setItemError(err?.response?.data?.detail || 'Failed to save item.');
      setSavingItem(false);
    }
  };

  const handleQuickRate = async (item, rating) => {
    try {
      await api.overrideInventory({
        item_name: item.name,
        count_estimate: item.count,
        par_level: item.par_level,
        location: item.location || null,
        notes: item.notes || null,
        brand: item.brand || null,
        rating: item.rating === rating ? null : rating,
        is_favorite: item.is_favorite || false,
      });
      await loadInventory();
    } catch (err) {
      console.error('Failed to rate item:', err);
    }
  };

  const handleQuickFavorite = async (item) => {
    try {
      await api.overrideInventory({
        item_name: item.name,
        count_estimate: item.count,
        par_level: item.par_level,
        location: item.location || null,
        notes: item.notes || null,
        brand: item.brand || null,
        rating: item.rating || null,
        is_favorite: !item.is_favorite,
      });
      await loadInventory();
    } catch (err) {
      console.error('Failed to favorite item:', err);
    }
  };

  // ── Expiry helpers ──────────────────────────────────────────────
  const today = new Date();
  const expiringSoonItems = items.filter(item => {
    if (!item.expires_at) return false;
    const d = new Date(item.expires_at);
    const days = Math.ceil((d - today) / (1000 * 60 * 60 * 24));
    return days <= 30;
  });

  function getExpiryStatus(expiresAt) {
    if (!expiresAt) return { label: '', class: '', textClass: '' };
    const d = new Date(expiresAt);
    const days = Math.ceil((d - today) / (1000 * 60 * 60 * 24));
    if (days < 0) return { label: `Expired ${Math.abs(days)}d ago`, class: 'text-red-700 bg-red-100', textClass: 'text-red-700' };
    if (days === 0) return { label: 'Expires today', class: 'text-red-700 bg-red-100', textClass: 'text-red-700' };
    if (days <= 7) return { label: `${days}d`, class: 'text-red-700 bg-red-100', textClass: 'text-red-700 font-semibold' };
    if (days <= 30) return { label: `${days}d`, class: 'text-yellow-700 bg-yellow-100', textClass: 'text-yellow-700' };
    return { label: `${days}d`, class: 'text-green-700 bg-green-100', textClass: 'text-green-600' };
  }

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
        <button onClick={openAdd} className="flex items-center gap-2 px-3 sm:px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700">
          <Plus size={16} />
          <span className="hidden sm:inline">Add Item</span>
        </button>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 sm:gap-4">
        <div className="relative flex-1 max-w-md">
          <Search size={20} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            placeholder="Search items..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div className="flex gap-3">
          <div className="relative">
            <button onClick={() => setFilterOpen(!filterOpen)} className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border rounded-lg hover:bg-gray-50 flex-1 sm:flex-none justify-center">
              <Filter size={16} />
              Filter
            </button>
            {filterOpen && (
              <div className="absolute right-0 z-30 mt-2 w-48 bg-white border rounded-lg shadow-lg p-2">
                <p className="px-2 py-1 text-xs font-semibold text-gray-400 uppercase">Stock</p>
                {[{ v: 'all', l: 'All items' }, { v: 'low', l: 'At or below par' }, { v: 'out', l: 'Out of stock' }].map((o) => (
                  <button key={o.v} onClick={() => { setStockFilter(o.v); setFilterOpen(false); }} className={`block w-full text-left px-2 py-1.5 text-sm rounded ${stockFilter === o.v ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-700 hover:bg-gray-50'}`}>
                    {o.l}
                  </button>
                ))}
              </div>
            )}
          </div>
          <button onClick={() => { setSortDir(d => d === 'asc' ? 'desc' : 'asc'); }} className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border rounded-lg hover:bg-gray-50 flex-1 sm:flex-none justify-center" title="Toggle sort order">
            <ArrowUpDown size={16} />
            Sort <span className="text-gray-400 text-xs">{sortField} {sortDir}</span>
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

      {/* Expiring Soon Alert */}
      {expiringSoonItems.length > 0 && (
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 flex items-center gap-3">
          <AlertTriangle size={20} className="text-orange-600 shrink-0" />
          <div className="min-w-0">
            <p className="font-medium text-orange-800">Expiring Soon</p>
            <p className="text-sm text-orange-700">
              {expiringSoonItems.length} items expiring within 30 days
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
                      <div className="w-10 h-10 bg-gray-100 rounded-lg overflow-hidden flex items-center justify-center shrink-0">
                        {item.image_url ? (
                          <img
                            src={item.image_url}
                            alt={item.name}
                            className="w-full h-full object-cover"
                            onError={(e) => { e.target.style.display = 'none'; }}
                          />
                        ) : null}
                        {!item.image_url && <Package size={20} className="text-gray-500" />}
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="font-medium text-gray-900 truncate">{item.name}</p>
                          <button
                            onClick={() => handleQuickFavorite(item)}
                            className={`shrink-0 ${item.is_favorite ? 'text-pink-500' : 'text-gray-300 hover:text-pink-400'}`}
                            aria-label={item.is_favorite ? 'Unfavorite' : 'Favorite'}
                          >
                            <Heart size={14} fill={item.is_favorite ? 'currentColor' : 'none'} />
                          </button>
                        </div>
                        <div className="flex items-center gap-2">
                          {item.brand && (
                            <p className="text-sm text-gray-500 truncate">{item.brand}</p>
                          )}
                          <span className="flex items-center gap-0.5 shrink-0">
                            {[1, 2, 3, 4, 5].map((n) => (
                              <button
                                key={n}
                                onClick={() => handleQuickRate(item, n)}
                                className={item.rating >= n ? 'text-amber-400' : 'text-gray-300 hover:text-amber-300'}
                                aria-label={`Rate ${n} stars`}
                              >
                                <Star size={12} fill={item.rating >= n ? 'currentColor' : 'none'} />
                              </button>
                            ))}
                          </span>
                        </div>
                        {item.location && (
                          <p className="text-xs text-gray-400 flex items-center gap-1"><MapPin size={10} /> {item.location}</p>
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
                    {(() => { const s = getExpiryStatus(item.expires_at); return <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${s.class}`}>{s.label}</span>; })()}
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
                    <button onClick={() => openEdit(item)} className="flex items-center gap-1 text-blue-600 hover:text-blue-800 text-sm font-medium whitespace-nowrap">
                      <Pencil size={14} />
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

      {/* ── Add / Edit Item Modal ─────────────────────────────────── */}
      {editingItem && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl w-full max-w-md max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">{editingItem.isNew ? 'Add Item' : `Edit ${editForm.item_name || 'Item'}`}</h3>
              <button onClick={closeEdit} className="p-1 rounded hover:bg-gray-100">
                <X size={20} className="text-gray-500" />
              </button>
            </div>
            <div className="p-6 space-y-4">
              {itemSuccess && (
                <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg">
                  <Check size={16} className="text-green-600" />
                  <p className="text-green-700 text-sm">{itemSuccess}</p>
                </div>
              )}
              {itemError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-red-700 text-sm">{itemError}</p>
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Item Name *</label>
                <input
                  type="text"
                  value={editForm.item_name}
                  onChange={handleEditField('item_name')}
                  placeholder="e.g. Black Beans"
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Count</label>
                  <input
                    type="number"
                    min="0"
                    value={editForm.count_estimate}
                    onChange={handleEditField('count_estimate')}
                    className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Par Level</label>
                  <input
                    type="number"
                    min="0"
                    value={editForm.par_level}
                    onChange={handleEditField('par_level')}
                    className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Brand</label>
                <input
                  type="text"
                  value={editForm.brand || ''}
                  onChange={handleEditField('brand')}
                  placeholder="e.g. H-E-B, Del Monte"
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Rating</label>
                  <span className="flex items-center gap-0.5">
                    {[1, 2, 3, 4, 5].map((n) => (
                      <button
                        key={n}
                        type="button"
                        onClick={() => setEditForm((f) => ({ ...f, rating: f.rating === n ? null : n }))}
                        className={`${editForm.rating >= n ? 'text-amber-400' : 'text-gray-300 hover:text-amber-300'}`}
                        aria-label={`Rate ${n} stars`}
                      >
                        <Star size={16} fill={editForm.rating >= n ? 'currentColor' : 'none'} />
                      </button>
                    ))}
                  </span>
                </div>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={editForm.is_favorite || false}
                    onChange={(e) => setEditForm((f) => ({ ...f, is_favorite: e.target.checked }))}
                    className="h-4 w-4 rounded border-gray-300"
                  />
                  <span className="flex items-center gap-1 text-sm text-gray-700">
                    <Heart size={14} className={editForm.is_favorite ? 'text-pink-500' : 'text-gray-400'} fill={editForm.is_favorite ? 'currentColor' : 'none'} />
                    Favorite
                  </span>
                </label>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
                <input
                  type="text"
                  value={editForm.location}
                  onChange={handleEditField('location')}
                  placeholder="e.g. pantry shelf A"
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                <textarea
                  rows="2"
                  value={editForm.notes}
                  onChange={handleEditField('notes')}
                  placeholder="optional"
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            <div className="border-t px-6 py-4 flex gap-3">
              <button onClick={closeEdit} className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200">
                Cancel
              </button>
              <button
                onClick={handleSaveItem}
                disabled={savingItem}
                className="flex-1 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {savingItem ? <Loader size={14} className="animate-spin inline" /> : 'Save'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
