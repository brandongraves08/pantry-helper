import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import { Package, Camera, MapPin, Users, Settings, Home, ShoppingCart } from 'lucide-react';

// Page components
import Dashboard from './pages/Dashboard';
import Inventory from './pages/Inventory';
import Captures from './pages/Captures';
import Zones from './pages/Zones';
import Reviews from './pages/Reviews';
import Household from './pages/Household';
import SettingsPage from './pages/Settings';

function Layout({ children }) {
  return (
    <div className="min-h-screen bg-gray-50">
      <aside className="fixed left-0 top-0 h-full w-64 bg-white border-r border-gray-200">
        <div className="p-6 border-b">
          <h1 className="text-xl font-bold text-gray-900">Pantry Inventory</h1>
          <p className="text-sm text-gray-500">Smart Food Tracking</p>
        </div>
        
        <nav className="p-4 space-y-1">
          <NavItem to="/" icon={Home} label="Dashboard" />
          <NavItem to="/inventory" icon={Package} label="Inventory" />
          <NavItem to="/captures" icon={Camera} label="Captures" />
          <NavItem to="/zones" icon={MapPin} label="Zones & ML" />
          <NavItem to="/reviews" icon={ShoppingCart} label="Review Queue" />
          <NavItem to="/household" icon={Users} label="Household" />
          <NavItem to="/settings" icon={Settings} label="Settings" />
        </nav>
        
        <div className="absolute bottom-0 w-64 p-4 border-t bg-white">
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span>System Online</span>
          </div>
        </div>
      </aside>
      
      <main className="ml-64 p-6">
        {children}
      </main>
    </div>
  );
}

function NavItem({ to, icon: Icon, label }) {
  return (
    <NavLink
      to={to}
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
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/inventory" element={<Inventory />} />
          <Route path="/captures" element={<Captures />} />
          <Route path="/zones" element={<Zones />} />
          <Route path="/reviews" element={<Reviews />} />
          <Route path="/household" element={<Household />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
