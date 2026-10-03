import { useState, useEffect } from 'react'
import api from '../services/api'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import './Register.css'

function Register() {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    full_name: '',
    password: '',
    role: 'student'
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [canTeacher, setCanTeacher] = useState(false)

  useEffect(() => {
    // Преподавателя можно создать только на компьютере с сервером (или самого первого)
    api.get('/auth/registration-options')
      .then(({ data }) => setCanTeacher(data.can_register_teacher))
      .catch(() => {})
  }, [])
  
  const { register, login } = useAuthStore()
  const navigate = useNavigate()

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    const result = await register(formData)
    
    if (result.success) {
      const loginResult = await login(formData.username, formData.password)
      if (loginResult.success) {
        navigate(formData.role === 'teacher' ? '/teacher' : '/student', { replace: true })
      }
    } else {
      setError(result.error)
    }
    
    setLoading(false)
  }

  return (
    <div className="register-container">
      <div className="register-card">
        <h1>Регистрация</h1>
        <form onSubmit={handleSubmit}>
          {error && <div className="error-message">{error}</div>}
          <div className="form-group">
            <label>Имя пользователя</label>
            <input
              type="text"
              name="username"
              value={formData.username}
              onChange={handleChange}
              required
              disabled={loading}
            />
          </div>
          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              disabled={loading}
            />
          </div>
          <div className="form-group">
            <label>Полное имя</label>
            <input
              type="text"
              name="full_name"
              value={formData.full_name}
              onChange={handleChange}
              required
              disabled={loading}
            />
          </div>
          <div className="form-group">
            <label>Пароль</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              disabled={loading}
            />
          </div>
          {canTeacher && (
            <div className="form-group">
              <label>Роль</label>
              <select
                name="role"
                value={formData.role}
                onChange={handleChange}
                disabled={loading}
              >
                <option value="student">Студент</option>
                <option value="teacher">Преподаватель</option>
              </select>
            </div>
          )}
          <button type="submit" disabled={loading} className="submit-btn">
            {loading ? 'Регистрация...' : 'Зарегистрироваться'}
          </button>
        </form>
        <p className="login-link">
          Уже есть аккаунт? <Link to="/login">Войти</Link>
        </p>
      </div>
    </div>
  )
}

export default Register

