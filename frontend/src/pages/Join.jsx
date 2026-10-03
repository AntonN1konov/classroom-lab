import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import api from '../services/api'
import { useAuthStore } from '../store/authStore'
import './Login.css'
import './Join.css'

// Страница ссылки-приглашения: /join/<token>
function Join() {
  const { token } = useParams()
  const navigate = useNavigate()
  const { isAuthenticated, user, login, register, logout, initAuth } = useAuthStore()
  const [invite, setInvite] = useState(null)
  const [inviteError, setInviteError] = useState('')
  const [mode, setMode] = useState('register') // register | login
  const [form, setForm] = useState({ username: '', email: '', full_name: '', password: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => { initAuth() }, [initAuth])

  useEffect(() => {
    api.get(`/invites/${token}`)
      .then(({ data }) => setInvite(data))
      .catch((err) => setInviteError(err.response?.data?.detail || 'Приглашение не найдено'))
  }, [token])

  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  const join = async () => {
    const { data } = await api.post(`/invites/${token}/join`)
    navigate('/student', { replace: true, state: { sessionId: data.session_id } })
  }

  const handleJoin = async () => {
    setError('')
    setBusy(true)
    try {
      await join()
    } catch (err) {
      setError(err.response?.data?.detail || 'Не удалось присоединиться')
    }
    setBusy(false)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      if (mode === 'register') {
        const result = await register({ ...form, role: 'student' })
        if (!result.success) throw new Error(result.error)
      }
      const result = await login(form.username, form.password)
      if (!result.success) throw new Error(result.error)
      await join()
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Ошибка')
    }
    setBusy(false)
  }

  if (inviteError) {
    return (
      <div className="login-container">
        <div className="login-card">
          <h1>Приглашение</h1>
          <div className="error-message">{inviteError}</div>
        </div>
      </div>
    )
  }

  if (!invite) {
    return <div className="login-container"><div className="login-card">Загрузка...</div></div>
  }

  return (
    <div className="login-container">
      <div className="login-card join-card">
        <p className="join-kicker">Вас пригласили в сессию</p>
        <h1 className="join-title">{invite.session_name}</h1>
        {invite.teacher_name && <p className="join-teacher">Преподаватель: {invite.teacher_name}</p>}
        {invite.session_description && <p className="join-description">{invite.session_description}</p>}

        {error && <div className="error-message">{error}</div>}

        {isAuthenticated && user ? (
          user.role === 'student' ? (
            <>
              <p className="setup-hint">Вы вошли как <b>{user.full_name}</b>.</p>
              <button className="submit-btn" onClick={handleJoin} disabled={busy}>
                {busy ? 'Подождите...' : 'Присоединиться'}
              </button>
              <p className="register-link">
                Не вы? <a href="#" onClick={(e) => { e.preventDefault(); logout() }}>Войти под другим аккаунтом</a>
              </p>
            </>
          ) : (
            <>
              <p className="setup-hint">
                Вы вошли как преподаватель ({user.full_name}). По приглашению присоединяются студенты.
              </p>
              <button className="submit-btn" onClick={() => logout()}>Выйти и войти как студент</button>
            </>
          )
        ) : (
          <>
            <div className="join-tabs">
              <button className={mode === 'register' ? 'active' : ''} onClick={() => { setMode('register'); setError('') }}>
                Я здесь впервые
              </button>
              <button className={mode === 'login' ? 'active' : ''} onClick={() => { setMode('login'); setError('') }}>
                У меня есть аккаунт
              </button>
            </div>
            <form onSubmit={handleSubmit}>
              {mode === 'register' && (
                <>
                  <div className="form-group">
                    <label>Имя и фамилия</label>
                    <input type="text" value={form.full_name} onChange={set('full_name')} required disabled={busy} />
                  </div>
                  <div className="form-group">
                    <label>Email</label>
                    <input type="email" value={form.email} onChange={set('email')} required disabled={busy} />
                  </div>
                </>
              )}
              <div className="form-group">
                <label>Логин</label>
                <input type="text" value={form.username} onChange={set('username')} required disabled={busy} autoComplete="username" />
              </div>
              <div className="form-group">
                <label>Пароль</label>
                <input
                  type="password"
                  value={form.password}
                  onChange={set('password')}
                  required
                  disabled={busy}
                  autoComplete={mode === 'register' ? 'new-password' : 'current-password'}
                />
              </div>
              <button type="submit" className="submit-btn" disabled={busy}>
                {busy ? 'Подождите...' : mode === 'register' ? 'Зарегистрироваться и войти' : 'Войти и присоединиться'}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  )
}

export default Join
