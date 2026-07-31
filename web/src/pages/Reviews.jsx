import { useEffect, useState } from 'react';
import { AlertCircle, CheckCircle, XCircle, Camera, RefreshCw, Loader, Edit3, ChevronDown, ChevronUp, Package } from 'lucide-react';
import * as api from '../api/client';

export default function Reviews() {
  const [captures, setCaptures] = useState([]);
  const [detections, setDetections] = useState({});
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(null);
  const [actionMsg, setActionMsg] = useState({});
  const [editModal, setEditModal] = useState(null); // { captureId, index, item }

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const capData = await api.listCaptures({ limit: 25 });
      const caps = capData.captures || [];

      setCaptures(caps);

      // Load detections for each capture
      const dets = {};
      await Promise.all(caps.map(async (c) => {
        try {
          const d = await api.listDetections(c.id);
          dets[c.id] = d;
        } catch {
          dets[c.id] = { items: [], detection_count: 0 };
        }
      }));
      setDetections(dets);
    } catch {
      setCaptures([]);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (captureId, index) => {
    try {
      await api.approveDetection(captureId, index);
      setActionMsg({ [captureId + '-' + index]: 'approved' });
      // Refresh to show updated state
      const d = await api.listDetections(captureId);
      setDetections(prev => ({ ...prev, [captureId]: d }));
      setTimeout(() => setActionMsg({}), 3000);
    } catch (err) {
      setActionMsg({ [captureId + '-' + index]: 'error: ' + (err.response?.data?.detail || err.message) });
    }
  };

  const handleReject = async (captureId, index) => {
    try {
      await api.rejectDetection(captureId, index);
      setActionMsg({ [captureId + '-' + index]: 'rejected' });
      const d = await api.listDetections(captureId);
      setDetections(prev => ({ ...prev, [captureId]: d }));
      setTimeout(() => setActionMsg({}), 3000);
    } catch (err) {
      setActionMsg({ [captureId + '-' + index]: 'error: ' + (err.response?.data?.detail || err.message) });
    }
  };

  const handleEditSave = async () => {
    if (!editModal) return;
    const { captureId, index, item } = editModal;
    try {
      await api.editDetection(captureId, index, {
        name: item.name,
        brand: item.brand || null,
        package_type: item.package_type || null,
        quantity_estimate: item.quantity_estimate || null,
        count: item.count || 1,
        par_level: item.par_level || 0,
        expires_at: item.expires_at || null,
      });
      setActionMsg({ [captureId + '-' + index]: 'edited' });
      const d = await api.listDetections(captureId);
      setDetections(prev => ({ ...prev, [captureId]: d }));
      setEditModal(null);
      setTimeout(() => setActionMsg({}), 3000);
    } catch (err) {
      setActionMsg({ [captureId + '-' + index]: 'error: ' + (err.response?.data?.detail || err.message) });
    }
  };

  const toggleExpand = (id) => {
    setExpanded(expanded === id ? null : id);
  };

  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base sm:text-2xl font-bold text-gray-900">Verification</h2>
          <p className="text-sm text-gray-500">Review items detected by AI vision</p>
        </div>
        <button
          onClick={loadData}
          disabled={loading}
          className="flex items-center gap-2 px-3 sm:px-4 py-2 text-sm font-medium text-gray-700 bg-white border rounded-lg hover:bg-gray-50"
        >
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          <span className="hidden sm:inline">Refresh</span>
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12 text-gray-400">
          <Loader size={24} className="animate-spin mr-2" />
          Loading detections...
        </div>
      ) : captures.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-xl">
          <Camera size={48} className="mx-auto text-gray-400 mb-4" />
          <p className="text-gray-600 font-medium">No captures yet</p>
          <p className="text-sm text-gray-500">Upload a photo to get started</p>
        </div>
      ) : (
        <div className="space-y-4">
          {captures.map((cap) => {
            const det = detections[cap.id];
            const items = det?.items || [];
            const isExpanded = expanded === cap.id;
            const pendingItems = items.filter(i => !i.in_inventory);

            return (
              <div key={cap.id} className="bg-white rounded-xl border overflow-hidden">
                {/* Capture header */}
                <button
                  onClick={() => toggleExpand(cap.id)}
                  className="w-full flex items-center justify-between px-3 sm:px-6 py-3 sm:py-4 hover:bg-gray-50 text-left"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="shrink-0">
                      {cap.status === 'complete' ? (
                        <CheckCircle size={20} className="text-green-500" />
                      ) : cap.status === 'failed' ? (
                        <XCircle size={20} className="text-red-500" />
                      ) : (
                        <Loader size={20} className="text-blue-500 animate-spin" />
                      )}
                    </div>
                    <div className="min-w-0">
                      <p className="font-medium text-gray-900 truncate">
                        Capture {cap.id.slice(0, 8)}...
                      </p>
                      <p className="text-xs text-gray-500">
                        {cap.captured_at ? new Date(cap.captured_at).toLocaleString() : 'N/A'}
                        {items.length > 0 && ` • ${items.length} detections`}
                        {pendingItems.length > 0 && ` • ${pendingItems.length} pending`}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                      cap.status === 'complete' ? 'bg-green-100 text-green-700' :
                      cap.status === 'failed' ? 'bg-red-100 text-red-700' :
                      'bg-yellow-100 text-yellow-700'
                    }`}>
                      {cap.status}
                    </span>
                    {isExpanded ? <ChevronUp size={18} className="text-gray-400" /> : <ChevronDown size={18} className="text-gray-400" />}
                  </div>
                </button>

                {/* Detected items list */}
                {isExpanded && (
                  <div className="border-t divide-y">
                    {items.length === 0 ? (
                      <div className="px-3 sm:px-6 py-6 text-center text-gray-400 text-xs sm:text-sm">
                        No items detected in this capture
                      </div>
                    ) : (
                      items.map((item, idx) => {
                        const key = cap.id + '-' + item.index;
                        const msg = actionMsg[key];
                        const isInInventory = item.in_inventory;

                        return (
                          <div key={item.index} className={`px-3 sm:px-6 py-3 sm:py-4 ${
                            isInInventory ? 'bg-green-50/30' : ''
                          }`}>
                            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                              <div className="flex items-start gap-2 sm:gap-3 min-w-0 flex-1">
                                <div className="hidden sm:flex w-10 h-10 bg-gray-100 rounded-lg items-center justify-center shrink-0">
                                  <Package size={18} className="text-gray-500" />
                                </div>
                                <div className="min-w-0">
                                  <div className="flex items-center gap-2 flex-wrap">
                                    <p className="font-medium text-gray-900">{item.name}</p>
                                    {item.brand && (
                                      <span className="hidden sm:inline text-sm text-gray-500">by {item.brand}</span>
                                    )}
                                  </div>
                                  <div className="flex items-center gap-2 mt-1 text-xs sm:text-sm text-gray-500 flex-wrap">
                                    <span className={`font-medium ${
                                      item.confidence >= 0.8 ? 'text-green-600' :
                                      item.confidence >= 0.5 ? 'text-yellow-600' :
                                      'text-red-600'
                                    }`}>
                                      {Math.round(item.confidence * 100)}%
                                    </span>
                                    {item.package_type && <span className="hidden sm:inline">&middot; {item.package_type}</span>}
                                    {item.quantity_estimate && <span className="hidden sm:inline">&middot; ~{item.quantity_estimate} qty</span>}
                                    {isInInventory && (
                                      <span className="px-1.5 sm:px-2 py-0.5 text-xs font-medium bg-green-100 text-green-700 rounded-full">
                                        In inv
                                      </span>
                                    )}
                                  </div>
                                </div>
                              </div>

                              {/* Action buttons */}
                              <div className="flex items-center gap-1.5 w-full sm:w-auto">
                                {msg === 'approved' && (
                                  <span className="text-xs text-green-600 font-medium">Approved ✓</span>
                                )}
                                {msg === 'rejected' && (
                                  <span className="text-xs text-red-600 font-medium">Rejected ✗</span>
                                )}
                                {msg === 'edited' && (
                                  <span className="text-xs text-blue-600 font-medium">Updated ✎</span>
                                )}
                                {msg && msg.startsWith('error') && (
                                  <span className="text-xs text-red-600">{msg}</span>
                                )}
                                {!msg && (
                                  <>
                                    <button
                                      onClick={() => handleApprove(cap.id, item.index)}
                                      className="flex items-center justify-center sm:gap-1 px-2 sm:px-3 py-1.5 text-xs font-medium text-green-700 bg-green-100 rounded-lg hover:bg-green-200"
                                      title="Approve"
                                    >
                                      <CheckCircle size={14} />
                                      <span className="hidden sm:inline"> Approve</span>
                                    </button>
                                    <button
                                      onClick={() => handleReject(cap.id, item.index)}
                                      className="flex items-center justify-center sm:gap-1 px-2 sm:px-3 py-1.5 text-xs font-medium text-red-700 bg-red-100 rounded-lg hover:bg-red-200"
                                      title="Reject"
                                    >
                                      <XCircle size={14} />
                                      <span className="hidden sm:inline"> Reject</span>
                                    </button>
                                    <button
                                      onClick={() => setEditModal({ captureId: cap.id, index: item.index, item: { ...item, count: item.current_count || item.quantity_estimate || 1, par_level: item.current_par || 0 } })}
                                      className="flex items-center justify-center sm:gap-1 px-2 sm:px-3 py-1.5 text-xs font-medium text-blue-700 bg-blue-100 rounded-lg hover:bg-blue-200"
                                      title="Edit"
                                    >
                                      <Edit3 size={14} />
                                      <span className="hidden sm:inline"> Edit</span>
                                    </button>
                                  </>
                                )}
                              </div>
                            </div>
                          </div>
                        );
                      })
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Edit Modal */}
      {editModal && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Edit Detection</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input
                  type="text"
                  value={editModal.item.name}
                  onChange={(e) => setEditModal(prev => ({ ...prev, item: { ...prev.item, name: e.target.value } }))}
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Brand</label>
                <input
                  type="text"
                  value={editModal.item.brand || ''}
                  onChange={(e) => setEditModal(prev => ({ ...prev, item: { ...prev.item, brand: e.target.value } }))}
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Count</label>
                  <input
                    type="number"
                    min={1}
                    value={editModal.item.count}
                    onChange={(e) => setEditModal(prev => ({ ...prev, item: { ...prev.item, count: parseInt(e.target.value) || 1 } }))}
                    className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Par Level</label>
                  <input
                    type="number"
                    min={0}
                    value={editModal.item.par_level}
                    onChange={(e) => setEditModal(prev => ({ ...prev, item: { ...prev.item, par_level: parseInt(e.target.value) || 0 } }))}
                    className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  onClick={handleEditSave}
                  className="flex-1 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
                >
                  Save & Approve
                </button>
                <button
                  onClick={() => setEditModal(null)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
