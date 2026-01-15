import React from 'react'
import { Upload, Loader } from 'lucide-react'

const ImageUpload = ({ onUpload, isLoading }) => {
  const handleDragOver = (e) => {
    e.preventDefault()
    e.currentTarget.classList.add('border-blue-400', 'bg-blue-50')
  }

  const handleDragLeave = (e) => {
    e.currentTarget.classList.remove('border-blue-400', 'bg-blue-50')
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.currentTarget.classList.remove('border-blue-400', 'bg-blue-50')
    const files = e.dataTransfer.files
    if (files.length > 0) {
      onUpload(files[0])
    }
  }

  const handleFileInput = (e) => {
    if (e.target.files.length > 0) {
      onUpload(e.target.files[0])
    }
  }

  return (
    <div className="rounded-lg border-2 border-dashed border-gray-300 bg-white p-8 transition-colors">
      <div
        className="flex flex-col items-center justify-center"
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {isLoading ? (
          <>
            <Loader className="mb-2 h-8 w-8 animate-spin text-blue-500" />
            <p className="text-sm text-gray-600">Processing image...</p>
          </>
        ) : (
          <>
            <Upload className="mb-2 h-8 w-8 text-gray-400" />
            <p className="text-center">
              <span className="font-medium text-gray-700">Drag & drop</span>{' '}
              <span className="text-gray-600">or</span>
            </p>
            <label className="mt-2">
              <span className="cursor-pointer font-medium text-blue-500 hover:text-blue-600">
                click to browse
              </span>
              <input
                type="file"
                accept="image/*"
                onChange={handleFileInput}
                className="hidden"
                disabled={isLoading}
              />
            </label>
            <p className="mt-2 text-xs text-gray-500">PNG, JPG, GIF up to 10MB</p>
          </>
        )}
      </div>
    </div>
  )
}

export default ImageUpload
