import { useEffect, useState } from 'react';
import { BookOpen, Plus, Search, X, Trash2, Edit, Loader, ShoppingCart, Check, ChevronDown } from 'lucide-react';
import * as api from '../api/client';

export default function Recipes() {
  const [recipes, setRecipes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  // Modal state
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState(null); // recipe object or null
  const [form, setForm] = useState(emptyForm());
  const [saving, setSaving] = useState(false);

  // View state
  const [viewing, setViewing] = useState(null); // recipe object for detail view
  const [shoppingNeeds, setShoppingNeeds] = useState(null);
  const [checkingNeeds, setCheckingNeeds] = useState(false);

  useEffect(() => {
    loadRecipes();
  }, []);

  function emptyForm() {
    return {
      name: '',
      description: '',
      source: '',
      servings: 4,
      prep_time_min: '',
      cook_time_min: '',
      instructions: '',
      ingredients: [{ quantity: '', name: '', note: '' }],
    };
  }

  const loadRecipes = async () => {
    setLoading(true);
    try {
      const data = await api.listRecipes();
      setRecipes(data.recipes || []);
    } catch (err) {
      console.error('Failed to load recipes:', err);
      setRecipes([]);
    } finally {
      setLoading(false);
    }
  };

  const filteredRecipes = recipes.filter((r) =>
    r.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // ── Form handlers ──────────────────────────────────────────
  const openAdd = () => {
    setEditing(null);
    setForm(emptyForm());
    setShowModal(true);
  };

  const openEdit = (recipe) => {
    setEditing(recipe);
    setForm({
      name: recipe.name || '',
      description: recipe.description || '',
      source: recipe.source || '',
      servings: recipe.servings || 4,
      prep_time_min: recipe.prep_time_min || '',
      cook_time_min: recipe.cook_time_min || '',
      instructions: recipe.instructions || '',
      ingredients: (recipe.ingredients || []).length
        ? recipe.ingredients.map((i) => ({ quantity: i.quantity || '', name: i.name, note: i.note || '' }))
        : [{ quantity: '', name: '', note: '' }],
    });
    setShowModal(true);
  };

  const updateIngredient = (idx, field, value) => {
    const ing = [...form.ingredients];
    ing[idx][field] = value;
    setForm({ ...form, ingredients: ing });
  };

  const addIngredient = () => {
    setForm({ ...form, ingredients: [...form.ingredients, { quantity: '', name: '', note: '' }] });
  };

  const removeIngredient = (idx) => {
    const ing = [...form.ingredients];
    ing.splice(idx, 1);
    setForm({ ...form, ingredients: ing });
  };

  const handleSave = async () => {
    if (!form.name.trim()) return;
    setSaving(true);
    const payload = {
      name: form.name.trim(),
      description: form.description || null,
      source: form.source || null,
      servings: form.servings || null,
      prep_time_min: form.prep_time_min ? Number(form.prep_time_min) : null,
      cook_time_min: form.cook_time_min ? Number(form.cook_time_min) : null,
      instructions: form.instructions || null,
      ingredients: form.ingredients
        .filter((i) => i.name.trim())
        .map((i) => ({
          quantity: i.quantity || null,
          name: i.name.trim(),
          note: i.note || null,
        })),
    };
    try {
      if (editing) {
        await api.updateRecipe(editing.id, payload);
      } else {
        await api.createRecipe(payload);
      }
      setShowModal(false);
      await loadRecipes();
    } catch (err) {
      console.error('Failed to save recipe:', err);
      alert('Failed to save recipe');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (recipe) => {
    if (!confirm(`Delete "${recipe.name}"?`)) return;
    try {
      await api.deleteRecipe(recipe.id);
      if (viewing?.id === recipe.id) setViewing(null);
      await loadRecipes();
    } catch (err) {
      console.error('Failed to delete recipe:', err);
      alert('Failed to delete recipe');
    }
  };

  const openView = async (recipe) => {
    setViewing(recipe);
    setShoppingNeeds(null);
    setCheckingNeeds(true);
    try {
      const needs = await api.getRecipeShoppingNeeds(recipe.id);
      setShoppingNeeds(needs);
    } catch {
      setShoppingNeeds(null);
    } finally {
      setCheckingNeeds(false);
    }
  };

  // ── Render ──────────────────────────────────────────────────
  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Recipes</h2>
        <button
          onClick={openAdd}
          className="flex items-center gap-2 px-3 sm:px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
        >
          <Plus size={16} />
          <span className="hidden sm:inline">Add Recipe</span>
        </button>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search size={20} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          placeholder="Search recipes..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {loading ? (
        <div className="flex justify-center py-16">
          <Loader size={28} className="animate-spin text-gray-400" />
        </div>
      ) : filteredRecipes.length === 0 ? (
        <div className="bg-white rounded-xl border p-12 text-center">
          <BookOpen size={40} className="mx-auto text-gray-300 mb-3" />
          <p className="text-gray-500 font-medium">No recipes yet</p>
          <p className="text-sm text-gray-400 mt-1">Add your first recipe to get started</p>
          <button
            onClick={openAdd}
            className="mt-4 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
          >
            <Plus size={16} className="inline mr-1" />
            Add Recipe
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredRecipes.map((recipe) => (
            <div key={recipe.id} className="bg-white rounded-xl border p-5 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="min-w-0">
                  <button onClick={() => openView(recipe)} className="text-left hover:text-blue-600">
                    <h3 className="font-semibold text-gray-900 truncate">{recipe.name}</h3>
                  </button>
                  {recipe.source && <p className="text-xs text-gray-400 mt-0.5">{recipe.source}</p>}
                </div>
                <div className="flex gap-1 shrink-0">
                  <button
                    onClick={() => openEdit(recipe)}
                    className="p-1.5 rounded hover:bg-gray-100 text-gray-500"
                    aria-label="Edit"
                  >
                    <Edit size={15} />
                  </button>
                  <button
                    onClick={() => handleDelete(recipe)}
                    className="p-1.5 rounded hover:bg-red-50 text-red-500"
                    aria-label="Delete"
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              </div>
              {recipe.description && (
                <p className="text-sm text-gray-600 mt-2 line-clamp-2">{recipe.description}</p>
              )}
              <div className="mt-3 flex items-center justify-between text-xs text-gray-400">
                <span>{recipe.ingredients?.length || 0} ingredients</span>
                <button
                  onClick={() => openView(recipe)}
                  className="flex items-center gap-1 text-blue-600 hover:text-blue-800 font-medium"
                >
                  <ShoppingCart size={13} />
                  View
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Add/Edit Modal ─────────────────────────────────────── */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between z-10">
              <h3 className="text-lg font-semibold text-gray-900">
                {editing ? 'Edit Recipe' : 'New Recipe'}
              </h3>
              <button onClick={() => setShowModal(false)} className="p-1 rounded hover:bg-gray-100">
                <X size={20} className="text-gray-500" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Recipe Name *</label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g. Pickle Remoulade Burgers"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Source</label>
                  <input
                    type="text"
                    value={form.source}
                    onChange={(e) => setForm({ ...form, source: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="Food Network"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Servings</label>
                  <input
                    type="number"
                    value={form.servings}
                    onChange={(e) => setForm({ ...form, servings: Number(e.target.value) })}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  rows={2}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Ingredients</label>
                <div className="space-y-2">
                  {form.ingredients.map((ing, idx) => (
                    <div key={idx} className="flex gap-2 items-start">
                      <input
                        type="text"
                        value={ing.quantity}
                        onChange={(e) => updateIngredient(idx, 'quantity', e.target.value)}
                        className="w-28 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                        placeholder="1½ lb"
                      />
                      <input
                        type="text"
                        value={ing.name}
                        onChange={(e) => updateIngredient(idx, 'name', e.target.value)}
                        className="flex-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                        placeholder="Ingredient"
                      />
                      <input
                        type="text"
                        value={ing.note}
                        onChange={(e) => updateIngredient(idx, 'note', e.target.value)}
                        className="flex-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                        placeholder="Note (80/20)"
                      />
                      {form.ingredients.length > 1 && (
                        <button
                          onClick={() => removeIngredient(idx)}
                          className="p-2 rounded hover:bg-red-50 text-red-500"
                          aria-label="Remove ingredient"
                        >
                          <X size={16} />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
                <button
                  onClick={addIngredient}
                  className="mt-2 flex items-center gap-1 text-sm font-medium text-blue-600 hover:text-blue-800"
                >
                  <Plus size={14} /> Add ingredient
                </button>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Instructions</label>
                <textarea
                  value={form.instructions}
                  onChange={(e) => setForm({ ...form, instructions: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  rows={4}
                  placeholder="Steps..."
                />
              </div>
            </div>

            <div className="border-t px-6 py-4 flex justify-end gap-2">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving || !form.name.trim()}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {saving ? <Loader size={14} className="inline animate-spin" /> : 'Save Recipe'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── View/Detail Modal ──────────────────────────────────── */}
      {viewing && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between z-10">
              <div className="min-w-0">
                <h3 className="text-lg font-semibold text-gray-900 truncate">{viewing.name}</h3>
                {viewing.source && <p className="text-xs text-gray-400">{viewing.source}</p>}
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <button
                  onClick={() => openEdit(viewing)}
                  className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-blue-600 hover:text-blue-800 bg-blue-50 rounded-lg"
                >
                  <Edit size={14} /> Edit
                </button>
                <button onClick={() => setViewing(null)} className="p-1 rounded hover:bg-gray-100">
                  <X size={20} className="text-gray-500" />
                </button>
              </div>
            </div>

            <div className="p-6 space-y-6">
              {viewing.description && (
                <p className="text-gray-700">{viewing.description}</p>
              )}

              {/* Ingredients */}
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Ingredients</h4>
                <ul className="space-y-1.5">
                  {(viewing.ingredients || []).map((ing) => (
                    <li key={ing.id} className="flex items-baseline gap-2 text-sm">
                      {ing.quantity && <span className="font-medium text-gray-900">{ing.quantity}</span>}
                      <span className="text-gray-700">{ing.name}</span>
                      {ing.note && <span className="text-gray-400">({ing.note})</span>}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Shopping needs */}
              <div className="bg-gray-50 border rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <ShoppingCart size={16} className="text-gray-600" />
                  <h4 className="font-medium text-gray-900">Shopping Needs</h4>
                </div>
                {checkingNeeds ? (
                  <Loader size={16} className="animate-spin text-gray-400 mx-auto" />
                ) : shoppingNeeds ? (
                  <div className="space-y-2">
                    {shoppingNeeds.needs.length === 0 ? (
                      <p className="text-sm text-gray-500">No tracked ingredients.</p>
                    ) : (
                      shoppingNeeds.needs.map((n, idx) => (
                        <div key={idx} className="flex items-center justify-between text-sm bg-white rounded-lg px-3 py-2 border">
                          <div className="min-w-0">
                            <p className="font-medium text-gray-800 truncate">
                              {n.quantity ? `${n.quantity} ` : ''}{n.ingredient}
                            </p>
                            {n.in_inventory && (
                              <p className="text-xs text-gray-400">Tracked as "{n.item_name}"</p>
                            )}
                          </div>
                          <span
                            className={`shrink-0 px-2 py-0.5 rounded-full text-xs font-medium ${
                              n.status === 'ok'
                                ? 'text-green-700 bg-green-100'
                                : n.status === 'below_par'
                                ? 'text-red-700 bg-red-100'
                                : 'text-gray-600 bg-gray-100'
                            }`}
                          >
                            {n.status === 'ok'
                              ? 'In stock'
                              : n.status === 'below_par'
                              ? `Low (${n.count}/${n.par_level})`
                              : n.in_inventory
                              ? 'No par'
                              : 'Not tracked'}
                          </span>
                        </div>
                      ))
                    )}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">Could not load shopping needs.</p>
                )}
              </div>

              {/* Instructions */}
              {viewing.instructions && (
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Instructions</h4>
                  <p className="text-sm text-gray-700 whitespace-pre-line">{viewing.instructions}</p>
                </div>
              )}
            </div>

            <div className="border-t px-6 py-4">
              <button
                onClick={() => setViewing(null)}
                className="w-full px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}