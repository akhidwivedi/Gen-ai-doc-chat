import { useState } from 'react'
import { Link } from 'react-router-dom'
import { errorMessage } from '../api/client'
import Spinner from './Spinner'

/** Shared layout for the login and register pages. */
export default function AuthForm({ title, fields, submitLabel, onSubmit, footer }) {
  const [values, setValues] = useState(Object.fromEntries(fields.map((f) => [f.name, ''])))
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const handle = async (e) => {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      await onSubmit(values)
    } catch (err) {
      setError(errorMessage(err))
      setBusy(false)
    }
  }

  return (
    <div className="mx-auto mt-16 w-full max-w-sm px-4">
      <form onSubmit={handle} className="space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="text-xl font-semibold">{title}</h1>
        {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
        {fields.map((f) => (
          <label key={f.name} className="block text-sm font-medium text-slate-700">
            {f.label}
            <input
              type={f.type || 'text'}
              required
              autoComplete={f.autoComplete}
              value={values[f.name]}
              onChange={(e) => setValues({ ...values, [f.name]: e.target.value })}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm font-normal outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"
            />
          </label>
        ))}
        <button
          disabled={busy}
          className="flex w-full items-center justify-center gap-2 rounded-md bg-indigo-600 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-60"
        >
          {busy && <Spinner className="h-4 w-4 text-white" />}
          {submitLabel}
        </button>
        <p className="text-center text-sm text-slate-500">
          {footer.text} <Link className="font-medium text-indigo-600 hover:underline" to={footer.to}>{footer.link}</Link>
        </p>
      </form>
    </div>
  )
}
