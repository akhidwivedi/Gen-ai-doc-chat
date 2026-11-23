import { useState } from 'react'

export default function MessageBubble({ message }) {
  const [showSources, setShowSources] = useState(false)
  const isUser = message.role === 'user'
  const sources = message.sources || []

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
          isUser ? 'bg-indigo-600 text-white' : message.error ? 'bg-red-50 text-red-700' : 'border border-slate-200 bg-white'
        }`}
      >
        <p className="whitespace-pre-wrap">{message.content}</p>
        {!isUser && sources.length > 0 && (
          <div className="mt-2 border-t border-slate-100 pt-2">
            <button onClick={() => setShowSources(!showSources)} className="text-xs font-medium text-indigo-600 hover:underline">
              {showSources ? 'Hide' : 'Show'} sources ({sources.length})
            </button>
            {showSources && (
              <ul className="mt-2 space-y-2">
                {sources.map((s, i) => (
                  <li key={i} className="rounded-md bg-slate-50 p-2 text-xs text-slate-600">
                    <span className="font-semibold">{s.page ? `Page ${s.page}` : `Excerpt ${i + 1}`}</span>
                    <span className="text-slate-400"> · match {Math.round(s.score * 100)}%</span>
                    <p className="mt-1 whitespace-pre-wrap">{s.snippet}</p>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
