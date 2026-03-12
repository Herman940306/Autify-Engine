import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { UserPlus, Archive, Trash2, Edit2, Save, X } from 'lucide-react'
import { fetchClients, createClient, updateClient, deleteClient } from '../api'
import { useAuth } from '../auth/AuthContext'

/**
 * ClientsPage — view, create, edit and archive client profiles.
 * Full CRUD with role-based delete access (admin only).
 */
export default function ClientsPage() {
  const { can } = useAuth()
  const [clients, setClients] = useState([])
  const [form, setForm] = useState({ name: '', surname: '', email: '', phone: '', address: '', company: '', notes: '' })
  const [editing, setEditing] = useState(null)
  const [showArchived, setShowArchived] = useState(false)

  const load = () => fetchClients().then(setClients).catch(() => {})
  useEffect(() => { load() }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    await createClient(form)
    setForm({ name: '', surname: '', email: '', phone: '', address: '', company: '', notes: '' })
    load()
  }

  const handleUpdate = async (id) => {
    const { id: _, ...data } = editing
    await updateClient(id, data)
    setEditing(null)
    load()
  }

  const handleDelete = async (id, name) => {
    if (!confirm(`Archive client "${name}"? This will hide them from the active list.`)) return
    try {
      await deleteClient(id)
      load()
    } catch (err) {
      alert(err.message)
    }
  }

  const displayed = showArchived ? clients : clients.filter((c) => !c.is_archived)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Clients</h1>
        <label className="flex items-center gap-2 text-sm text-gray-500 cursor-pointer">
          <input
            type="checkbox"
            className="rounded"
            checked={showArchived}
            onChange={(e) => setShowArchived(e.target.checked)}
          />
          Show archived
        </label>
      </div>

      {/* Create client */}
      <form onSubmit={handleCreate} className="flex flex-wrap gap-3 items-end bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
        <div>
          <label className="block text-xs text-gray-500 mb-1">Name *</label>
          <input
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-400 outline-none"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
          />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Surname</label>
          <input
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-400 outline-none"
            value={form.surname}
            onChange={(e) => setForm({ ...form, surname: e.target.value })}
          />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Email *</label>
          <input
            type="email"
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-400 outline-none"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            required
          />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Phone</label>
          <input
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-400 outline-none"
            value={form.phone}
            onChange={(e) => setForm({ ...form, phone: e.target.value })}
          />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Company</label>
          <input
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-400 outline-none"
            value={form.company}
            onChange={(e) => setForm({ ...form, company: e.target.value })}
          />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Address</label>
          <input
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-400 outline-none"
            value={form.address}
            onChange={(e) => setForm({ ...form, address: e.target.value })}
          />
        </div>
        <button
          type="submit"
          className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition-colors"
        >
          <UserPlus size={15} /> Add Client
        </button>
      </form>

      {/* Client list */}
      <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="bg-gray-50 text-left text-xs uppercase tracking-wider text-gray-500">
              <th className="px-4 py-3">ID</th>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Surname</th>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Company</th>
              <th className="px-4 py-3">Phone</th>
              <th className="px-4 py-3">Address</th>
              <th className="px-4 py-3">Last Update</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {displayed.map((c) => (
              <motion.tr
                key={c.client_id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className={c.is_archived ? 'opacity-50' : ''}
              >
                <td className="px-4 py-3 font-mono text-xs">#{c.client_id}</td>
                <td className="px-4 py-3">
                  {editing?.id === c.client_id ? (
                    <input
                      className="border rounded px-2 py-1 text-sm w-full"
                      value={editing.name}
                      onChange={(e) => setEditing({ ...editing, name: e.target.value })}
                    />
                  ) : (
                    <span className="font-medium">{c.name}</span>
                  )}
                </td>
                <td className="px-4 py-3 text-gray-500">
                  {editing?.id === c.client_id ? (
                    <input
                      className="border rounded px-2 py-1 text-sm w-full"
                      value={editing.surname || ''}
                      onChange={(e) => setEditing({ ...editing, surname: e.target.value })}
                    />
                  ) : (c.surname || '-')}
                </td>
                <td className="px-4 py-3">
                  {editing?.id === c.client_id ? (
                    <input
                      className="border rounded px-2 py-1 text-sm w-full"
                      value={editing.email}
                      onChange={(e) => setEditing({ ...editing, email: e.target.value })}
                    />
                  ) : c.email}
                </td>
                <td className="px-4 py-3 text-gray-500">
                  {editing?.id === c.client_id ? (
                    <input
                      className="border rounded px-2 py-1 text-sm w-full"
                      value={editing.company || ''}
                      onChange={(e) => setEditing({ ...editing, company: e.target.value })}
                    />
                  ) : (c.company || '-')}
                </td>
                <td className="px-4 py-3 text-gray-500">
                  {editing?.id === c.client_id ? (
                    <input
                      className="border rounded px-2 py-1 text-sm w-full"
                      value={editing.phone || ''}
                      onChange={(e) => setEditing({ ...editing, phone: e.target.value })}
                    />
                  ) : (c.phone || '-')}
                </td>
                <td className="px-4 py-3 text-gray-500">
                  {editing?.id === c.client_id ? (
                    <input
                      className="border rounded px-2 py-1 text-sm w-full"
                      value={editing.address || ''}
                      onChange={(e) => setEditing({ ...editing, address: e.target.value })}
                    />
                  ) : (c.address || '-')}
                </td>
                <td className="px-4 py-3 text-gray-500 text-xs">
                  {c.last_update ? new Date(c.last_update).toLocaleDateString() : '-'}
                </td>
                <td className="px-4 py-3 text-right space-x-1">
                  {editing?.id === c.client_id ? (
                    <>
                      <button onClick={() => handleUpdate(c.client_id)} className="inline-flex items-center gap-1 px-3 py-1 text-xs rounded-lg bg-green-600 text-white">
                        <Save size={12} /> Save
                      </button>
                      <button onClick={() => setEditing(null)} className="px-2 py-1 text-xs rounded-lg text-gray-500 hover:bg-gray-100">
                        <X size={12} />
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        onClick={() => setEditing({
                          id: c.client_id,
                          name: c.name,
                          surname: c.surname || '',
                          email: c.email,
                          phone: c.phone || '',
                          address: c.address || '',
                          company: c.company || '',
                          notes: c.notes || '',
                        })}
                        className="inline-flex items-center gap-1 px-3 py-1 text-xs rounded-lg bg-gray-100 text-gray-700 hover:bg-gray-200"
                      >
                        <Edit2 size={12} /> Edit
                      </button>
                      {can('can_delete_clients') && !c.is_archived && (
                        <button
                          onClick={() => handleDelete(c.client_id, c.name)}
                          className="inline-flex items-center gap-1 px-3 py-1 text-xs rounded-lg text-red-600 hover:bg-red-50"
                        >
                          <Archive size={12} /> Archive
                        </button>
                      )}
                    </>
                  )}
                </td>
              </motion.tr>
            ))}
            {displayed.length === 0 && (
              <tr><td colSpan={9} className="px-4 py-8 text-center text-gray-400">No clients found</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
