import { useState } from 'react';
import { Routes, Route, NavLink } from 'react-router-dom';
import { Package, Camera, MapPin, Users, Settings, Home, ShoppingCart, ScanLine, Menu, X } from 'lucide-react';

// Page components
import Dashboard from './pages/Dashboard';
import Inventory from './pages/Inventory';
import Captures from './pages/Captures';
import Zones from './pages/Zones';
import Reviews from './pages/Reviews';
import Household from './pages/Household';
import SettingsPage from './pages/Settings';
import BarcodeScan from './pages/BarcodeScan';
import Devices from './pages/Devices';

function Layout({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const closeSidebar = () => setSidebarOpen(false);

  const sidebar = (
    <>
      {/* Logo area */}
      <div className="p-4 sm:p-6 border-b">
        <h1 className="text-xl font-bold text-gray-900">Pantry Inventory</h1>
        <p className="text-sm text-gray-500">Smart Food Tracking</p>
      </div>

      <nav className="p-4 space-y-1 flex-1 overflow-y-auto">
        <NavItem to="/" icon={Home} label="Dashboard" onClick={closeSidebar} />
        <NavItem to="/inventory" icon={Package} label="Inventory" onClick={closeSidebar} />
        <NavItem to="/barcode" icon={ScanLine} label="Scan Barcode" onClick={closeSidebar} />
        <NavItem to="/captures" icon={Camera} label="Captures" onClick={closeSidebar} />
        <NavItem to="/zones" icon={MapPin} label="Zones & ML" onClick={closeSidebar} />
        <NavItem to="/reviews" icon={ShoppingCart} label="Review Queue" onClick={closeSidebar} />
        <NavItem to="/household" icon={Users} label="Household" onClick={closeSidebar} />
        <NavItem to="/settings" icon={Settings} label="Settings" onClick={closeSidebar} />
      </nav>

      <div className="p-4 border-t bg-white shrink-0">
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <div className="w-2 h-2 bg-green-500 rounded-full" />
          <span>System Online</span>
        </div>
      </div>
    </>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={closeSidebar}
        />
      )}

      {/* Sidebar — drawer on mobile, fixed on desktop */}
      <aside
        className={`
          fixed top-0 left-0 h-full w-64 bg-white border-r border-gray-200 z-50
          flex flex-col
          transition-transform duration-300
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
          lg:translate-x-0 lg:static lg:z-auto
        `}
      >
        {sidebar}
      </aside>

      {/* Main content area */}
      <div className="lg:ml-64 min-h-screen flex flex-col">
        {/* Mobile top bar */}
        <header className="sticky top-0 z-30 bg-white border-b border-gray-200 lg:hidden">
          <div className="flex items-center justify-between px-4 py-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="p-2 -ml-2 rounded-lg hover:bg-gray-100"
              aria-label="Open menu"
            >
              <Menu size={24} className="text-gray-700" />
            </button>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold text-gray-900">Pantry Inventory</h1>
            </div>
            <div className="w-10" /> {/* spacer for symmetry */}
          </div>
        </header>

        <main className="flex-1 p-4 sm:p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}

function NavItem({ to, icon: Icon, label, onClick }) {
  return (
    <NavLink
      to={to}
      end={to === '/'}
      onClick={onClick}
      className={({ isActive }) =>
        `flex items-center gap-3 px-4 py-2 rounded-lg transition-colors ${
          isActive
            ? 'bg-blue-50 text-blue-600'
            : 'text-gray-700 hover:bg-gray-100'
        }`
      }
    >
      <Icon size={20} />
      <span className="font-medium">{label}</span>
    </NavLink>
  );
}

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/inventory" element={<Inventory />} />
        <Route path="/barcode" element={<BarcodeScan />} />
        <Route path="/captures" element={<Captures />} />
        <Route path="/zones" element={<Zones />} />
        <Route path="/reviews" element={<Reviews />} />
        <Route path="/household" element={<Household />} />
        <Route path="/devices" element={<Devices />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
    </Layout>
  );
}

export default App;
