import { useRef, useState } from 'react'
import { errorMessage } from '../api/client'
import { uploadDocument } from '../api/documents'

const ACCEPT = '.pdf,.docx,.txt'

export default function UploadBox({ onUploaded }) {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)
  const [progress, setProgress] = useState(null) // null = idle, 0-100 uploading, 100 = processing
  const [error, setError] = useState('')

  const send = async (file) => {
    if (!file) return
    setError('')
    setProgress(0)
    try {
      const doc = await uploadDocument(file, setProgress)
      onUploaded(doc)
    } catch (err) {
      setError(errorMessage(err, 'Upload failed.'))
    } finally {
      setProgress(null)
      if (inputRef.current) inputRef.current.value = ''
    }
  }

  const busy = progress !== null

  return (
    <div>
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); send(e.dataTransfer.files[0]) }}
        onClick={() => !busy && inputRef.current?.click()}
        className={`cursor-pointer rounded-xl border-2 border-dashed p-8 text-center transition ${
          dragging ? 'border-indigo-500 bg-indigo-50' : 'border-slate-300 bg-white hover:border-indigo-400'
        } ${busy ? 'cursor-wait opacity-80' : ''}`}
      >
        <input ref={inputRef} type="file" accept={ACCEPT} className="hidden" onChange={(e) => send(e.target.files[0])} />
        {busy ? (
          <div className="mx-auto max-w-xs">
            <p className="text-sm font-medium text-slate-700">
              {progress < 100 ? `Uploading... ${progress}%` : 'Processing and indexing (first time may take a minute)...'}
            </p>
            <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-200">
              <div
                className={`h-full bg-indigo-600 transition-all ${progress >= 100 ? 'animate-pulse' : ''}`}
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        ) : (
          <>
            <p className="text-sm font-medium text-slate-800">Drop a file here or click to upload</p>
            <p className="mt-1 text-xs text-slate-500">PDF, DOCX or TXT, up to 20 MB</p>
          </>
        )}
      </div>
      {error && <p className="mt-2 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
    </div>
  )
}
