import { Navigate, useNavigate } from 'react-router-dom'
import AuthForm from '../components/AuthForm'
import { useAuth } from '../context/AuthContext'

export default function RegisterPage() {
  const { user, register } = useAuth()
  const navigate = useNavigate()

  if (user) return <Navigate to="/" replace />

  return (
    <AuthForm
      title="Create your account"
      submitLabel="Sign up"
      fields={[
        { name: 'username', label: 'Username', autoComplete: 'username' },
        { name: 'email', label: 'Email', type: 'email', autoComplete: 'email' },
        { name: 'password', label: 'Password', type: 'password', autoComplete: 'new-password' },
      ]}
      onSubmit={async (v) => { await register(v); navigate('/', { replace: true }) }}
      footer={{ text: 'Already registered?', link: 'Log in', to: '/login' }}
    />
  )
}
