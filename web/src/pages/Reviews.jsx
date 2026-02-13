import { useState } from 'react';
import { AlertCircle, CheckCircle, XCircle, Image as ImageIcon, Clock } from 'lucide-react';

export default function Reviews() {
  const [reviews, setReviews] = useState([
    {
      id: '1',
      capture_id: 'abc123',
      status: 'pending',
      notes: '',
      suggested_items: [
        { name: 'Unknown Can', confidence: 0.45, inferred: 'Tomatoes (85% zone pattern)' },
        { name: 'Cereal Box', confidence: 0.72 },
      ],
      created_at: '2026-02-12T14:00:00Z',
    },
    {
      id: '2',
      capture_id: 'def456',
      status: 'approved',
      notes: 'Confirmed stock',
      created_at: '2026-02-12T13:30:00Z',
      resolved_at: '2026-02-12T13:35:00Z',
    },
  ]);
  const [filter, setFilter] = useState('pending');

  const filteredReviews = reviews.filter(r => 
    filter === 'all' ? true : r.status === filter
  );

  const handleApprove = (id) => {
    setReviews(reviews.map(r => 
      r.id === id ? { ...r, status: 'approved', resolved_at: new Date().toISOString() } : r
    ));
  };

  const handleReject = (id) => {
    setReviews(reviews.map(r => 
      r.id === id ? { ...r, status: 'rejected', resolved_at: new Date().toISOString() } : r
    ));
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Review Queue</h2>
          <p className="text-sm text-gray-500">Approve or reject AI-detected items</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-3 py-1 text-sm font-medium text-yellow-700 bg-yellow-100 rounded-full">
            {reviews.filter(r => r.status === 'pending').length} pending
          </span>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2">
        {['pending', 'approved', 'rejected', 'all'].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-2 text-sm font-medium rounded-lg capitalize ${
              filter === f
                ? 'bg-gray-900 text-white'
                : 'bg-white text-gray-700 border hover:bg-gray-50'
            }`}
          >
            {f} ({reviews.filter(r => f === 'all' || r.status === f).length})
          </button>
        ))}
      </div>

      {/* Reviews List */}
      <div className="space-y-4">
        {filteredReviews.length === 0 ? (
          <div className="text-center py-12 bg-gray-50 rounded-xl">
            <AlertCircle size={48} className="mx-auto text-gray-400 mb-4" />
            <p className="text-gray-600 font-medium">No {filter} reviews</p>
            <p className="text-sm text-gray-500">
              {filter === 'pending' ? 'All caught up!' : 'None in this category yet.'}
            </p>
          </div>
        ) : (
          filteredReviews.map((review) => (
            <div key={review.id} className="bg-white rounded-xl border p-6">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4">
                  <div className="w-16 h-16 bg-gray-100 rounded-lg flex items-center justify-center">
                    <ImageIcon size={24} className="text-gray-500" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="font-medium text-gray-900">Capture {review.capture_id.slice(0, 8)}</h4>
                      <StatusBadge status={review.status} />
                    </div>
                    <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
                      <span className="flex items-center gap-1">
                        <Clock size={14} />
                        {new Date(review.created_at).toLocaleString()}
                      </span>
                      {review.resolved_at && (
                        <span>Resolved {new Date(review.resolved_at).toLocaleString()}</span>
                      )}
                    </div>

                    {/* Suggested Items */}
                    {review.status === 'pending' && review.suggested_items && (
                      <div className="mt-4 space-y-2">
                        <p className="text-sm font-medium text-gray-700">Suggested Items:</p>
                        {review.suggested_items.map((item, idx) => (
                          <div
                            key={idx}
                            className={`p-3 rounded-lg ${
                              item.confidence < 0.7 ? 'bg-yellow-50 border border-yellow-200' : 'bg-gray-50'
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <div>
                                <p className="font-medium text-gray-900">{item.name}</p>
                                {item.inferred && (
                                  <p className="text-sm text-blue-600">{item.inferred}</p>
                                )}
                              </div>
                              <div className="text-right">
                                <span className={`text-lg font-semibold ${
                                  item.confidence >= 0.7 ? 'text-green-600' : 'text-yellow-600'
                                }`}>
                                  {Math.round(item.confidence * 100)}%
                                </span>
                                <p className="text-xs text-gray-500">confidence</p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {review.notes && (
                      <p className="mt-3 text-sm text-gray-600 italic">
                        Note: {review.notes}
                      </p>
                    )}
                  </div>
                </div>

                {review.status === 'pending' && (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleApprove(review.id)}
                      className="flex items-center gap-1 px-4 py-2 text-sm font-medium text-green-700 bg-green-100 rounded-lg hover:bg-green-200"
                    >
                      <CheckCircle size={16} />
                      Approve
                    </button>
                    <button
                      onClick={() => handleReject(review.id)}
                      className="flex items-center gap-1 px-4 py-2 text-sm font-medium text-red-700 bg-red-100 rounded-lg hover:bg-red-200"
                    >
                      <XCircle size={16} />
                      Reject
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function StatusBadge({ status }) {
  const styles = {
    pending: 'bg-yellow-100 text-yellow-700',
    approved: 'bg-green-100 text-green-700',
    rejected: 'bg-red-100 text-red-700',
  };

  return (
    <span className={`px-2 py-1 text-xs font-medium rounded-full ${styles[status]}`}>
      {status}
    </span>
  );
}
