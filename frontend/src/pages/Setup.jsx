import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'
import { useAuthStore } from '../store/authStore'
import InternetAccess from '../components/InternetAccess'
import '../components/InviteDialog.css'
import './Login.css'
import './Setup.css'

const PROVIDERS = [
  {
    id: 'demo',
    title: 'Демо-режим',
    note: 'Бесплатно. Модель не подключена: на запросы приходят тестовые ответы. Подходит, чтобы проверить интерфейс и сценарии.',
  },
  {
    id: 'ollama',
    title: 'Локальная модель (Ollama)',
    note: 'Бесплатно. Модель работает на этом компьютере. Нужно установить Ollama и скачать модель.',
  },
  {
    id: 'openai',
    title: 'Локальная модель (LM Studio)',
    note: 'Бесплатно. Модель работает на этом компьютере в LM Studio. Подходит и любой сервер с API в формате OpenAI.',
  },
  {
    id: 'yandexgpt',
    title: 'YandexGPT',
    note: 'Платно, по тарифам Yandex Cloud. Нужны Folder ID и API-ключ сервисного аккаунта.',
  },
]

const errorText = (err, fallback) => err.response?.data?.detail || fallback

// Выбор и проверка языковой модели. Менять можно только на компьютере с сервером.
function Setup() {
  const { isAuthenticated, user } = useAuthStore()
  const [status, setStatus] = useState(null)
  const [form, setForm] = useState({ provider: 'demo', folder_id: '', api_key: '', ollama_url: '', ollama_model: '', openai_url: '', openai_model: '' })
  const [message, setMessage] = useState(null) // {type: 'error'|'success'|'info', text}
  const [busy, setBusy] = useState(false)
  const [tunnel, setTunnel] = useState(null)

  const loadTunnel = () => api.get('/setup/addresses').then(({ data }) => setTunnel(data.tunnel)).catch(() => {})

  useEffect(() => {
    api.get('/setup/status')
      .then(({ data }) => {
        setStatus(data)
        setForm((f) => ({
          ...f,
          provider: data.provider,
          folder_id: data.folder_id || '',
          ollama_url: data.ollama_url || '',
          ollama_model: data.ollama_model || '',
          openai_url: data.openai_url || '',
          openai_model: data.openai_model || '',
        }))
      })
      .catch(() => setStatus({ editable: false }))
    loadTunnel()
  }, [])

  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  const payload = () => ({ ...form, api_key: form.api_key || null })

  const testConnection = async () => {
    setBusy(true)
    setMessage({ type: 'info', text: 'Отправляю пробный запрос...' })
    try {
      const { data } = await api.post('/setup/test', payload())
      setMessage({ type: 'success', text: `Модель ответила: «${data.response.trim().slice(0, 200)}»` })
    } catch (err) {
      setMessage({ type: 'error', text: errorText(err, 'Не удалось проверить подключение') })
    }
    setBusy(false)
  }

  const save = async (e) => {
    e.preventDefault()
    setBusy(true)
    try {
      const { data } = await api.post('/setup/', payload())
      setStatus((s) => ({ ...s, provider: data.provider, label: data.label, has_api_key: s.has_api_key || !!form.api_key }))
      setForm((f) => ({ ...f, api_key: '' }))
      setMessage({ type: 'success', text: `Сохранено. Сейчас используется: ${data.label}.` })
    } catch (err) {
      setMessage({ type: 'error', text: errorText(err, 'Не удалось сохранить настройки') })
    }
    setBusy(false)
  }

  const backLink = isAuthenticated
    ? <Link to={user?.role === 'teacher' ? '/teacher' : '/student'}>← Вернуться в кабинет</Link>
    : <Link to="/login">{status?.first_run ? 'Настроить позже и перейти ко входу →' : 'Ко входу →'}</Link>

  if (!status) {
    return <div className="login-container"><div className="login-card">Загрузка...</div></div>
  }

  return (
    <div className="login-container">
      <div className="login-card setup-card">
        <h1>Настройки</h1>
        <h2>Какую модель использовать в чатах</h2>

        {!status.editable ? (
          <p className="setup-hint">
            Сейчас используется: <b>{status.label}</b>.<br />
            Изменить модель можно только на компьютере, где запущен сервер Classroom Lab.
          </p>
        ) : (
          <form onSubmit={save}>
            <div className="provider-list">
              {PROVIDERS.map((p) => (
                <label key={p.id} className={`provider-option ${form.provider === p.id ? 'selected' : ''}`}>
                  <input
                    type="radio"
                    name="provider"
                    value={p.id}
                    checked={form.provider === p.id}
                    onChange={() => { setForm({ ...form, provider: p.id }); setMessage(null) }}
                  />
                  <span>
                    <span className="provider-title">
                      {p.title}
                      {status.provider === p.id && <span className="provider-current">используется</span>}
                    </span>
                    <span className="provider-note">{p.note}</span>
                  </span>
                </label>
              ))}
            </div>

            {form.provider === 'ollama' && (
              <div className="provider-fields">
                <ol className="setup-steps">
                  <li>Установите Ollama с сайта <a href="https://ollama.com/download" target="_blank" rel="noreferrer">ollama.com</a>.</li>
                  <li>В командной строке скачайте модель: <code>ollama pull {form.ollama_model || 'qwen2.5:3b'}</code></li>
                  <li>Нажмите «Проверить подключение».</li>
                </ol>
                <div className="form-group">
                  <label>Модель</label>
                  <input type="text" value={form.ollama_model} onChange={set('ollama_model')} placeholder="qwen2.5:3b" />
                </div>
                <div className="form-group">
                  <label>Адрес Ollama</label>
                  <input type="text" value={form.ollama_url} onChange={set('ollama_url')} placeholder="http://127.0.0.1:11434" />
                </div>
              </div>
            )}

            {form.provider === 'openai' && (
              <div className="provider-fields">
                <ol className="setup-steps">
                  <li>Установите <a href="https://lmstudio.ai" target="_blank" rel="noreferrer">LM Studio</a> и скачайте модель, например Qwen2.5 3B Instruct.</li>
                  <li>На вкладке <b>Developer</b> загрузите модель и включите сервер (Status: Running).</li>
                  <li>Нажмите «Проверить подключение».</li>
                </ol>
                <div className="form-group">
                  <label>Модель</label>
                  <input type="text" value={form.openai_model} onChange={set('openai_model')} placeholder="Пусто — загруженная в LM Studio" />
                </div>
                <div className="form-group">
                  <label>Адрес сервера</label>
                  <input type="text" value={form.openai_url} onChange={set('openai_url')} placeholder="http://127.0.0.1:1234/v1" />
                </div>
              </div>
            )}

            {form.provider === 'yandexgpt' && (
              <div className="provider-fields">
                <div className="form-group">
                  <label>Folder ID (каталог Yandex Cloud)</label>
                  <input type="text" value={form.folder_id} onChange={set('folder_id')} placeholder="b1g..." required />
                </div>
                <div className="form-group">
                  <label>API-ключ</label>
                  <input
                    type="password"
                    value={form.api_key}
                    onChange={set('api_key')}
                    autoComplete="off"
                    placeholder={status.has_api_key ? 'Сохранён. Оставьте пустым, чтобы не менять' : ''}
                    required={!status.has_api_key}
                  />
                </div>
                <p className="setup-hint">
                  Сервисный аккаунт с ролью <code>ai.languageModels.user</code>, ключ с областью
                  действия <code>yc.ai.languageModels.execute</code>. Каждый запрос тарифицируется.
                </p>
              </div>
            )}

            {message && <div className={`setup-message ${message.type}`}>{message.text}</div>}

            <div className="setup-actions">
              {form.provider !== 'demo' && (
                <button type="button" className="secondary-btn" onClick={testConnection} disabled={busy}>
                  Проверить подключение
                </button>
              )}
              <button type="submit" className="submit-btn" disabled={busy}>
                {busy ? 'Подождите...' : 'Сохранить'}
              </button>
            </div>
          </form>
        )}

        {status.editable && tunnel && (
          <div className="setup-section">
            <h2>Доступ для студентов</h2>
            <InternetAccess tunnel={tunnel} onChange={loadTunnel} />
          </div>
        )}

        <p className="register-link">{backLink}</p>
      </div>
    </div>
  )
}

export default Setup
