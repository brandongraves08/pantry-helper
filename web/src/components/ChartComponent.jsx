import React, { useState } from 'react'
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const data = {
  items: [
    { name: 'Milk', count: 2 },
    { name: 'Eggs', count: 8 },
    { name: 'Bread', count: 1 },
    { name: 'Butter', count: 1 },
    { name: 'Cheese', count: 3 },
  ],
  timeline: [
    { day: 'Mon', items: 12 },
    { day: 'Tue', items: 14 },
    { day: 'Wed', items: 11 },
    { day: 'Thu', items: 15 },
    { day: 'Fri', items: 18 },
    { day: 'Sat', items: 16 },
    { day: 'Sun', items: 20 },
  ],
  expiry: [
    { name: 'Fresh (0-3 days)', value: 8 },
    { name: 'Good (4-7 days)', value: 7 },
    { name: 'OK (8+ days)', value: 5 },
  ],
}

const COLORS = ['#10b981', '#6366f1', '#f59e0b']

const ChartComponent = () => {
  const [activeChart, setActiveChart] = useState('items')

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <div className="mb-6 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Inventory Analytics</h3>
        <div className="flex gap-2">
          <button
            onClick={() => setActiveChart('items')}
            className={`px-3 py-1 rounded text-sm font-medium ${
              activeChart === 'items' ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-700'
            }`}
          >
            Items
          </button>
          <button
            onClick={() => setActiveChart('timeline')}
            className={`px-3 py-1 rounded text-sm font-medium ${
              activeChart === 'timeline' ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-700'
            }`}
          >
            Timeline
          </button>
          <button
            onClick={() => setActiveChart('expiry')}
            className={`px-3 py-1 rounded text-sm font-medium ${
              activeChart === 'expiry' ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-700'
            }`}
          >
            Expiry
          </button>
        </div>
      </div>

      <div className="h-80">
        {activeChart === 'items' && (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data.items}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#10b981" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}

        {activeChart === 'timeline' && (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data.timeline}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="items" stroke="#6366f1" strokeWidth={2} dot={{ r: 6 }} />
            </LineChart>
          </ResponsiveContainer>
        )}

        {activeChart === 'expiry' && (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data.expiry}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}`}
                outerRadius={120}
                fill="#8884d8"
                dataKey="value"
              >
                {data.expiry.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}

export default ChartComponent
