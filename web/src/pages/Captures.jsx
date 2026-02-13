import { useEffect, useState, useRef } from 'react';
import { Camera, Upload, Image as ImageIcon, CheckCircle, XCircle } from 'lucide-react';

export default function Captures() {
  const [captures, setCaptures] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const handleUpload = async (files) => {
    if (!files.length) return;
    
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('device_id', 'pantry-cam-001');
      formData.append('token', 'F4l3yZqinCaePCckx-IDkKtnediBuNeY_pAd5J5b8qg');
      formData.append('timestamp', new Date().toISOString());
      formData.append('trigger_type', 'manual');
      formData.append('battery_v', '4.2');
      formData.append('rssi', '-45');
      formData.append('image', files[0]);

      const response = await fetch('http://localhost:8000/v1/ingest', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        alert(`Upload successful! Capture ID: ${data.capture_id}`);
      } else {
        alert('Upload failed');
      }
    } catch (err) {
      console.error('Upload error:', err);
      alert('Upload failed: ' + err.message);
    } finally {
      setUploading(false);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleUpload(e.dataTransfer.files);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Captures</h2>
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          <Camera size={16} />
          {uploading ? 'Uploading...' : 'Upload Image'}
        </button>
      </div>

      {/* Upload Area */}
      <div
        className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
          dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={(e) => handleUpload(e.target.files)}
          className="hidden"
        />
        <Upload size={48} className="mx-auto text-gray-400 mb-4" />
        <p className="text-lg font-medium text-gray-700">
          Drop image here or click to upload
        </p>
        <p className="text-sm text-gray-500 mt-2">
          Supports JPEG, PNG (max 20MB)
        </p>
      </div>

      {/* Recent Captures */}
      <div className="bg-white rounded-xl border p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Captures</h3>
        <div className="space-y-3">
          {[
            { id: '26e52457-ab7f...', status: 'complete', items: 37, time: '13:52' },
            { id: '417129c7-6b13...', status: 'complete', items: 13, time: '13:50' },
            { id: '62b9001b-f6a2...', status: 'complete', items: 19, time: '13:48' },
          ].map((capture) => (
            <div
              key={capture.id}
              className="flex items-center justify-between p-4 border rounded-lg hover:shadow-sm transition-shadow"
            >
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                  <ImageIcon size={24} className="text-gray-500" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">Capture {capture.id}</p>
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <span>{capture.items} items detected</span>
                    <span>•</span>
                    <span>{capture.time}</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <span className={`flex items-center gap-1 px-3 py-1 text-sm font-medium rounded-full ${
                  capture.status === 'complete'
                    ? 'bg-green-100 text-green-700'
                    : 'bg-yellow-100 text-yellow-700'
                }`}>
                  {capture.status === 'complete' ? (
                    <CheckCircle size={14} />
                  ) : (
                    <XCircle size={14} />
                  )}
                  {capture.status}
                </span>
                <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                  View Details
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
