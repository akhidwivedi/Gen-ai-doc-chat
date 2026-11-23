import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
        <Link to="/" className="flex items-center gap-2 text-lg font-semibold text-indigo-700">
          <span className="grid h-7 w-7 place-items-center rounded-lg bg-indigo-600 text-sm text-white">D</span>
          DocChat
        </Link>
        {user ? (
          <div className="flex items-center gap-4 text-sm">
            <span className="hidden text-slate-500 sm:inline">{user.username}</span>
            <button
              onClick={() => { logout(); navigate('/login') }}
              className="rounded-md border border-slate-300 px-3 py-1.5 font-medium text-slate-700 hover:bg-slate-100"
            >
              Log out
            </button>
          </div>
        ) : (
          <nav className="flex gap-3 text-sm font-medium">
            <Link to="/login" className="text-slate-600 hover:text-indigo-700">Log in</Link>
            <Link to="/register" className="text-slate-600 hover:text-indigo-700">Sign up</Link>
          </nav>
        )}
      </div>
    </header>
  )
}
