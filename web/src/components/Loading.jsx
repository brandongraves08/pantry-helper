export const Spinner = ({ size = 'md', className = '' }) => {
  const sizeClasses = {
    sm: 'w-4 h-4 border-2',
    md: 'w-6 h-6 border-2',
    lg: 'w-12 h-12 border-4',
    xl: 'w-16 h-16 border-4'
  }

  return (
    <div className={`${sizeClasses[size]} border-gray-200 border-t-indigo-600 rounded-full animate-spin ${className}`} />
  )
}

export const LoadingState = ({ text = 'Loading...', fullPage = false }) => {
  const content = (
    <div className="flex flex-col items-center justify-center gap-4">
      <Spinner size="lg" />
      <span className="text-gray-500 text-sm">{text}</span>
    </div>
  )

  if (fullPage) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        {content}
      </div>
    )
  }

  return (
    <div className="py-12 flex items-center justify-center">
      {content}
    </div>
  )
}

export const SkeletonCard = () => (
  <div className="bg-white rounded-lg shadow-sm p-4 animate-pulse">
    <div className="h-4 bg-gray-200 rounded w-3/4 mb-3"></div>
    <div className="h-3 bg-gray-200 rounded w-1/2 mb-2"></div>
    <div className="h-3 bg-gray-200 rounded w-2/3"></div>
  </div>
)

export const SkeletonList = ({ count = 3 }) => (
  <div className="space-y-4">
    {Array.from({ length: count }).map((_, i) => (
      <SkeletonCard key={i} />
    ))}
  </div>
)

export const LoadingOverlay = ({ visible, text = 'Processing...' }) => {
  if (!visible) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 shadow-xl flex flex-col items-center gap-4">
        <Spinner size="lg" />
        <span className="text-gray-700 font-medium">{text}</span>
      </div>
    </div>
  )
}

export default LoadingState
