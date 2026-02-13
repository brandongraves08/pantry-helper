import { useState, useEffect, createContext, useContext } from 'react'
import { X, CheckCircle, AlertCircle, Info } from 'lucide-react'

const ToastContext = createContext()

export const useToast = () => useContext(ToastContext)

const Toast = ({ toast, onClose }) => {
  const { id, type = 'info', message, title, visible } = toast

  const icons = {
    success: CheckCircle,
    error: AlertCircle,
    warning: AlertCircle,
    info: Info
  }

  const colors = {
    success: 'bg-green-100 text-green-800 border-green-200',
    error: 'bg-red-100 text-red-800 border-red-200',
    warning: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    info: 'bg-blue-100 text-blue-800 border-blue-200'
  }

  const Icon = icons[type]

  useEffect(() => {
    if (visible) {
      const timer = setTimeout(() => onClose(id), 5000)
      return () => clearTimeout(timer)
    }
  }, [id, visible, onClose])

  return (
    <div
      className={`flex items-start gap-3 p-4 rounded-lg shadow-lg border ${colors[type]} max-w-sm transform transition-all duration-300 ${
        visible ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-full'
      }`}
    >
      <Icon size={20} className="flex-shrink-0 mt-0.5" />
      <div className="flex-1">
        {title && <div className="font-semibold text-sm">{title}</div>}
        <div className="text-sm opacity-90">{message}</div>
      </div>
      <button
        onClick={() => onClose(id)}
        className="p-1 hover:bg-black/10 rounded transition-colors"
      >
        <X size={16} />
      </button>
    </div>
  )
}

export const Toaster = () => {
  const [toasts, setToasts] = useState([])

  const show = (message, options = {}) => {
    const id = Date.now() + Math.random()
    const toast = {
      id,
      message,
      ...options,
      visible: false
    }
    
    setToasts(prev => [...prev, toast])
    
    // Trigger enter animation
    setTimeout(() => {
      setToasts(prev => prev.map(t => t.id === id ? { ...t, visible: true } : t))
    }, 10)
    
    return id
  }

  const close = (id) => {
    setToasts(prev => prev.map(t => t.id === id ? { ...t, visible: false } : t))
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id))
    }, 300)
  }

  const value = {
    show,
    close,
    success: (msg, opts) => show(msg, { ...opts, type: 'success' }),
    error: (msg, opts) => show(msg, { ...opts, type: 'error' }),
    warning: (msg, opts) => show(msg, { ...opts, type: 'warning' }),
    info: (msg, opts) => show(msg, { ...opts, type: 'info' })
  }

  return (
    <ToastContext.Provider value={value}>
      <div className="fixed top-4 right-4 z-50 space-y-2">
        {toasts.map(toast => (
          <Toast key={toast.id} toast={toast} onClose={close} />
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export default Toaster
