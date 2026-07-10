import { useState } from 'react';
import { Settings, Server, Database, Bell, Shield, Key } from 'lucide-react';

export default function SettingsPage() {
  const [apiUrl, setApiUrl] = useState('http://localhost:8000');
  const [deviceId, setDeviceId] = useState('pantry-cam-001');

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Settings</h2>

      {/* API Configuration */}
      <div className="bg-white rounded-xl border p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-blue-50 rounded-lg text-blue-600">
            <Server size={20} />
          </div>
          <h3 className="text-lg font-semibold text-gray-900">API Configuration</h3>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              API Base URL
            </label>
            <input
              type="text"
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-sm text-gray-500 mt-1">
              Backend server endpoint
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Device ID
            </label>
            <input
              type="text"
              value={deviceId}
              onChange={(e) => setDeviceId(e.target.value)}
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-sm text-gray-500 mt-1">
              Default device for captures
            </p>
          </div>

          <div className="pt-4 border-t">
            <button className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700">
              Test Connection
            </button>
          </div>
        </div>
      </div>

      {/* Vision Models */}
      <div className="bg-white rounded-xl border p-4 sm:p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-purple-50 rounded-lg text-purple-600 shrink-0">
            <Database size={20} />
          </div>
          <h3 className="text-lg font-semibold text-gray-900">Vision Models</h3>
        </div>

        <div className="space-y-2">
          {[
            { name: 'meta/llama-3.2-11b-vision-instruct', status: 'active', cost: 'Free' },
            { name: 'meta/llama-3.2-90b-vision-instruct', status: 'available', cost: 'Free' },
            { name: 'microsoft/phi-3-vision-128k-instruct', status: 'available', cost: 'Free' },
          ].map((model) => (
            <div
              key={model.name}
              className={`flex items-center justify-between p-4 rounded-lg ${
                model.status === 'active' ? 'bg-blue-50 border border-blue-200' : 'bg-gray-50'
              }`}
            >
              <div>
                <p className="font-medium text-gray-900">{model.name}</p>
                <p className="text-sm text-gray-500">{model.cost}</p>
              </div>
              <span className={`px-3 py-1 text-xs font-medium rounded-full ${
                model.status === 'active'
                  ? 'bg-green-100 text-green-700'
                  : 'bg-gray-100 text-gray-600'
              }`}>
                {model.status}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Notifications */}
      <div className="bg-white rounded-xl border p-4 sm:p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-yellow-50 rounded-lg text-yellow-600 shrink-0">
            <Bell size={20} />
          </div>
          <h3 className="text-lg font-semibold text-gray-900">Notifications</h3>
        </div>

        <div className="space-y-3">
          <label className="flex items-center gap-3">
            <input type="checkbox" defaultChecked className="w-4 h-4 text-blue-600" />
            <span className="text-gray-700">Low stock alerts</span>
          </label>
          <label className="flex items-center gap-3">
            <input type="checkbox" defaultChecked className="w-4 h-4 text-blue-600" />
            <span className="text-gray-700">Expiry warnings</span>
          </label>
          <label className="flex items-center gap-3">
            <input type="checkbox" className="w-4 h-4 text-blue-600" />
            <span className="text-gray-700">Supply forecast alerts</span>
          </label>
          <label className="flex items-center gap-3">
            <input type="checkbox" className="w-4 h-4 text-blue-600" />
            <span className="text-gray-700">Review queue notifications</span>
          </label>
        </div>
      </div>

      {/* Security */}
      <div className="bg-white rounded-xl border p-4 sm:p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-green-50 rounded-lg text-green-600 shrink-0">
            <Shield size={20} />
          </div>
          <h3 className="text-lg font-semibold text-gray-900">Security</h3>
        </div>

        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-3">
            <Key size={20} className="text-gray-500" />
            <div>
              <p className="font-medium text-gray-900">Device Token</p>
              <p className="text-sm text-gray-500">••••••••••••••••</p>
            </div>
          </div>
          <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
            Regenerate
          </button>
        </div>
      </div>

      {/* System Info */}
      <div className="bg-gray-50 rounded-xl border p-6">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">System Information</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-gray-500">Web UI Version</p>
            <p className="font-medium text-gray-900">0.1.0</p>
          </div>
          <div>
            <p className="text-gray-500">API Version</p>
            <p className="font-medium text-gray-900">1.0.0</p>
          </div>
          <div>
            <p className="text-gray-500">Database</p>
            <p className="font-medium text-gray-900">SQLite</p>
          </div>
          <div>
            <p className="text-gray-500">Last Build</p>
            <p className="font-medium text-gray-900">{new Date().toLocaleString()}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
