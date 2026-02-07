import { useEffect, useState } from 'react'
import api, { API_BASE_URL } from '../api'
import { Check, X, ClipboardList, RefreshCw, Image as ImageIcon } from 'lucide-react'

const ReviewQueue = () => {
  const [reviews, setReviews] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchPending = async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await api.get('/v1/reviews/pending')
      setReviews(res.data || [])
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const act = async (id, action) => {
    try {
      await api.post(`/v1/reviews/${id}/${action}`)
      await fetchPending()
    } catch (e) {
      setError(e.message)
    }
  }

  useEffect(() => {
    fetchPending()
  }, [])

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <ClipboardList className="h-5 w-5" /> Manual Checks (Review Queue)
        </h2>
        <button
          onClick={fetchPending}
          className="rounded bg-blue-500 px-3 py-1 text-sm font-medium text-white hover:bg-blue-600"
          title="Refresh"
        >
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>

      {error && <div className="mb-4 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}

      {loading ? (
        <div className="py-8 text-center text-gray-600">Loading…</div>
      ) : reviews.length === 0 ? (
        <div className="py-8 text-center text-gray-500">No pending checks. Nice.</div>
      ) : (
        <div className="space-y-3">
          {reviews.map((r) => {
            const imageUrl = `${API_BASE_URL}/v1/captures/${r.capture_id}/image`
            return (
              <div key={r.id} className="rounded border border-gray-200 p-4 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div className="flex gap-3">
                  <div className="h-20 w-20 rounded border border-gray-200 bg-gray-50 flex items-center justify-center overflow-hidden">
                    <img
                      src={imageUrl}
                      alt={`capture ${r.capture_id}`}
                      className="h-full w-full object-cover"
                      onError={(e) => {
                        e.currentTarget.style.display = 'none'
                      }}
                    />
                    <ImageIcon className="h-6 w-6 text-gray-300" />
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">Capture: {r.capture_id}</div>
                    <div className="text-xs text-gray-500">Created: {new Date(r.created_at).toLocaleString()}</div>
                    {r.notes && <div className="mt-1 text-sm text-gray-700">{r.notes}</div>}
                    <a
                      href={imageUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-1 inline-block text-xs text-blue-600 hover:underline"
                    >
                      Open image
                    </a>
                  </div>
                </div>
                <div className="flex gap-2 sm:flex-col sm:items-end">
                  <button
                    onClick={() => act(r.id, 'approve')}
                    className="inline-flex items-center gap-1 rounded bg-green-500 px-3 py-1 text-sm font-medium text-white hover:bg-green-600"
                  >
                    <Check className="h-4 w-4" /> Approve
                  </button>
                  <button
                    onClick={() => act(r.id, 'reject')}
                    className="inline-flex items-center gap-1 rounded bg-red-500 px-3 py-1 text-sm font-medium text-white hover:bg-red-600"
                  >
                    <X className="h-4 w-4" /> Reject
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default ReviewQueue
