import { motion } from 'framer-motion'
import { CheckCircle, XCircle, Mail, Calendar, FileBarChart, User } from 'lucide-react'

const typeIcons = {
  email:    Mail,
  calendar: Calendar,
  report:   FileBarChart,
  profile:  User,
}

/**
 * DraftTable — table of draft outputs with Approve/Reject controls.
 * Strict draft-only workflow: every actionable row starts as approved=false.
 *
 * @param {Array}    drafts    – list of draft objects from API
 * @param {Function} onApprove – callback(draft_id)
 * @param {Function} onReject  – callback(draft_id)
 */
export default function DraftTable({ drafts, onApprove, onReject }) {
  if (!drafts || drafts.length === 0) {
    return (
      <div className="text-center py-12 text-gray-400 text-sm">
        No drafts to display.
      </div>
    )
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="bg-gray-50 text-left text-xs uppercase tracking-wider text-gray-500">
            <th className="px-4 py-3">ID</th>
            <th className="px-4 py-3">Type</th>
            <th className="px-4 py-3">Preview</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3 text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {drafts.map((d) => {
            const Icon = typeIcons[d.draft_type] || FileBarChart
            const preview =
              typeof d.content === 'object'
                ? d.content.subject || d.content.title || JSON.stringify(d.content).slice(0, 80)
                : String(d.content).slice(0, 80)

            return (
              <motion.tr
                key={d.draft_id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="hover:bg-gray-50 transition-colors"
              >
                <td className="px-4 py-3 font-mono text-xs">#{d.draft_id}</td>
                <td className="px-4 py-3">
                  <span className="inline-flex items-center gap-1.5 capitalize">
                    <Icon size={14} /> {d.draft_type}
                  </span>
                </td>
                <td className="px-4 py-3 max-w-xs truncate text-gray-600">{preview}</td>
                <td className="px-4 py-3">
                  {d.rejected ? (
                    <span className="inline-flex items-center gap-1 text-red-600 font-medium">
                      <XCircle size={14} /> Rejected
                    </span>
                  ) : d.approved ? (
                    <span className="inline-flex items-center gap-1 text-green-600 font-medium">
                      <CheckCircle size={14} /> Approved
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-amber-600 font-medium">
                      Pending
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-right space-x-2">
                  {!d.approved && !d.rejected && (
                    <>
                      <button
                        onClick={() => onApprove(d.draft_id)}
                        className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-lg bg-green-600 text-white hover:bg-green-700 transition-colors"
                      >
                        <CheckCircle size={13} /> Approve
                      </button>
                      <button
                        onClick={() => onReject(d.draft_id)}
                        className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-lg bg-red-50 text-red-600 hover:bg-red-100 transition-colors"
                      >
                        <XCircle size={13} /> Reject
                      </button>
                    </>
                  )}
                </td>
              </motion.tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
