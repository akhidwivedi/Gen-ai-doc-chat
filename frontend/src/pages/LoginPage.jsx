import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import AuthForm from '../components/AuthForm'
import { useAuth } from '../context/AuthContext'

export default function LoginPage() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const dest = location.state?.from?.pathname || '/'

  if (user) return <Navigate to={dest} replace />

  return (
    <AuthForm
      title="Welcome back"
      submitLabel="Log in"
      fields={[
        { name: 'username', label: 'Username', autoComplete: 'username' },
        { name: 'password', label: 'Password', type: 'password', autoComplete: 'current-password' },
      ]}
      onSubmit={async (v) => { await login(v); navigate(dest, { replace: true }) }}
      footer={{ text: 'No account?', link: 'Sign up', to: '/register' }}
    />
  )
}
