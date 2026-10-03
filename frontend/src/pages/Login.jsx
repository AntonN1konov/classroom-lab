import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api from '../services/api'
import { useAuthStore } from '../store/authStore'
import './Login.css'

function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [setup, setSetup] = useState(null)
  
  const { login, isAuthenticated, user } = useAuthStore()
  const navigate = useNavigate()

  useEffect(() => {
    if (isAuthenticated) {
      navigate(user?.role === 'teacher' ? '/teacher' : '/student', { replace: true })
    }
  }, [isAuthenticated, user, navigate])

  useEffect(() => {
    // В установленной версии напоминаем настроить YandexGPT
    api.get('/setup/status').then(({ data }) => setSetup(data)).catch(() => {})
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    const result = await login(username, password)
    
    if (result.success) {
      navigate(user?.role === 'teacher' ? '/teacher' : '/student', { replace: true })
    } else {
      setError(result.error)
    }
    
    setLoading(false)
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <h1>YandexGPT Office Laboratory</h1>
        <h2>Вход в систему</h2>
        {setup && !setup.configured && (
          <div className="setup-banner">
            YandexGPT ещё не подключён.{' '}
            {setup.editable
              ? <Link to="/setup">Настроить</Link>
              : 'Попросите преподавателя завершить настройку.'}
          </div>
        )}
        <form onSubmit={handleSubmit}>
          {error && <div className="error-message">{error}</div>}
          <div className="form-group">
            <label>Имя пользователя</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              disabled={loading}
            />
          </div>
          <div className="form-group">
            <label>Пароль</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={loading}
            />
          </div>
          <button type="submit" disabled={loading} className="submit-btn">
            {loading ? 'Вход...' : 'Войти'}
          </button>
        </form>
        <p className="register-link">
          Нет аккаунта? <a href="/register">Зарегистрироваться</a>
        </p>
      </div>
    </div>
  )
}

export default Login

