import { useEffect, useMemo, useRef, useState } from 'react';
import { MapPin, Package, Pencil, Plus, Search, Trash2, X } from 'lucide-react';
import * as api from '../api/client';

const emptyForm = { name: '', category: '', quantity: 1, unit: '', location: '', condition: 'Unknown', notes: '' };

export default function Gear() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [search, setSearch] = useState('');
  const [formOpen, setFormOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [formError, setFormError] = useState('');
  const [saving, setSaving] = useState(false);
  const [actionError, setActionError] = useState('');
  const formNameRef = useRef(null);
  const returnFocusRef = useRef(null);

  const loadGear = async () => {
    setLoading(true);
    setLoadError('');
    try {
      const result = await api.listGear();
      setItems(result.items || []);
    } catch {
      setLoadError("Couldn't load gear. Check your connection, then retry.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadGear(); }, []);

  useEffect(() => {
    if (formOpen) {
      formNameRef.current?.focus();
    } else if (!loading && returnFocusRef.current) {
      const trigger = returnFocusRef.current.type === 'add'
        ? document.querySelector('[data-gear-add-trigger]')
        : [...document.querySelectorAll('[data-gear-edit-trigger]')]
          .find((button) => button.dataset.gearEditTrigger === returnFocusRef.current.id);
      trigger?.focus();
      returnFocusRef.current = null;
    }
  }, [formOpen, items, loading]);

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return items;
    return items.filter((item) => [item.name, item.category, item.location, item.notes]
      .some((value) => value?.toLowerCase().includes(query)));
  }, [items, search]);

  const openAdd = () => {
    returnFocusRef.current = { type: 'add' };
    setEditingId(null);
    setForm(emptyForm);
    setFormError('');
    setActionError('');
    setFormOpen(true);
  };

  const openEdit = (item) => {
    returnFocusRef.current = { type: 'edit', id: item.id };
    setEditingId(item.id);
    setForm({ ...emptyForm, ...item, unit: item.unit || '', location: item.location || '', notes: item.notes || '' });
    setFormError('');
    setActionError('');
    setFormOpen(true);
  };

  const updateField = (event) => {
    const { name, value } = event.target;
    setForm((previous) => ({ ...previous, [name]: value }));
  };

  const saveGear = async (event) => {
    event.preventDefault();
    if (!form.name.trim()) return setFormError('Item name is required.');
    if (!form.category.trim()) return setFormError('Category is required.');
    if (form.quantity === '' || !Number.isFinite(Number(form.quantity)) || Number(form.quantity) < 0) return setFormError('Quantity must be zero or more.');
    setSaving(true);
    setFormError('');
    setActionError('');
    const payload = { ...form, name: form.name.trim(), category: form.category.trim(), quantity: Number(form.quantity), unit: form.unit.trim() || null, location: form.location.trim() || null, notes: form.notes.trim() || null };
    try {
      if (editingId) await api.updateGear(editingId, payload);
      else await api.createGear(payload);
      setFormOpen(false);
      await loadGear();
    } catch {
      setActionError("Couldn't save gear. Check your connection and try again.");
    } finally {
      setSaving(false);
    }
  };

  const removeGear = async (item) => {
    if (!window.confirm(`Delete ${item.name} from your gear inventory?`)) return;
    setActionError('');
    try {
      await api.deleteGear(item.id);
      await loadGear();
    } catch {
      setActionError("Couldn't delete that item. Check your connection and try again.");
    }
  };

  return (
    <section className="mx-auto max-w-5xl space-y-6" aria-labelledby="gear-heading">
      <header className="flex flex-col gap-4 border-b border-gray-200 pb-5 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 id="gear-heading" className="text-2xl font-bold tracking-tight text-gray-900 sm:text-3xl">Prepping Gear</h1>
          <p className="mt-1 text-sm text-gray-600">Keep track of the equipment and supplies you rely on.</p>
        </div>
        <button type="button" onClick={openAdd} data-gear-add-trigger hidden={formOpen} style={formOpen ? { display: 'none' } : undefined} className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"><Plus size={17} aria-hidden="true" />Add gear</button>
      </header>

      {actionError && <p role="alert" className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-800">{actionError}</p>}

      {formOpen && (
        <form onSubmit={saveGear} className="space-y-4 rounded-xl border border-gray-200 bg-white p-4 shadow-sm sm:p-6" aria-labelledby="gear-form-heading">
          <div className="flex items-center justify-between gap-3">
            <h2 id="gear-form-heading" className="text-lg font-semibold text-gray-900">{editingId ? 'Edit gear' : 'Add gear'}</h2>
            <button type="button" onClick={() => setFormOpen(false)} aria-label="Close gear form" className="rounded-md p-2 text-gray-600 hover:bg-gray-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-600"><X size={18} aria-hidden="true" /></button>
          </div>
          {formError && <p role="alert" className="text-sm font-medium text-red-700">{formError}</p>}
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Item name" name="name" value={form.name} onChange={updateField} inputRef={formNameRef} required placeholder="e.g. Camp stove" />
            <Field label="Category" name="category" value={form.category} onChange={updateField} required placeholder="e.g. Stove, fuel, solar, battery" />
            <Field label="Quantity" name="quantity" type="number" min="0" step="any" value={form.quantity} onChange={updateField} required />
            <Field label="Unit" name="unit" value={form.unit} onChange={updateField} placeholder="e.g. cans, Wh, gallons" />
            <Field label="Storage location" name="location" value={form.location} onChange={updateField} placeholder="e.g. Garage shelf" />
            <div>
              <label htmlFor="gear-condition" className="mb-1 block text-sm font-medium text-gray-700">Condition</label>
              <select id="gear-condition" name="condition" value={form.condition} onChange={updateField} className="min-h-11 w-full rounded-lg border border-gray-300 bg-white px-3 text-sm text-gray-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-indigo-600">
                <option>Unknown</option><option>Good</option><option>Needs attention</option>
              </select>
            </div>
            <div className="sm:col-span-2">
              <label htmlFor="gear-notes" className="mb-1 block text-sm font-medium text-gray-700">Notes</label>
              <textarea id="gear-notes" name="notes" rows="2" value={form.notes} onChange={updateField} className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-indigo-600" placeholder="Optional details" />
            </div>
          </div>
          <div className="flex flex-col-reverse gap-2 border-t border-gray-100 pt-4 sm:flex-row sm:justify-end">
            <button type="button" onClick={() => setFormOpen(false)} className="min-h-11 rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-600">Cancel</button>
            <button type="submit" disabled={saving} className="min-h-11 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600">{saving ? 'Saving…' : 'Save gear'}</button>
          </div>
        </form>
      )}

      <div className="relative max-w-xl">
        <Search size={18} aria-hidden="true" className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
        <label className="sr-only" htmlFor="gear-search">Search gear</label>
        <input id="gear-search" type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search gear, category, location, notes…" className="min-h-11 w-full rounded-lg border border-gray-300 bg-white py-2 pl-10 pr-3 text-sm text-gray-900 placeholder:text-gray-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-indigo-600" />
      </div>

      {loading ? <p role="status" className="py-8 text-center text-sm text-gray-600">Loading gear…</p> : loadError ? (
        <div className="rounded-xl border border-red-200 bg-red-50 p-5 text-center">
          <p role="alert" className="text-sm font-medium text-red-800">{loadError}</p>
          <button type="button" onClick={loadGear} className="mt-3 min-h-11 rounded-lg border border-red-300 bg-white px-4 text-sm font-semibold text-red-800 hover:bg-red-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-600">Retry</button>
        </div>
      ) : filtered.length === 0 ? (
        <div className="rounded-xl border border-dashed border-gray-300 bg-white px-5 py-12 text-center">
          <Package size={28} aria-hidden="true" className="mx-auto text-gray-500" />
          <h2 className="mt-3 text-base font-semibold text-gray-900">{items.length ? 'No matching gear' : 'No gear added yet'}</h2>
          <p className="mt-1 text-sm text-gray-600">{items.length ? 'Try another search.' : 'Add your stove, fuel, solar gear, batteries, and other supplies.'}</p>
        </div>
      ) : (
        <ul className="divide-y divide-gray-200 rounded-xl border border-gray-200 bg-white" aria-label="Gear inventory">
          {filtered.map((item) => (
            <li key={item.id} className="flex flex-col gap-4 p-4 sm:flex-row sm:items-start sm:justify-between sm:p-5">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                  <h2 className="break-words text-base font-semibold text-gray-900">{item.name}</h2>
                  <span className="rounded-full bg-indigo-50 px-2.5 py-1 text-xs font-medium text-indigo-800">{item.category}</span>
                </div>
                <p className="mt-2 text-sm text-gray-700">Quantity: <span className="font-semibold text-gray-900">{item.quantity}{item.unit ? ` ${item.unit}` : ''}</span></p>
                <p className="mt-1 text-sm text-gray-700">Condition: <span className={item.condition === 'Needs attention' ? 'font-semibold text-amber-800' : 'font-medium text-gray-900'}>{item.condition}</span></p>
                {item.location && <p className="mt-1 flex items-start gap-1.5 text-sm text-gray-600"><MapPin size={15} aria-hidden="true" className="mt-0.5 shrink-0" />{item.location}</p>}
                {item.notes && <p className="mt-2 whitespace-pre-wrap break-words text-sm text-gray-600"><span className="font-medium text-gray-700">Notes:</span> {item.notes}</p>}
              </div>
              <div className="flex shrink-0 gap-2 sm:justify-end">
                <button type="button" onClick={() => openEdit(item)} data-gear-edit-trigger={item.id} aria-label={`Edit ${item.name}`} className="inline-flex min-h-11 items-center gap-1.5 rounded-lg border border-gray-300 px-3 text-sm font-medium text-gray-700 hover:bg-gray-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-600"><Pencil size={15} aria-hidden="true" />Edit</button>
                <button type="button" onClick={() => removeGear(item)} aria-label={`Delete ${item.name}`} className="inline-flex min-h-11 items-center gap-1.5 rounded-lg border border-red-200 px-3 text-sm font-medium text-red-800 hover:bg-red-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-600"><Trash2 size={15} aria-hidden="true" />Delete</button>
              </div>
            </li>
          ))}
        </ul>
      )}
      {!loading && !loadError && items.length > 0 && <p className="text-sm text-gray-600">Showing {filtered.length} of {items.length} gear items</p>}
    </section>
  );
}

function Field({ label, name, value, onChange, type = 'text', inputRef, ...props }) {
  return <div>
    <label htmlFor={`gear-${name}`} className="mb-1 block text-sm font-medium text-gray-700">{label}{props.required && <span aria-hidden="true"> *</span>}</label>
    <input ref={inputRef} id={`gear-${name}`} name={name} type={type} value={value} onChange={onChange} className="min-h-11 w-full rounded-lg border border-gray-300 px-3 text-sm text-gray-900 placeholder:text-gray-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-indigo-600" {...props} />
  </div>;
}
