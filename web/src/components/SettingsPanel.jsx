import React, { useState } from 'react'
import { Settings } from 'lucide-react'

const SettingsPanel = ({ onClose }) => {
  const [settings, setSettings] = useState({
    refreshInterval: 30,
    itemsPerPage: 20,
    enableNotifications: true,
    theme: 'light',
    autoUpload: true,
  })

  const handleChange = (key, value) => {
    setSettings((prev) => ({ ...prev, [key]: value }))
  }

  const handleSave = () => {
    localStorage.setItem('pantry-settings', JSON.stringify(settings))
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-lg">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-xl font-semibold">
            <Settings className="h-5 w-5" />
            Settings
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            ✕
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Refresh Interval (seconds)</label>
            <input
              type="number"
              value={settings.refreshInterval}
              onChange={(e) => handleChange('refreshInterval', parseInt(e.target.value))}
              min="5"
              max="300"
              className="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Items Per Page</label>
            <input
              type="number"
              value={settings.itemsPerPage}
              onChange={(e) => handleChange('itemsPerPage', parseInt(e.target.value))}
              min="5"
              max="100"
              className="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Theme</label>
            <select
              value={settings.theme}
              onChange={(e) => handleChange('theme', e.target.value)}
              className="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none"
            >
              <option value="light">Light</option>
              <option value="dark">Dark</option>
              <option value="auto">Auto</option>
            </select>
          </div>

          <div className="space-y-2">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={settings.enableNotifications}
                onChange={(e) => handleChange('enableNotifications', e.target.checked)}
                className="h-4 w-4 rounded border-gray-300 text-blue-500"
              />
              <span className="text-sm font-medium text-gray-700">Enable Notifications</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={settings.autoUpload}
                onChange={(e) => handleChange('autoUpload', e.target.checked)}
                className="h-4 w-4 rounded border-gray-300 text-blue-500"
              />
              <span className="text-sm font-medium text-gray-700">Auto-Upload Images</span>
            </label>
          </div>
        </div>

        <div className="mt-6 flex gap-2">
          <button
            onClick={handleSave}
            className="flex-1 rounded bg-blue-500 px-4 py-2 font-medium text-white hover:bg-blue-600"
          >
            Save Settings
          </button>
          <button
            onClick={onClose}
            className="flex-1 rounded bg-gray-200 px-4 py-2 font-medium text-gray-700 hover:bg-gray-300"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}

export default SettingsPanel
