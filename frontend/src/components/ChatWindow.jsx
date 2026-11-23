import { useEffect, useRef, useState } from 'react'
import { askQuestion } from '../api/chat'
import { errorMessage } from '../api/client'
import MessageBubble from './MessageBubble'
import Spinner from './Spinner'

const SUGGESTIONS = ['Summarize the key points', 'What are the main conclusions?', 'List important dates or numbers']

export default function ChatWindow({ docId, messages, setMessages }) {
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, sending])

  const send = async (text) => {
    const question = text.trim()
    if (!question || sending) return
    setInput('')
    setSending(true)
    const tempId = `tmp-${Date.now()}`
    setMessages((m) => [...m, { id: tempId, role: 'user', content: question }])
    try {
      const { user_message, assistant_message } = await askQuestion(docId, question)
      setMessages((m) => [...m.filter((x) => x.id !== tempId), user_message, assistant_message])
    } catch (err) {
      setMessages((m) => [
        ...m,
        { id: `err-${Date.now()}`, role: 'assistant', error: true, content: errorMessage(err, 'Failed to get an answer.') },
      ])
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex-1 space-y-4 overflow-y-auto px-4 py-4">
        {messages.length === 0 && (
          <div className="mx-auto mt-10 max-w-md text-center">
            <p className="text-sm text-slate-500">Ask anything about this document. Try:</p>
            <div className="mt-3 flex flex-wrap justify-center gap-2">
              {SUGGESTIONS.map((s) => (
                <button key={s} onClick={() => send(s)} className="rounded-full border border-slate-300 bg-white px-3 py-1.5 text-xs hover:border-indigo-400 hover:text-indigo-700">
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m) => <MessageBubble key={m.id} message={m} />)}
        {sending && (
          <div className="flex items-center gap-2 text-sm text-slate-500"><Spinner className="h-4 w-4" /> Thinking...</div>
        )}
        <div ref={bottomRef} />
      </div>
      <form
        onSubmit={(e) => { e.preventDefault(); send(input) }}
        className="flex gap-2 border-t border-slate-200 bg-white p-3"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          maxLength={2000}
          placeholder="Ask a question about this document..."
          className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"
        />
        <button
          disabled={sending || !input.trim()}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  )
}
