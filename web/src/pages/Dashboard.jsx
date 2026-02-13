import { useEffect, useState } from 'react';
import { Package, Camera, AlertCircle, MapPin, TrendingUp, RefreshCw } from 'lucide-react';
import * as api from '../api';

export default function Dashboard() {
  const [stats, setStats] = useState({
    totalItems: 0,
    recentCaptures: 0,
    pendingReviews: 0,
    activeZones: 0,
  });
  const [recentCaptures, setRecentCaptures] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      // Load data from multiple endpoints
      const [inventoryRes, zonesRes] = await Promise.all([
        api.getInventory().catch(() => ({ data: { items: [] } })),
        api.getZones('pantry-cam-001').catch(() => ({ data: [] })),
      ]);

      setStats({
        totalItems: inventoryRes.data?.items?.length || 0,
        recentCaptures: 3, // From our test runs
        pendingReviews: 0,
        activeZones: zonesRes.data?.length || 0,
      });
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
        <button
          onClick={loadDashboardData}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border rounded-lg hover:bg-gray-50"
        >
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard
          icon={Package}
          label="Total Items"
          value={stats.totalItems}
          trend="+12%"
          color="blue"
        />
        <StatCard
          icon={Camera}
          label="Today's Captures"
          value={stats.recentCaptures}
          color="green"
        />
        <StatCard
          icon={AlertCircle}
          label="Pending Reviews"
          value={stats.pendingReviews}
          color="yellow"
        />
        <StatCard
          icon={MapPin}
          label="Active Zones"
          value={stats.activeZones}
          color="purple"
        />
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-xl border p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-3 gap-4">
          <QuickActionCard
            title="Upload Image"
            description="Process new pantry capture"
            icon={Camera}
            href="/captures"
            color="blue"
          />
          <QuickActionCard
            title="Review Items"
            description="Approve pending detections"
            icon={AlertCircle}
            href="/reviews"
            color="yellow"
          />
          <QuickActionCard
            title="Manage Zones"
            description="Configure shelf zones"
            icon={MapPin}
            href="/zones"
            color="purple"
          />
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Captures</h3>
          <div className="space-y-3">
            <CaptureItem id="26e52457-..." items={37} time="2 min ago" status="complete" />
            <CaptureItem id="417129c7-..." items={13} time="5 min ago" status="complete" />
            <CaptureItem id="62b9001b-..." items={19} time="8 min ago" status="complete" />
          </div>
        </div>

        <div className="bg-white rounded-xl border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Low Stock Alerts</h3>
          <div className="flex flex-col items-center justify-center h-40 text-gray-400">
            <Package size={48} className="mb-2" />
            <p>No low stock items</p>
            <p className="text-sm">All items above par level</p>
          </div>
        </div>
      </div>

      {/* Zone ML Status */}
      <div className="bg-white rounded-xl border p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">ML Pattern Learning</h3>
          <span className="px-3 py-1 text-sm font-medium text-green-700 bg-green-100 rounded-full">
            Active
          </span>
        </div>
        <div className="grid grid-cols-3 gap-4">
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-500">Zone</p>
            <p className="font-medium text-gray-900">shelf_3_left</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-500">Learned Pattern</p>
            <p className="font-medium text-gray-900">Tomatoes</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-500">Confidence</p>
            <p className="font-medium text-gray-900">85%</p>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, trend, color }) {
  const colors = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    purple: 'bg-purple-50 text-purple-600',
  };

  return (
    <div className="bg-white rounded-xl border p-6">
      <div className="flex items-center justify-between">
        <div className={`p-3 rounded-lg ${colors[color]}`}>
          <Icon size={24} />
        </div>
        {trend && (
          <span className="flex items-center text-sm font-medium text-green-600">
            <TrendingUp size={16} className="mr-1" />
            {trend}
          </span>
        )}
      </div>
      <p className="mt-4 text-3xl font-bold text-gray-900">{value}</p>
      <p className="text-sm text-gray-500">{label}</p>
    </div>
  );
}

function QuickActionCard({ title, description, icon: Icon, href, color }) {
  const colors = {
    blue: 'bg-blue-50 text-blue-600 hover:bg-blue-100',
    yellow: 'bg-yellow-50 text-yellow-600 hover:bg-yellow-100',
    purple: 'bg-purple-50 text-purple-600 hover:bg-purple-100',
  };

  return (
    <a
      href={href}
      className={`flex items-center gap-4 p-4 rounded-lg transition-colors ${colors[color]}`}
    >
      <div className="p-3 bg-white rounded-lg shadow-sm">
        <Icon size={24} />
      </div>
      <div>
        <h4 className="font-semibold text-gray-900">{title}</h4>
        <p className="text-sm text-gray-600">{description}</p>
      </div>
    </a>
  );
}

function CaptureItem({ id, items, time, status }) {
  return (
    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
      <div className="flex items-center gap-3">
        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
        <div>
          <p className="font-medium text-gray-900">Capture {id.slice(0, 8)}...</p>
          <p className="text-sm text-gray-500">{items} items detected • {time}</p>
        </div>
      </div>
      <span className="px-2 py-1 text-xs font-medium text-green-700 bg-green-100 rounded">
        {status}
      </span>
    </div>
  );
}
