import { useEffect, useState } from 'react';
import { Settings, Plus, Trash2, RefreshCw, Battery, Wifi, Camera, Clock, AlertTriangle, Check, X, Loader } from 'lucide-react';
import * as api from '../api/client';

export default function Devices() {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [healthData, setHealthData] = useState({});
  const [expandedId, setExpandedId] = useState(null);
  const [showRegister, setShowRegister] = useState(false);
  const [newDeviceName, setNewDeviceName] = useState('');
  const [registering, setRegistering] = useState(false);
  const [newDeviceToken, setNewDeviceToken] = useState(null);

  useEffect(() => {
    loadDevices();
  }, []);

  const loadDevices = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.listDevices();
      setDevices(data.items || []);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load devices');
    } finally {
      setLoading(false);
    }
  };

  const toggleExpand = async (deviceId) => {
    if (expandedId === deviceId) {
      setExpandedId(null);
      return;
    }
    setExpandedId(deviceId);
    if (!healthData[deviceId]) {
      try {
        const health = await api.getDeviceHealth(deviceId);
        setHealthData(prev => ({ ...prev, [deviceId]: health }));
      } catch {
        setHealthData(prev => ({ ...prev, [deviceId]: { error: 'Failed to load health' } }));
      }
    }
  };

  const handleRegister = async () => {
    if (!newDeviceName.trim()) return;
    setRegistering(true);
    setError(null);
    try {
      const result = await api.registerDevice({ name: newDeviceName.trim() });
      setNewDeviceToken(result.device_token);
      setDevices(prev => [...prev, result]);
      setNewDeviceName('');
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to register device');
    } finally {
      setRegistering(false);
    }
  };

  const handleDelete = async (deviceId) => {
    if (!window.confirm('Delete this device? This cannot be undone.')) return;
    try {
      await api.deleteDevice(deviceId);
      setDevices(prev => prev.filter(d => d.id !== deviceId));
      setExpandedId(null);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to delete device');
    }
  };

  const statusBadge = (status) => {
    const colors = {
      active: 'bg-green-100 text-green-800',
      idle: 'bg-gray-100 text-gray-600',
      error: 'bg-red-100 text-red-800',
      offline: 'bg-yellow-100 text-yellow-800',
    };
    return (
      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${colors[status] || 'bg-gray-100 text-gray-600'}`}>
        {status}
      </span>
    );
  };

  const timeAgo = (dateStr) => {
    if (!dateStr) return 'Never';
    const seconds = Math.floor((new Date() - new Date(dateStr)) / 1000);
    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

  return (
    <div className="max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Devices</h1>
          <p className="text-sm text-gray-500 mt-1">Manage connected cameras and capture devices</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={loadDevices}
            className="p-2 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100 transition-colors"
            title="Refresh"
          >
            <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => setShowRegister(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
          >
            <Plus className="w-4 h-4" />
            Add Device
          </button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700 text-sm">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span className="flex-1">{error}</span>
          <button onClick={() => setError(null)} className="hover:text-red-900">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Register Device Panel */}
      {showRegister && (
        <div className="mb-6 p-4 bg-white border border-gray-200 rounded-xl shadow-sm">
          <h3 className="text-sm font-semibold text-gray-900 mb-3">Register New Device</h3>
          {newDeviceToken ? (
            <div>
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg mb-3">
                <p className="text-xs font-medium text-blue-800 mb-1">Device Registered! Save this token — it won't be shown again.</p>
                <code className="block text-sm bg-blue-100 px-3 py-2 rounded break-all font-mono">{newDeviceToken}</code>
              </div>
              <button
                onClick={() => { setShowRegister(false); setNewDeviceToken(null); }}
                className="text-sm text-gray-600 hover:text-gray-900"
              >
                Done
              </button>
            </div>
          ) : (
            <div className="flex gap-3">
              <input
                type="text"
                value={newDeviceName}
                onChange={e => setNewDeviceName(e.target.value)}
                placeholder="Device name (e.g. Kitchen Pantry Cam)"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                onKeyDown={e => e.key === 'Enter' && handleRegister()}
              />
              <button
                onClick={handleRegister}
                disabled={!newDeviceName.trim() || registering}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {registering ? <Loader className="w-4 h-4 animate-spin" /> : 'Register'}
              </button>
              <button
                onClick={() => setShowRegister(false)}
                className="px-3 py-2 text-gray-500 hover:text-gray-700 text-sm"
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      )}

      {/* Device List */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader className="w-8 h-8 text-blue-600 animate-spin" />
        </div>
      ) : devices.length === 0 ? (
        <div className="text-center py-20 text-gray-500">
          <Settings className="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p className="text-lg font-medium">No devices registered</p>
          <p className="text-sm mt-1">Register your first camera device to get started.</p>
          <button
            onClick={() => setShowRegister(true)}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            Register Device
          </button>
        </div>
      ) : (
        <div className="space-y-2">
          {devices.map(device => (
            <div key={device.id} className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
              {/* Device Row */}
              <div
                className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => toggleExpand(device.id)}
              >
                <div className="flex items-center gap-4">
                  <div className={`p-2 rounded-lg ${device.status === 'active' ? 'bg-green-100' : 'bg-gray-100'}`}>
                    <Camera className={`w-5 h-5 ${device.status === 'active' ? 'text-green-600' : 'text-gray-400'}`} />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{device.name}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      {statusBadge(device.status)}
                      {device.battery_pct !== null && device.battery_pct !== undefined && (
                        <span className="flex items-center gap-1 text-xs text-gray-500">
                          <Battery className="w-3 h-3" />
                          {device.battery_pct}%
                        </span>
                      )}
                      <span className="flex items-center gap-1 text-xs text-gray-500">
                        <Camera className="w-3 h-3" />
                        {device.total_captures || 0} captures
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-gray-400">
                    <Clock className="w-3 h-3 inline mr-1" />
                    {timeAgo(device.last_seen_at)}
                  </span>
                  <button
                    onClick={(e) => { e.stopPropagation(); handleDelete(device.id); }}
                    className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    title="Delete device"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Expanded Health Details */}
              {expandedId === device.id && (
                <div className="border-t border-gray-100 px-4 py-3 bg-gray-50">
                  {healthData[device.id]?.error ? (
                    <p className="text-sm text-red-500">{healthData[device.id].error}</p>
                  ) : healthData[device.id] ? (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <p className="text-gray-500 text-xs font-medium uppercase tracking-wide">Health</p>
                        <p className={`font-medium mt-1 ${healthData[device.id].is_healthy ? 'text-green-600' : 'text-yellow-600'}`}>
                          {healthData[device.id].is_healthy ? 'Healthy' : 'Unhealthy'}
                        </p>
                      </div>
                      <div>
                        <p className="text-gray-500 text-xs font-medium uppercase tracking-wide">Last Seen</p>
                        <p className="font-medium mt-1">{timeAgo(healthData[device.id].last_seen_at)}</p>
                      </div>
                      <div>
                        <p className="text-gray-500 text-xs font-medium uppercase tracking-wide">Success Rate (7d)</p>
                        <p className="font-medium mt-1">{healthData[device.id].success_rate_7d?.toFixed(0) || 'N/A'}%</p>
                      </div>
                      <div>
                        <p className="text-gray-500 text-xs font-medium uppercase tracking-wide">Captures (7d)</p>
                        <p className="font-medium mt-1">{healthData[device.id].captures_7d || 0}</p>
                      </div>
                      <div>
                        <p className="text-gray-500 text-xs font-medium uppercase tracking-wide">Battery</p>
                        <p className="font-medium mt-1">
                          {healthData[device.id].battery_pct !== null
                            ? `${healthData[device.id].battery_pct}%`
                            : 'N/A'}
                        </p>
                      </div>
                      <div>
                        <p className="text-gray-500 text-xs font-medium uppercase tracking-wide">Signal (RSSI)</p>
                        <p className="font-medium mt-1">
                          {healthData[device.id].rssi !== null
                            ? `${healthData[device.id].rssi} dBm`
                            : 'N/A'}
                        </p>
                      </div>
                      <div>
                        <p className="text-gray-500 text-xs font-medium uppercase tracking-wide">Successful</p>
                        <p className="font-medium mt-1 text-green-600">{healthData[device.id].successful_7d || 0}</p>
                      </div>
                      <div>
                        <p className="text-gray-500 text-xs font-medium uppercase tracking-wide">Failed</p>
                        <p className="font-medium mt-1 text-red-600">{healthData[device.id].failed_7d || 0}</p>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center justify-center py-3">
                      <Loader className="w-5 h-5 text-gray-400 animate-spin" />
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
