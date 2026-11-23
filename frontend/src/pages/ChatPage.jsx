import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { clearHistory, getHistory } from '../api/chat'
import { errorMessage } from '../api/client'
import { getDocument, summarizeDocument } from '../api/documents'
import ChatWindow from '../components/ChatWindow'
import Spinner from '../components/Spinner'

export default function ChatPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [doc, setDoc] = useState(null)
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [summarizing, setSummarizing] = useState(false)
  const [showSummary, setShowSummary] = useState(false)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    Promise.all([getDocument(id), getHistory(id)])
      .then(([d, h]) => { if (!cancelled) { setDoc(d); setMessages(h); setShowSummary(Boolean(d.summary)) } })
      .catch((err) => {
        if (err.response?.status === 404) navigate('/', { replace: true })
        else setError(errorMessage(err))
      })
      .finally(() => !cancelled && setLoading(false))
    return () => { cancelled = true }
  }, [id, navigate])

  const handleSummarize = async () => {
    setSummarizing(true)
    setError('')
    try {
      setDoc(await summarizeDocument(id))
      setShowSummary(true)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setSummarizing(false)
    }
  }

  const handleClear = async () => {
    if (!window.confirm('Clear the chat history for this document?')) return
    try {
      await clearHistory(id)
      setMessages([])
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  if (loading) return <div className="flex h-full items-center justify-center"><Spinner /></div>

  return (
    <div className="mx-auto flex h-full max-w-3xl flex-col border-x border-slate-200 bg-slate-50">
      <div className="flex items-center justify-between gap-2 border-b border-slate-200 bg-white px-4 py-3">
        <div className="min-w-0">
          <Link to="/" className="text-xs text-indigo-600 hover:underline">← All documents</Link>
          <h1 className="truncate font-semibold">{doc?.title}</h1>
        </div>
        <div className="flex shrink-0 gap-2 text-sm">
          <button
            onClick={doc?.summary ? () => setShowSummary(!showSummary) : handleSummarize}
            disabled={summarizing}
            className="rounded-md border border-slate-300 px-3 py-1.5 hover:bg-slate-100 disabled:opacity-60"
          >
            {summarizing ? 'Summarizing...' : doc?.summary ? (showSummary ? 'Hide summary' : 'Summary') : 'Summarize'}
          </button>
          <button onClick={handleClear} className="rounded-md border border-slate-300 px-3 py-1.5 hover:bg-slate-100">
            Clear chat
          </button>
        </div>
      </div>
      {error && <p className="bg-red-50 px-4 py-2 text-sm text-red-700">{error}</p>}
      {showSummary && doc?.summary && (
        <div className="max-h-48 overflow-y-auto border-b border-slate-200 bg-indigo-50 px-4 py-3 text-sm">
          <div className="mb-1 flex items-center justify-between">
            <span className="font-semibold text-indigo-800">Summary</span>
            <button onClick={handleSummarize} disabled={summarizing} className="text-xs text-indigo-600 hover:underline">Regenerate</button>
          </div>
          <p className="whitespace-pre-wrap text-slate-700">{doc.summary}</p>
        </div>
      )}
      <ChatWindow docId={id} messages={messages} setMessages={setMessages} />
    </div>
  )
}
