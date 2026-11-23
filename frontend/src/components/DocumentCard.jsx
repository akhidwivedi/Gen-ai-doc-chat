import { Link } from 'react-router-dom'

const STATUS_STYLES = {
  ready: 'bg-green-100 text-green-700',
  processing: 'bg-amber-100 text-amber-700',
  pending: 'bg-slate-100 text-slate-600',
  failed: 'bg-red-100 text-red-700',
}

const formatSize = (bytes) =>
  bytes > 1024 * 1024 ? `${(bytes / 1024 / 1024).toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`

export default function DocumentCard({ doc, onDelete, onRetry }) {
  return (
    <li className="flex items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <span className="rounded bg-indigo-50 px-1.5 py-0.5 text-xs font-semibold uppercase text-indigo-700">
            {doc.file_type}
          </span>
          <h3 className="truncate font-medium">{doc.title}</h3>
        </div>
        <p className="mt-1 text-xs text-slate-500">
          {formatSize(doc.file_size)}
          {doc.page_count > 0 && ` · ${doc.page_count} pages`}
          {doc.chunk_count > 0 && ` · ${doc.chunk_count} chunks`}
          {` · ${new Date(doc.created_at).toLocaleDateString()}`}
        </p>
        {doc.status === 'failed' && doc.error_message && (
          <p className="mt-1 text-xs text-red-600">{doc.error_message}</p>
        )}
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[doc.status]}`}>{doc.status}</span>
        {doc.status === 'ready' && (
          <Link to={`/documents/${doc.id}`} className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700">
            Chat
          </Link>
        )}
        {doc.status === 'failed' && (
          <button onClick={() => onRetry(doc)} className="rounded-md border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-100">
            Retry
          </button>
        )}
        <button
          onClick={() => onDelete(doc)}
          className="rounded-md px-2 py-1.5 text-sm text-slate-500 hover:bg-red-50 hover:text-red-600"
          aria-label={`Delete ${doc.title}`}
        >
          Delete
        </button>
      </div>
    </li>
  )
}
