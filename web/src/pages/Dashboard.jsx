import { useEffect, useState } from 'react';
import { Package, Camera, AlertCircle, MapPin, TrendingUp, RefreshCw } from 'lucide-react';
import * as api from '../api/client';

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
      const [inventoryData, capturesData, devicesData] = await Promise.all([
        api.listInventory(),
        api.listCaptures({ limit: 5 }),
        api.listDevices(),
      ]);

      const items = inventoryData?.items || [];
      const captures = capturesData?.captures || [];
      const devices = devicesData?.items || [];

      setStats({
        totalItems: items.length,
        recentCaptures: captures.filter(c => c.status === 'complete').length,
        pendingReviews: captures.filter(c => c.status === 'analyzing').length,
        activeZones: devices.filter(d => d.status === 'active').length || devices.length,
      });
      setRecentCaptures(captures.slice(0, 3));
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-3 sm:space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg sm:text-2xl font-bold text-gray-900">Dashboard</h2>
        <button
          onClick={loadDashboardData}
          className="flex items-center gap-1.5 px-2.5 sm:px-4 py-1.5 sm:py-2 text-xs sm:text-sm font-medium text-gray-700 bg-white border rounded-lg hover:bg-gray-50"
        >
          <RefreshCw size={14} />
          <span className="hidden sm:inline">Refresh</span>
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-4">
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

      {/* Quick Actions — hidden on mobile, too much noise */}
      <div className="hidden sm:block bg-white rounded-xl border p-4 sm:p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">
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
      <div className="grid grid-cols-1 gap-4 sm:gap-6">
        <div className="bg-white rounded-xl border p-3 sm:p-6">
          <h3 className="text-sm sm:text-lg font-semibold text-gray-900 mb-3 sm:mb-4">Recent Captures</h3>
          <div className="space-y-3">
            {recentCaptures.length === 0 ? (
              <p className="text-gray-400 text-center py-4 sm:py-8 text-xs sm:text-sm">No captures yet</p>
            ) : (
              recentCaptures.map((c, i) => (
                <CaptureItem key={c.id || i} id={c.id || ''} items={c.trigger_type || 'manual'} time={c.captured_at ? new Date(c.captured_at).toLocaleTimeString() : ''} status={c.status || 'stored'} />
              ))
            )}
          </div>
        </div>

        <div className="bg-white rounded-xl border p-3 sm:p-6">
          <h3 className="text-sm sm:text-lg font-semibold text-gray-900 mb-3 sm:mb-4">Low Stock Alerts</h3>
          <div className="flex flex-col items-center justify-center h-24 sm:h-40 text-gray-400">
            <Package size={32} className="sm:size-48 mb-1 sm:mb-2" />
            <p className="text-xs sm:text-base">No low stock items</p>
            <p className="text-xs sm:text-sm">All items above par level</p>
          </div>
        </div>
      </div>

      {/* Zone ML Status — hidden on mobile */}
      <div className="hidden sm:block bg-white rounded-xl border p-4 sm:p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">ML Pattern Learning</h3>
          <span className="px-3 py-1 text-sm font-medium text-green-700 bg-green-100 rounded-full">
            Active
          </span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">
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
    <div className="bg-white rounded-xl border p-3 sm:p-6">
      <div className="flex items-center justify-between">
        <div className={`p-1.5 sm:p-3 rounded-lg ${colors[color]}`}>
          <Icon size={16} className="sm:size-6" />
        </div>
        {trend && (
          <span className="flex items-center text-sm font-medium text-green-600">
            <TrendingUp size={16} className="mr-1" />
            {trend}
          </span>
        )}
      </div>
      <p className="mt-2 sm:mt-4 text-xl sm:text-3xl font-bold text-gray-900">{value}</p>
      <p className="text-xs sm:text-sm text-gray-500">{label}</p>
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
      <div className="p-3 bg-white rounded-lg shadow-sm shrink-0">
        <Icon size={24} />
      </div>
      <div className="min-w-0">
        <h4 className="font-semibold text-gray-900">{title}</h4>
        <p className="text-sm text-gray-600">{description}</p>
      </div>
    </a>
  );
}

function CaptureItem({ id, items, time, status }) {
  const statusColors = {
    complete: 'bg-green-100 text-green-700',
    analyzing: 'bg-yellow-100 text-yellow-700',
    failed: 'bg-red-100 text-red-700',
    stored: 'bg-blue-100 text-blue-700',
  };
  const dotColors = {
    complete: 'bg-green-500',
    analyzing: 'bg-yellow-500',
    failed: 'bg-red-500',
    stored: 'bg-blue-500',
  };
  const color = statusColors[status] || 'bg-gray-100 text-gray-700';
  const dot = dotColors[status] || 'bg-gray-500';
  return (
    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
      <div className="flex items-center gap-3 min-w-0">
        <div className={`w-2 h-2 rounded-full ${dot} shrink-0`} />
        <div className="min-w-0">
          <p className="font-medium text-gray-900 truncate">Capture {(id || '').slice(0, 8)}...</p>
          <p className="text-sm text-gray-500 truncate">{items} &bull; {time}</p>
        </div>
      </div>
      <span className={`px-2 py-1 text-xs font-medium rounded ${color} shrink-0`}>
        {status}
      </span>
    </div>
  );
}
