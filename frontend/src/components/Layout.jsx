import { useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import './Layout.css'

function Layout({ children }) {
  const { user, logout, initAuth, isAuthenticated } = useAuthStore()
  const navigate = useNavigate()

  useEffect(() => {
    initAuth()
  }, [initAuth])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  if (!isAuthenticated) {
    return null
  }

  return (
    <div className="layout">
      <header className="layout-header">
        <div className="layout-header-content">
          <h1>YandexGPT Office Laboratory</h1>
          <div className="layout-header-user">
            <span>{user?.full_name} ({user?.role === 'teacher' ? 'Преподаватель' : 'Студент'})</span>
            {user?.role === 'teacher' && (
              <Link to="/setup" className="logout-btn settings-btn">Настройки ИИ</Link>
            )}
            <button onClick={handleLogout} className="logout-btn">
              Выход
            </button>
          </div>
        </div>
      </header>
      <main className="layout-main">
        {children}
      </main>
    </div>
  )
}

export default Layout

