import { useEffect, useState } from 'react';
import { MapPin, Plus, Trash2, Brain, Target, TrendingUp } from 'lucide-react';
import * as api from '../api/client';

export default function Zones() {
  const [zones, setZones] = useState([]);
  const [patterns, setPatterns] = useState([]);
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddZone, setShowAddZone] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadZones();
  }, []);

  const loadZones = async () => {
    setLoading(true);
    setError(null);
    try {
      const devData = await api.listDevices();
      const devs = devData?.items ?? devData ?? [];
      setDevices(devs);

      const allZones = [];
      const allPatterns = [];
      for (const dev of devs) {
        const zoneList = await api.getZonesByDevice(dev.id);
        for (const zone of zoneList || []) {
          allZones.push({ ...zone, device_name: dev.name });
          try {
            const pats = await api.getZonePatterns(zone.id);
            allPatterns.push(...(pats || []));
          } catch {
            // patterns unavailable for this zone — ignore
          }
        }
      }
      setZones(allZones);
      setPatterns(allPatterns);
    } catch (err) {
      console.error('Failed to load zones:', err);
      setZones([]);
      setPatterns([]);
      setError('Could not load zones. Check that a camera device is registered.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteZone = async (zoneId) => {
    try {
      await api.deleteZone(zoneId);
      setZones(zones.filter(z => z.id !== zoneId));
      setPatterns(patterns.filter(p => p.zone_id !== zoneId));
    } catch (err) {
      console.error('Failed to delete zone:', err);
      setError('Failed to delete zone.');
    }
  };

  const handleCreateZone = async (e) => {
    e.preventDefault();
    const form = e.target;
    const deviceId = form.deviceId.value;
    const payload = {
      name: form.name.value.trim(),
      x: parseFloat(form.x.value),
      y: parseFloat(form.y.value),
      width: parseFloat(form.width.value),
      height: parseFloat(form.height.value),
      expected_item_type: form.expectedItemType.value.trim() || null,
      notes: form.notes.value.trim() || null,
    };
    if (!deviceId || !payload.name) return;
    setSaving(true);
    setError(null);
    try {
      await api.createZone(deviceId, payload);
      setShowAddZone(false);
      await loadZones();
    } catch (err) {
      console.error('Failed to create zone:', err);
      setError('Failed to create zone. Check the device and try again.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Zones & ML Learning</h2>
          <p className="text-sm text-gray-500">Configure shelf zones and view learned patterns</p>
        </div>
        <button
          onClick={() => setShowAddZone(true)}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
        >
          <Plus size={16} />
          Add Zone
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3">
          {error}
        </div>
      )}

      {/* Zone Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border p-4 sm:p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-blue-50 rounded-lg text-blue-600">
              <MapPin size={20} />
            </div>
            <p className="text-sm text-gray-500">Active Zones</p>
          </div>
          <p className="text-3xl font-bold text-gray-900">{zones.filter(z => z.is_active).length}</p>
        </div>
        <div className="bg-white rounded-xl border p-4 sm:p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-purple-50 rounded-lg text-purple-600">
              <Brain size={20} />
            </div>
            <p className="text-sm text-gray-500">Learned Patterns</p>
          </div>
          <p className="text-3xl font-bold text-gray-900">{patterns.length}</p>
        </div>
        <div className="bg-white rounded-xl border p-4 sm:p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-green-50 rounded-lg text-green-600">
              <TrendingUp size={20} />
            </div>
            <p className="text-sm text-gray-500">Avg Confidence</p>
          </div>
          <p className="text-3xl font-bold text-gray-900">
            {patterns.length > 0
              ? Math.round(patterns.reduce((a, p) => a + p.confidence_score, 0) / patterns.length * 100)
              : 0}%
          </p>
        </div>
      </div>

      {/* Zones List */}
      <div className="bg-white rounded-xl border">
        <div className="px-4 sm:px-6 py-4 border-b">
          <h3 className="text-lg font-semibold text-gray-900">Shelf Zones</h3>
        </div>
        <div className="divide-y">
          {loading ? (
            <p className="p-6 text-sm text-gray-400">Loading zones…</p>
          ) : zones.length === 0 ? (
            <p className="p-6 text-sm text-gray-400 italic">
              No zones yet. Add a zone to define a shelf region for ML learning.
            </p>
          ) : (
            zones.map((zone) => (
              <div key={zone.id} className="p-4 sm:p-6">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4">
                    <div className="w-16 h-16 bg-gray-100 rounded-lg flex items-center justify-center">
                      <div
                        className="bg-blue-200 rounded"
                        style={{
                          width: `${zone.width * 60}px`,
                          height: `${zone.height * 60}px`,
                        }}
                      />
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900">{zone.name}</h4>
                      <p className="text-sm text-gray-500">
                        {zone.device_name ? `${zone.device_name} • ` : ''}Position: ({zone.x}, {zone.y}) • Size: {zone.width}x{zone.height}
                      </p>
                      <div className="flex items-center gap-2 mt-2">
                        <span className="px-2 py-1 text-xs font-medium text-blue-700 bg-blue-100 rounded">
                          {zone.expected_item_type || 'any item'}
                        </span>
                        <span className={`px-2 py-1 text-xs font-medium rounded ${
                          zone.is_active
                            ? 'text-green-700 bg-green-100'
                            : 'text-gray-700 bg-gray-100'
                        }`}>
                          {zone.is_active ? 'active' : 'inactive'}
                        </span>
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => handleDeleteZone(zone.id)}
                    className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                    title="Delete zone"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>

                {/* Patterns for this zone */}
                <div className="mt-4 ml-20">
                  <h5 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                    <Target size={14} />
                    Learned Patterns
                  </h5>
                  {patterns
                    .filter((p) => p.zone_id === zone.id)
                    .map((pattern, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between p-3 bg-gray-50 rounded-lg mb-2"
                      >
                        <div>
                          <p className="font-medium text-gray-900">{pattern.item_name}</p>
                          <p className="text-sm text-gray-500">
                            {pattern.occurrence_count} sightings • avg {pattern.avg_quantity} items
                          </p>
                        </div>
                        <div className="text-right">
                          <span className="text-2xl font-bold text-green-600">
                            {Math.round(pattern.confidence_score * 100)}%
                          </span>
                          <p className="text-xs text-gray-500">confidence</p>
                        </div>
                      </div>
                    ))}
                  {patterns.filter((p) => p.zone_id === zone.id).length === 0 && (
                    <p className="text-sm text-gray-400 italic">
                      No patterns learned yet. Place items here and capture images.
                    </p>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Add Zone Modal */}
      {showAddZone && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Add Zone</h3>
            <form onSubmit={handleCreateZone} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Device</label>
                <select
                  name="deviceId"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {devices.length === 0 && <option value="">No devices registered</option>}
                  {devices.map((dev) => (
                    <option key={dev.id} value={dev.id}>
                      {dev.name} ({dev.id})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Zone Name</label>
                <input
                  name="name"
                  required
                  placeholder="e.g. Top shelf, canned goods"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="grid grid-cols-4 gap-3">
                {[
                  ['x', 'X'],
                  ['y', 'Y'],
                  ['width', 'W'],
                  ['height', 'H'],
                ].map(([field, label]) => (
                  <div key={field}>
                    <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
                    <input
                      name={field}
                      type="number"
                      step="0.01"
                      min="0"
                      required
                      placeholder="0.0"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                ))}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Expected Item Type <span className="text-gray-400">(optional)</span>
                </label>
                <input
                  name="expectedItemType"
                  placeholder="e.g. Canned goods"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notes <span className="text-gray-400">(optional)</span>
                </label>
                <textarea
                  name="notes"
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              {error && <p className="text-sm text-red-600">{error}</p>}
              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddZone(false)}
                  className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving || devices.length === 0}
                  className="flex-1 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {saving ? 'Creating…' : 'Create Zone'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
