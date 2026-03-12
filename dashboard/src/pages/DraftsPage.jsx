import { useEffect, useState } from 'react'
import DraftTable from '../components/DraftTable'
import { fetchDrafts, approveDraft, rejectDraft } from '../api'

/**
 * DraftsPage — draft review panel with Approve / Reject controls.
 * Enforces the draft-only workflow: no action without explicit human click.
 */
export default function DraftsPage() {
  const [drafts, setDrafts] = useState([])
  const [filter, setFilter] = useState('') // '', 'pending', 'approved', 'rejected'

  const load = () => fetchDrafts(filter || undefined).then(setDrafts).catch(() => {})
  useEffect(() => { load() }, [filter])

  const handleApprove = async (id) => {
    await approveDraft(id)
    load()
  }

  const handleReject = async (id) => {
    await rejectDraft(id)
    load()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Drafts</h1>
        <div className="flex gap-2">
          {['', 'pending', 'approved', 'rejected'].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 text-xs rounded-lg font-medium transition-colors ${
                filter === f
                  ? 'bg-brand-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {f === '' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <DraftTable drafts={drafts} onApprove={handleApprove} onReject={handleReject} />
    </div>
  )
}
