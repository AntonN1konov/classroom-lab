import { useEffect, useState, useCallback } from 'react'
import api from '../services/api'
import InternetAccess from './InternetAccess'
import './InviteDialog.css'

const isLocalHost = (host) => ['localhost', '127.0.0.1', '[::1]'].includes(host)

// Ссылка-приглашение в сессию
function InviteDialog({ sessionId, onClose }) {
  const [token, setToken] = useState(null)
  const [addresses, setAddresses] = useState(null)
  const [base, setBase] = useState('')
  const [copied, setCopied] = useState(false)
  const [error, setError] = useState('')

  const loadAddresses = useCallback(async () => {
    const { data } = await api.get('/setup/addresses')
    setAddresses(data)
    return data
  }, [])

  useEffect(() => {
    api.post(`/sessions/${sessionId}/invite`)
      .then(({ data }) => setToken(data.token))
      .catch((err) => setError(err.response?.data?.detail || 'Не удалось создать приглашение'))
    loadAddresses().catch(() => setAddresses({ tunnel: null }))
  }, [sessionId, loadAddresses])

  // Варианты адреса сервера для ссылки
  const options = []
  if (addresses?.public_url) options.push({ value: addresses.public_url, label: 'Из интернета' })
  if (!isLocalHost(window.location.hostname) && !options.some((o) => o.value === window.location.origin)) {
    options.push({ value: window.location.origin, label: 'Текущий адрес' })
  }
  if (addresses?.lan_url && !options.some((o) => o.value === addresses.lan_url)) {
    options.push({ value: addresses.lan_url, label: 'Только локальная сеть' })
  }
  if (options.length === 0) options.push({ value: window.location.origin, label: 'Этот компьютер' })

  useEffect(() => {
    if (!options.some((o) => o.value === base)) setBase(options[0].value)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [addresses])

  const link = token && base ? `${base}/join/${token}` : ''

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(link)
    } catch {
      // Буфер обмена недоступен по http: выделяем текст, чтобы скопировать вручную
      document.getElementById('invite-link')?.select()
      return
    }
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const reset = async () => {
    const { data } = await api.post(`/sessions/${sessionId}/invite/reset`)
    setToken(data.token)
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content invite-modal" onClick={(e) => e.stopPropagation()}>
        <h3>Пригласить студентов</h3>
        <p className="invite-hint">
          Отправьте ссылку студентам. Перейдя по ней, они зарегистрируются (или войдут) и сразу попадут в эту сессию.
        </p>

        {error && <div className="session-students-error">{error}</div>}

        <InternetAccess tunnel={addresses?.tunnel} onChange={loadAddresses} />

        {options.length > 1 && (
          <div className="invite-options">
            {options.map((o) => (
              <label key={o.value} className={base === o.value ? 'selected' : ''}>
                <input type="radio" checked={base === o.value} onChange={() => setBase(o.value)} />
                {o.label}
              </label>
            ))}
          </div>
        )}

        <div className="invite-link-row">
          <input id="invite-link" readOnly value={link || 'Создаю ссылку...'} onFocus={(e) => e.target.select()} />
          <button className="add-student-item-btn" onClick={copy} disabled={!link}>
            {copied ? 'Скопировано' : 'Копировать'}
          </button>
        </div>

        {base && isLocalHost(new URL(base).hostname) && (
          <p className="invite-warning">
            Это адрес только для этого компьютера. Чтобы пригласить других, включите доступ из интернета.
          </p>
        )}

        <div className="modal-actions invite-actions">
          <button type="button" className="link-btn" onClick={reset}>Сбросить ссылку</button>
          <button type="button" className="cancel-btn" onClick={onClose}>Готово</button>
        </div>
      </div>
    </div>
  )
}

export default InviteDialog
