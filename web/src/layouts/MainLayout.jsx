import { Link, useLocation, Navigate } from 'react-router-dom'
import { 
  Home, 
  Camera, 
  Package, 
  MapPin, 
  Settings, 
  Users,
  Menu,
  X
} from 'lucide-react'
import { useState } from 'react'

const NavItem = ({ to, icon: Icon, label, isActive, onClick }) => (
  <Link
    to={to}
    onClick={onClick}
    className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
      isActive
        ? 'bg-indigo-600 text-white'
        : 'text-gray-600 hover:bg-gray-100'
    }`}
  >
    <Icon size={20} />
    <span className="font-medium">{label}</span>
  </Link>
)

const Sidebar = ({ isOpen, onClose }) => {
  const location = useLocation()
  const navItems = [
    { path: '/', label: 'Dashboard', icon: Home },
    { path: '/captures', label: 'Captures', icon: Camera },
    { path: '/inventory', label: 'Inventory', icon: Package },
    { path: '/zones', label: 'Zones', icon: MapPin },
    { path: '/devices', label: 'Devices', icon: Settings },
    { path: '/members', label: 'Members', icon: Users },
  ]

  return (
    <>
      {/* Mobile Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}
      
      {/* Sidebar */}
      <aside 
        className={`fixed lg:static inset-y-0 left-0 z-50 w-64 bg-white border-r border-gray-200 transform transition-transform duration-300 lg:transform-none ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="h-full flex flex-col">
          {/* Header */}
          <div className="p-4 border-b border-gray-200 flex items-center justify-between">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
                <Package className="w-5 h-5 text-white" />
              </div>
              <span className="font-semibold text-lg text-gray-900">Pantry Helper</span>
            </Link>
            <button 
              onClick={onClose}
              className="lg:hidden p-1 hover:bg-gray-100 rounded"
            >
              <X size={20} />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
            {navItems.map((item) => (
              <NavItem
                key={item.path}
                to={item.path}
                icon={item.icon}
                label={item.label}
                isActive={location.pathname === item.path}
                onClick={onClose}
              />
            ))}
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-gray-200">
            <div className="text-xs text-gray-400 text-center">
              v0.1.0
            </div>
          </div>
        </div>
      </aside>
    </>
  )
}

const Header = ({ onMenuClick }) => (
  <header className="lg:hidden bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between sticky top-0 z-30">
    <button 
      onClick={onMenuClick}
      className="p-2 hover:bg-gray-100 rounded-lg"
    >
      <Menu size={20} />
    </button>
    <span className="font-semibold text-gray-900">Pantry Helper</span>
    <div className="w-10" /> {/* Spacer for centering */}
  </header>
)

const MainLayout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const token = localStorage.getItem('token')

  // Redirect to login if not authenticated
  // Commenting out for dev - uncomment when auth is ready
  // if (!token) {
  //   return <Navigate to="/login" replace />
  // }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 flex flex-col">
        <Header onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 p-4 lg:p-8 overflow-auto">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}

export default MainLayout
