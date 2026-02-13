import { useState } from 'react';
import { MapPin, Plus, Trash2, Brain, Target, TrendingUp } from 'lucide-react';

export default function Zones() {
  const [zones, setZones] = useState([
    {
      id: '4781b564-269a-4d69-bbc8-15e68b532225',
      name: 'shelf_3_left',
      x: 0.0,
      y: 0.6,
      width: 0.4,
      height: 0.3,
      expected_item_type: 'can',
      is_active: true,
    },
  ]);
  const [patterns, setPatterns] = useState([
    {
      zone_id: '4781b564-269a-4d69-bbc8-15e68b532225',
      item_name: 'Tomatoes',
      occurrence_count: 5,
      confidence_score: 0.85,
      avg_quantity: 4.0,
    },
  ]);
  const [showAddZone, setShowAddZone] = useState(false);

  const handleDeleteZone = (zoneId) => {
    setZones(zones.filter(z => z.id !== zoneId));
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Zones & ML Learning</h2>
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

      {/* Zone Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-blue-50 rounded-lg text-blue-600">
              <MapPin size={20} />
            </div>
            <p className="text-sm text-gray-500">Active Zones</p>
          </div>
          <p className="text-3xl font-bold text-gray-900">{zones.filter(z => z.is_active).length}</p>
        </div>
        <div className="bg-white rounded-xl border p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-purple-50 rounded-lg text-purple-600">
              <Brain size={20} />
            </div>
            <p className="text-sm text-gray-500">Learned Patterns</p>
          </div>
          <p className="text-3xl font-bold text-gray-900">{patterns.length}</p>
        </div>
        <div className="bg-white rounded-xl border p-6">
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
        <div className="px-6 py-4 border-b">
          <h3 className="text-lg font-semibold text-gray-900">Shelf Zones</h3>
        </div>
        <div className="divide-y">
          {zones.map((zone) => (
            <div key={zone.id} className="p-6">
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
                      Position: ({zone.x}, {zone.y}) • Size: {zone.width}x{zone.height}
                    </p>
                    <div className="flex items-center gap-2 mt-2">
                      <span className="px-2 py-1 text-xs font-medium text-blue-700 bg-blue-100 rounded">
                        {zone.expected_item_type}
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
          ))}
        </div>
      </div>

      {/* Add Zone Modal (placeholder) */}
      {showAddZone && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-96">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Add Zone</h3>
            <p className="text-sm text-gray-500 mb-4">
              Zone creation UI coming. Use API for now:
            </p>
            <code className="block bg-gray-100 p-3 rounded text-sm">
              POST /v1/zones/device/{'{device_id}'}
            </code>
            <button
              onClick={() => setShowAddZone(false)}
              className="mt-4 w-full px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
