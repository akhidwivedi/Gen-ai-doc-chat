import { useCallback, useEffect, useState } from 'react'
import { errorMessage } from '../api/client'
import { deleteDocument, listDocuments, reprocessDocument } from '../api/documents'
import DocumentCard from '../components/DocumentCard'
import Spinner from '../components/Spinner'
import UploadBox from '../components/UploadBox'

export default function DashboardPage() {
  const [docs, setDocs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    try {
      setDocs(await listDocuments())
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const handleDelete = async (doc) => {
    if (!window.confirm(`Delete "${doc.title}" and its chat history?`)) return
    try {
      await deleteDocument(doc.id)
      setDocs((d) => d.filter((x) => x.id !== doc.id))
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  const handleRetry = async (doc) => {
    setDocs((d) => d.map((x) => (x.id === doc.id ? { ...x, status: 'processing' } : x)))
    try {
      const updated = await reprocessDocument(doc.id)
      setDocs((d) => d.map((x) => (x.id === doc.id ? updated : x)))
    } catch (err) {
      setError(errorMessage(err))
      load()
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-4 py-8">
      <div>
        <h1 className="text-2xl font-semibold">Your documents</h1>
        <p className="text-sm text-slate-500">Upload a document, then ask questions about it. Each document has its own chat.</p>
      </div>
      <UploadBox onUploaded={(doc) => setDocs((d) => [doc, ...d])} />
      {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
      {loading ? (
        <div className="flex justify-center py-8"><Spinner /></div>
      ) : docs.length === 0 ? (
        <p className="py-8 text-center text-sm text-slate-500">No documents yet. Upload one to get started.</p>
      ) : (
        <ul className="space-y-3">
          {docs.map((doc) => (
            <DocumentCard key={doc.id} doc={doc} onDelete={handleDelete} onRetry={handleRetry} />
          ))}
        </ul>
      )}
    </div>
  )
}
