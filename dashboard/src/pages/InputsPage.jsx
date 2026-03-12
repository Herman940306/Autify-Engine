import { useEffect, useState } from 'react'
import { Upload } from 'lucide-react'
import { fetchInputs, fetchClients, uploadFile } from '../api'

/**
 * InputsPage — view uploaded files and upload new ones.
 */
export default function InputsPage() {
  const [inputs, setInputs] = useState([])
  const [clients, setClients] = useState([])
  const [selectedClient, setSelectedClient] = useState('')
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState(null)

  useEffect(() => {
    fetchInputs().then(setInputs).catch(() => {})
    fetchClients().then(setClients).catch(() => {})
  }, [])

  const handleUpload = async (e) => {
    e.preventDefault()
    if (!selectedClient || !file) return
    setUploading(true)
    try {
      const res = await uploadFile(selectedClient, file)
      setResult(res)
      fetchInputs().then(setInputs)
    } catch (err) {
      setResult({ error: err.message })
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Inputs</h1>

      {/* Upload form */}
      <form
        onSubmit={handleUpload}
        className="flex flex-wrap gap-3 items-end bg-white p-4 rounded-xl border border-gray-200 shadow-sm"
      >
        <div>
          <label className="block text-xs text-gray-500 mb-1">Client</label>
          <select
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
            value={selectedClient}
            onChange={(e) => setSelectedClient(e.target.value)}
            required
          >
            <option value="">Select client…</option>
            {clients.map((c) => (
              <option key={c.client_id} value={c.client_id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">File (CSV, XLSX, PDF, JSON, TXT)</label>
          <input
            type="file"
            accept=".csv,.xls,.xlsx,.pdf,.json,.txt"
            className="text-sm"
            onChange={(e) => setFile(e.target.files[0])}
            required
          />
        </div>
        <button
          type="submit"
          disabled={uploading}
          className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 disabled:opacity-50 transition-colors"
        >
          <Upload size={15} /> {uploading ? 'Uploading…' : 'Upload & Analyse'}
        </button>
      </form>

      {result && (
        <div className={`p-4 rounded-xl text-sm ${result.error ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'}`}>
          {result.error ? result.error : result.message}
        </div>
      )}

      {/* Input history */}
      <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="bg-gray-50 text-left text-xs uppercase tracking-wider text-gray-500">
              <th className="px-4 py-3">ID</th>
              <th className="px-4 py-3">Client</th>
              <th className="px-4 py-3">File</th>
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3">Uploaded</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {inputs.map((inp) => (
              <tr key={inp.input_id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-mono text-xs">#{inp.input_id}</td>
                <td className="px-4 py-3">{inp.client_id}</td>
                <td className="px-4 py-3">{inp.file_name}</td>
                <td className="px-4 py-3 uppercase text-xs font-medium">{inp.file_type}</td>
                <td className="px-4 py-3 text-gray-500 text-xs">{inp.upload_time}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
