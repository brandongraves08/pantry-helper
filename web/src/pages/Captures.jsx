import { useEffect, useRef, useState } from 'react';
import { Camera, Upload, Image, RotateCcw, Check, X, Loader2, Clock, RefreshCw, AlertTriangle, Scan } from 'lucide-react';
import * as api from '../api/client';

export default function Captures() {
  const [captures, setCaptures] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [preview, setPreview] = useState(null);
  const [file, setFile] = useState(null);
  const [deviceId, setDeviceId] = useState('');
  const [devices, setDevices] = useState([]);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [refreshing, setRefreshing] = useState(false);

  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);

  useEffect(() => {
    loadCaptures();
    loadDevices();
  }, []);

  const loadCaptures = async () => {
    try {
      const data = await api.listCaptures({ limit: 50 });
      setCaptures(data.captures || []);
    } catch {
      setCaptures([]);
    } finally {
      setLoading(false);
    }
  };

  const loadDevices = async () => {
    try {
      const data = await api.listDevices();
      setDevices(data.items || []);
    } catch {}
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadCaptures();
    setRefreshing(false);
  };

  const handleFileSelect = (e) => {
    const f = e.target.files?.[0];
    if (f) {
      setFile(f);
      setPreview(URL.createObjectURL(f));
    }
  };

  const retakePhoto = () => {
    setFile(null);
    setPreview(null);
    setError('');
    setSuccess('');
  };

  const uploadCapture = async () => {
    if (!file) return;
    setUploading(true);
    setError('');
    setSuccess('');

    try {
      const data = await api.uploadImage(file, { deviceId });
      setSuccess(`Photo processed! Capture ID: ${data.capture_id?.slice(0, 12)}... — ${data.message || 'queued for inventory analysis'}`);
      setFile(null);
      setPreview(null);
      await loadCaptures();
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Pantry Captures</h2>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border rounded-lg hover:bg-gray-50"
        >
          <RefreshCw size={16} className={refreshing ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Photo Upload / Camera Section */}
      <div className="bg-white rounded-xl border p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">New Capture</h3>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700 text-sm">
            <AlertTriangle size={16} />
            {error}
          </div>
        )}

        {success && (
          <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg flex items-center gap-2 text-green-700 text-sm">
            <Check size={16} />
            {success}
          </div>
        )}

        {/* Preview / Upload */}
          <div className="space-y-4">
            {preview ? (
              <div className="space-y-4">
                <div className="rounded-xl overflow-hidden border bg-gray-50">
                  <img
                    src={preview}
                    alt="Preview"
                    className="w-full max-h-96 object-contain"
                  />
                </div>

                <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
                  <div className="flex-1">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Device (optional)</label>
                    <select
                      value={deviceId}
                      onChange={(e) => setDeviceId(e.target.value)}
                      className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Auto-select device</option>
                      {devices.map((d) => (
                        <option key={d.id} value={d.id}>{d.name} ({d.id})</option>
                      ))}
                    </select>
                  </div>
                  <div className="flex gap-2 sm:pt-5">
                    <button
                      onClick={retakePhoto}
                      className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
                    >
                      <RotateCcw size={16} />
                      Retake
                    </button>
                    <button
                      onClick={uploadCapture}
                      disabled={uploading}
                      className="flex items-center gap-2 px-6 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                    >
                      {uploading ? <Loader2 size={16} className="animate-spin" /> : <Scan size={16} />}
                      {uploading ? 'Processing...' : 'Analyze Pantry'}
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* File Upload */}
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="flex flex-col items-center justify-center gap-3 p-8 border-2 border-dashed border-gray-300 rounded-xl hover:border-blue-400 hover:bg-blue-50 transition-colors"
                >
                  <Upload size={32} className="text-gray-400" />
                  <span className="font-medium text-gray-700">Upload Photo</span>
                  <span className="text-sm text-gray-400">From your device</span>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                  <input
                    ref={cameraInputRef}
                    type="file"
                    accept="image/*"
                    capture="environment"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                </button>

                {/* Camera Capture */}
                <button
                  onClick={() => cameraInputRef.current?.click()}
                  className="flex flex-col items-center justify-center gap-3 p-8 border-2 border-dashed border-gray-300 rounded-xl hover:border-green-400 hover:bg-green-50 transition-colors"
                >
                  <Camera size={32} className="text-gray-400" />
                  <span className="font-medium text-gray-700">Take Photo</span>
                  <span className="text-sm text-gray-400">Use camera</span>
                </button>
              </div>
            )}
          </div>
      </div>

      {/* Capture History */}
      <div className="bg-white rounded-xl border overflow-hidden">
        <div className="px-4 sm:px-6 py-4 border-b bg-gray-50">
          <h3 className="font-semibold text-gray-900">Capture History</h3>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12 text-gray-400">
            <Loader2 size={24} className="animate-spin mr-2" />
            Loading captures...
          </div>
        ) : captures.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-gray-400">
            <Image size={48} className="mb-3" />
            <p className="font-medium">No captures yet</p>
            <p className="text-sm">Take a photo of your pantry to get started</p>
          </div>
        ) : (
          <div className="divide-y">
            {captures.map((cap) => (
              <CaptureRow key={cap.id} capture={cap} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function CaptureRow({ capture }) {
  const [expanded, setExpanded] = useState(false);

  const statusColors = {
    complete: 'bg-green-100 text-green-700',
    analyzing: 'bg-yellow-100 text-yellow-700',
    stored: 'bg-blue-100 text-blue-700',
    failed: 'bg-red-100 text-red-700',
  };

  const triggerIcons = {
    manual: '📷',
    door: '🚪',
    light: '💡',
    timer: '⏰',
    boot: '🔌',
  };

  return (
    <div className="hover:bg-gray-50">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 sm:px-6 py-4 flex items-center justify-between text-left"
      >
        <div className="flex items-center gap-4">
          <span className="text-xl">{triggerIcons[capture.trigger_type] || '📸'}</span>
          <div>
            <p className="font-medium text-gray-900 truncate">
              Capture {capture.id?.slice(0, 8)}...
            </p>
            <p className="text-sm text-gray-500 flex items-center gap-1">
              <Clock size={12} />
              {capture.captured_at ? new Date(capture.captured_at).toLocaleString() : 'N/A'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className={`px-2 py-1 text-xs font-medium rounded-full ${statusColors[capture.status] || 'bg-gray-100 text-gray-700'}`}>
            {capture.status}
          </span>
          {capture.image_url && (
            <span className="text-xs text-gray-400">📸</span>
          )}
        </div>
      </button>

      {expanded && (
        <div className="px-4 sm:px-6 pb-4 pl-9 sm:pl-16">
          {capture.image_url && (
            <div className="mb-3 rounded-lg overflow-hidden border max-w-sm">
              <img
                src={capture.image_url}
                alt={`Capture ${capture.id}`}
                className="w-full h-48 object-cover"
                onError={(e) => { e.target.style.display = 'none'; }}
              />
            </div>
          )}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm">
            <div>
              <span className="text-gray-500">Device:</span>{' '}
              <span className="text-gray-900">{capture.device_id || '—'}</span>
            </div>
            <div>
              <span className="text-gray-500">Trigger:</span>{' '}
              <span className="text-gray-900 capitalize">{capture.trigger_type || '—'}</span>
            </div>
          </div>
          {capture.error_message && (
            <p className="mt-2 text-sm text-red-600">{capture.error_message}</p>
          )}
        </div>
      )}
    </div>
  );
}
