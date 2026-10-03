import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'
import './Login.css'

// Первичная настройка установленной версии: ключ YandexGPT и Folder ID.
// Доступна только на компьютере, где запущен сервер.
function Setup() {
  const [status, setStatus] = useState(null)
  const [folderId, setFolderId] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    api.get('/setup/status')
      .then(({ data }) => {
        setStatus(data)
        setFolderId(data.folder_id || '')
      })
      .catch(() => setStatus({ configured: false, editable: false }))
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await api.post('/setup/', { folder_id: folderId, api_key: apiKey })
      setSaved(true)
      setApiKey('')
    } catch (err) {
      setError(err.response?.data?.detail || 'Не удалось сохранить настройки')
    }
    setLoading(false)
  }

  if (!status) {
    return <div className="login-container"><div className="login-card">Загрузка...</div></div>
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <h1>Настройка</h1>
        <h2>Подключение к YandexGPT</h2>

        {!status.editable ? (
          <p className="setup-hint">
            Настройки можно изменить только на компьютере, где запущен сервер.
          </p>
        ) : saved ? (
          <>
            <div className="success-message">Настройки сохранены.</div>
            <Link to="/login" className="submit-btn setup-link">Перейти ко входу</Link>
          </>
        ) : (
          <form onSubmit={handleSubmit}>
            {status.configured && (
              <p className="setup-hint">Ключ уже задан. Заполните форму, чтобы заменить его.</p>
            )}
            {error && <div className="error-message">{error}</div>}
            <div className="form-group">
              <label>Folder ID (каталог Yandex Cloud)</label>
              <input
                type="text"
                value={folderId}
                onChange={(e) => setFolderId(e.target.value)}
                placeholder="b1g..."
                required
                disabled={loading}
              />
            </div>
            <div className="form-group">
              <label>API-ключ YandexGPT</label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                autoComplete="off"
                required
                disabled={loading}
              />
            </div>
            <button type="submit" disabled={loading} className="submit-btn">
              {loading ? 'Сохранение...' : 'Сохранить'}
            </button>
            <p className="setup-hint">
              Ключ и Folder ID создаются в консоли Yandex Cloud: сервисный аккаунт с ролью
              «ai.languageModels.user» → «Создать API-ключ».
            </p>
          </form>
        )}

        {status.configured && !saved && (
          <p className="register-link"><Link to="/login">Ко входу</Link></p>
        )}
      </div>
    </div>
  )
}

export default Setup
