import { useEffect, useState } from 'react';
import {
  CalendarDays, Plus, Trash2, Loader, ShoppingCart, Check,
  ChevronLeft, ChevronRight, X, Search, AlertTriangle, Info,
} from 'lucide-react';
import * as api from '../api/client';

const MEAL_TYPES = ['breakfast', 'lunch', 'dinner', 'snack'];
const MEAL_LABELS = { breakfast: 'Breakfast', lunch: 'Lunch', dinner: 'Dinner', snack: 'Snack' };
const STATUS_STYLES = {
  ok: 'bg-green-50 text-green-700 border-green-200',
  short: 'bg-red-50 text-red-700 border-red-200',
  not_tracked: 'bg-amber-50 text-amber-700 border-amber-200',
};

function mondayOf(d) {
  const dt = new Date(d);
  const day = (dt.getDay() + 6) % 7; // Mon=0
  dt.setDate(dt.getDate() - day);
  dt.setHours(0, 0, 0, 0);
  return dt;
}

function fmtDate(d) {
  return d.toISOString().slice(0, 10);
}

export default function MealPlans() {
  const [plans, setPlans] = useState([]);
  const [activePlan, setActivePlan] = useState(null); // plan object
  const [loading, setLoading] = useState(true);
  const [weekStart, setWeekStart] = useState(() => mondayOf(new Date()));

  // Add-slot picker state
  const [picker, setPicker] = useState(null); // { day: Date, mealType: string }
  const [recipes, setRecipes] = useState([]);
  const [recipeSearch, setRecipeSearch] = useState('');
  const [multiplier, setMultiplier] = useState(1);

  // Verify state
  const [verify, setVerify] = useState(null);
  const [verifying, setVerifying] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [flash, setFlash] = useState('');

  const load = async () => {
    try {
      const data = await api.listMealPlans();
      setPlans(data.plans || []);
      if (!activePlan && (data.plans || []).length) {
        setActivePlan(data.plans[0]);
      }
    } catch (err) {
      console.error('Failed to load meal plans:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadRecipes = async () => {
    try {
      const data = await api.listRecipes();
      setRecipes(data.recipes || []);
    } catch (err) {
      console.error('Failed to load recipes:', err);
      setRecipes([]);
    }
  };

  useEffect(() => {
    load();
    loadRecipes();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (activePlan) setVerify(null);
  }, [activePlan]);

  const createNewPlan = async () => {
    const ws = mondayOf(new Date());
    try {
      const plan = await api.createMealPlan({ week_start: fmtDate(ws), name: `Week of ${fmtDate(ws)}` });
      setActivePlan(plan);
      await load();
    } catch (err) {
      console.error('Failed to create plan:', err);
    }
  };

  const removePlan = async (plan) => {
    if (!window.confirm(`Delete meal plan "${plan.name || plan.week_start}"?`)) return;
    try {
      await api.deleteMealPlan(plan.id);
      if (activePlan?.id === plan.id) setActivePlan(null);
      await load();
    } catch (err) {
      console.error('Failed to delete plan:', err);
    }
  };

  const openPicker = (day, mealType) => {
    setPicker({ day, mealType });
    setRecipeSearch('');
    setMultiplier(1);
  };

  const addEntry = async () => {
    if (!picker) return;
    const recipe = recipes.find((r) => r.id === picker.recipeId);
    if (!recipe) return;
    try {
      await api.addMealPlanEntry(activePlan.id, {
        plan_date: fmtDate(picker.day),
        meal_type: picker.mealType,
        recipe_id: recipe.id,
        servings_multiplier: multiplier,
      });
      setPicker(null);
      setVerify(null);
      await load();
    } catch (err) {
      console.error('Failed to add entry:', err);
    }
  };

  const removeEntry = async (entry) => {
    try {
      await api.deleteMealPlanEntry(entry.id);
      setVerify(null);
      await load();
    } catch (err) {
      console.error('Failed to remove entry:', err);
    }
  };

  const runVerify = async () => {
    if (!activePlan) return;
    setVerifying(true);
    setVerify(null);
    try {
      const v = await api.verifyMealPlan(activePlan.id);
      setVerify(v);
    } catch (err) {
      console.error('Verify failed:', err);
    } finally {
      setVerifying(false);
    }
  };

  const pushToHeb = async () => {
    if (!activePlan) return;
    setUpdating(true);
    try {
      const res = await api.updateShoppingFromPlan(activePlan.id);
      setFlash(`Added ${res.added} missing item(s) to the HEB order list`);
      setVerify(null);
      setTimeout(() => setFlash(''), 4000);
    } catch (err) {
      console.error('Update shopping failed:', err);
      setFlash('Failed to update shopping list');
      setTimeout(() => setFlash(''), 4000);
    } finally {
      setUpdating(false);
    }
  };

  const days = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(weekStart);
    d.setDate(d.getDate() + i);
    return d;
  });

  const entriesByDay = {};
  (activePlan?.entries || []).forEach((e) => {
    const key = e.plan_date;
    (entriesByDay[key] = entriesByDay[key] || []).push(e);
  });

  const filteredRecipes = recipes.filter((r) =>
    r.name.toLowerCase().includes(recipeSearch.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12 text-gray-500">
        <Loader className="animate-spin mr-2" size={18} /> Loading meal plans…
      </div>
    );
  }

  const weekLabel = `${fmtDate(days[0])} – ${fmtDate(days[6])}`;
  const shortCount = verify?.items.filter((i) => i.status === 'short').length || 0;
  const untrackedCount = verify?.items.filter((i) => i.status === 'not_tracked').length || 0;
  const okCount = verify?.items.filter((i) => i.status === 'ok').length || 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-3">
        <CalendarDays size={20} className="text-blue-600" />
        <h1 className="text-xl font-bold text-gray-900">Meal Plans</h1>

        <select
          value={activePlan?.id || ''}
          onChange={(e) => {
            const p = plans.find((x) => x.id === e.target.value);
            setActivePlan(p || null);
          }}
          className="ml-2 border rounded px-3 py-1.5 text-sm"
        >
          <option value="">Select plan…</option>
          {plans.map((p) => (
            <option key={p.id} value={p.id}>{p.name || `Week of ${p.week_start}`}</option>
          ))}
        </select>

        {!plans.length && (
          <button
            onClick={createNewPlan}
            className="flex items-center gap-1 bg-blue-600 text-white px-3 py-1.5 rounded text-sm hover:bg-blue-700"
          >
            <Plus size={14} /> Create this week's plan
          </button>
        )}

        {activePlan && (
          <>
            <button
              onClick={() => removePlan(activePlan)}
              className="flex items-center gap-1 text-gray-500 border rounded px-3 py-1.5 text-sm hover:text-red-600"
            >
              <Trash2 size={14} /> Delete
            </button>
          </>
        )}

        <div className="flex-1" />

        {activePlan && (
          <>
            <button
              onClick={runVerify}
              disabled={verifying}
              className="flex items-center gap-1 bg-gray-800 text-white px-3 py-1.5 rounded text-sm hover:bg-gray-900 disabled:opacity-50"
            >
              {verifying ? <Loader className="animate-spin" size={14} /> : <Check size={14} />}
              Verify stock
            </button>
            <button
              onClick={pushToHeb}
              disabled={updating}
              className="flex items-center gap-1 bg-emerald-600 text-white px-3 py-1.5 rounded text-sm hover:bg-emerald-700 disabled:opacity-50"
            >
              {updating ? <Loader className="animate-spin" size={14} /> : <ShoppingCart size={14} />}
              Add missing to HEB order
            </button>
          </>
        )}
      </div>

      {flash && (
        <div className="bg-green-50 border border-green-200 text-green-700 rounded px-4 py-2 text-sm">
          {flash}
        </div>
      )}

      {/* Week navigation */}
      <div className="flex items-center gap-2 text-sm">
        <button
          onClick={() => { const d = new Date(weekStart); d.setDate(d.getDate() - 7); setWeekStart(d); }}
          className="p-1 rounded hover:bg-gray-100"
        >
          <ChevronLeft size={16} />
        </button>
        <span className="font-semibold text-gray-700">{weekLabel}</span>
        <button
          onClick={() => { const d = new Date(weekStart); d.setDate(d.getDate() + 7); setWeekStart(d); }}
          className="p-1 rounded hover:bg-gray-100"
        >
          <ChevronRight size={16} />
        </button>
        <button
          onClick={() => setWeekStart(mondayOf(new Date()))}
          className="text-blue-600 hover:underline ml-2"
        >
          This week
        </button>
      </div>

      {/* Week grid */}
      {activePlan ? (
        <div className="grid grid-cols-7 gap-2 min-w-[980px] overflow-x-auto">
          {days.map((day) => {
            const key = fmtDate(day);
            const dayEntries = entriesByDay[key] || [];
            const isToday = fmtDate(day) === fmtDate(new Date());
            return (
              <div key={key} className={`border rounded-lg p-2 ${isToday ? 'border-blue-400 bg-blue-50/40' : 'border-gray-200'}`}>
                <div className="text-xs font-bold text-gray-600 mb-1">
                  {day.toLocaleDateString('en-US', { weekday: 'short' })}
                  <span className="font-normal text-gray-400 ml-1">{day.getDate()}</span>
                </div>
                {MEAL_TYPES.map((mt) => {
                  const entries = dayEntries.filter((e) => e.meal_type === mt);
                  return (
                    <div key={mt} className="mb-1">
                      {entries.map((e) => (
                        <div key={e.id} className="bg-white border border-gray-200 rounded px-1.5 py-1 mb-1 text-xs group relative">
                          <div className="font-medium text-gray-800 leading-tight">{e.recipe_name}</div>
                          {e.servings_multiplier > 1 && (
                            <div className="text-[10px] text-gray-400">×{e.servings_multiplier}</div>
                          )}
                          <button
                            onClick={() => removeEntry(e)}
                            className="absolute -top-1 -right-1 bg-white border border-gray-200 rounded-full p-0.5 opacity-0 group-hover:opacity-100 hover:text-red-600"
                            title="Remove"
                          >
                            <X size={10} />
                          </button>
                        </div>
                      ))}
                      <button
                        onClick={() => openPicker(day, mt)}
                        className="w-full text-[10px] text-gray-400 hover:text-blue-600 border border-dashed border-gray-200 rounded px-1 py-0.5"
                      >
                        + {MEAL_LABELS[mt]}
                      </button>
                    </div>
                  );
                })}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="border border-dashed border-gray-300 rounded-lg p-10 text-center text-gray-500">
          {plans.length ? 'Select a meal plan above, or create a new week.' : 'No meal plans yet. Create one to start scheduling recipes.'}
        </div>
      )}

      {/* Verify results */}
      {verify && (
        <div className="border rounded-lg p-4 bg-white">
          <div className="flex items-center gap-2 mb-3">
            <Check size={16} className="text-emerald-600" />
            <span className="font-semibold text-gray-800">Stock check ({verify.start} → {verify.end})</span>
            <span className="text-xs text-gray-500 ml-auto">
              {okCount} ok · {shortCount} short · {untrackedCount} untracked
            </span>
          </div>
          {verify.items.length === 0 && (
            <div className="text-sm text-gray-500">Nothing planned in this window.</div>
          )}
          <div className="space-y-1 max-h-72 overflow-y-auto">
            {verify.items.map((item, idx) => (
              <div key={idx} className="flex items-center gap-2 text-sm border rounded px-2 py-1.5">
                <span className={`px-2 py-0.5 rounded text-xs font-medium border ${STATUS_STYLES[item.status] || ''}`}>
                  {item.status === 'ok' ? 'HAVE' : item.status === 'short' ? 'SHORT' : 'NOT TRACKED'}
                </span>
                <span className="font-medium text-gray-800">{item.name}</span>
                {item.required_units != null && (
                  <span className="text-gray-500 text-xs">
                    need {item.required_units}{item.approx ? '≈' : ''}
                    {item.available_units != null && <> · have {item.available_units}</>}
                    {item.missing_units > 0 && <span className="text-red-600 font-medium"> · missing {item.missing_units}</span>}
                  </span>
                )}
                {item.status !== 'ok' && item.sources?.length > 0 && (
                  <span className="text-gray-400 text-[10px] ml-auto">
                    {item.sources.map((s) => `${s.recipe}${s.servings_multiplier > 1 ? ` ×${s.servings_multiplier}` : ''}`).join(', ')}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recipe picker modal */}
      {picker && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={() => setPicker(null)}>
          <div className="bg-white rounded-xl p-5 w-[480px] max-h-[80vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-bold text-gray-900">
                Add {MEAL_LABELS[picker.mealType]} · {picker.day.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })}
              </h2>
              <button onClick={() => setPicker(null)} className="text-gray-400 hover:text-gray-600"><X size={18} /></button>
            </div>

            <div className="relative mb-3">
              <Search size={14} className="absolute left-2.5 top-2.5 text-gray-400" />
              <input
                value={recipeSearch}
                onChange={(e) => setRecipeSearch(e.target.value)}
                placeholder="Search recipes…"
                className="w-full border rounded pl-8 pr-3 py-2 text-sm"
              />
            </div>

            <div className="space-y-1 mb-3 max-h-52 overflow-y-auto">
              {filteredRecipes.map((r) => (
                <button
                  key={r.id}
                  onClick={() => setPicker({ ...picker, recipeId: r.id })}
                  className={`w-full text-left px-3 py-2 rounded text-sm border ${picker.recipeId === r.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-blue-300'}`}
                >
                  <span className="font-medium text-gray-800">{r.name}</span>
                  {r.servings && <span className="text-gray-400 text-xs ml-2">serves {r.servings}</span>}
                </button>
              ))}
              {!filteredRecipes.length && <div className="text-sm text-gray-400 p-2">No recipes match.</div>}
            </div>

            <div className="flex items-center gap-2 mb-4">
              <span className="text-sm text-gray-600">Servings multiplier</span>
              <input
                type="number"
                min="1"
                max="10"
                value={multiplier}
                onChange={(e) => setMultiplier(Math.max(1, parseInt(e.target.value) || 1))}
                className="w-20 border rounded px-2 py-1 text-sm"
              />
            </div>

            <div className="flex justify-end gap-2">
              <button onClick={() => setPicker(null)} className="px-3 py-1.5 text-sm border rounded hover:bg-gray-50">
                Cancel
              </button>
              <button
                onClick={addEntry}
                disabled={!picker.recipeId}
                className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                Schedule
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Hints */}
      {activePlan && !verify && (
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <Info size={13} />
          Verify checks planned meals against pantry stock (7-day window). Missing items land on the HEB order list.
        </div>
      )}
    </div>
  );
}
