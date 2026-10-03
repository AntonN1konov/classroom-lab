import { useState } from 'react'
import api from '../services/api'

// Включение/выключение доступа из интернета (Cloudflare Tunnel).
function InternetAccess({ tunnel, onChange }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const toggle = async (action) => {
    setBusy(true)
    setError('')
    try {
      await api.post(`/setup/tunnel/${action}`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Не удалось изменить доступ из интернета')
    }
    setBusy(false)
    onChange?.()
  }

  if (!tunnel) return null

  return (
    <div className={`internet-access ${tunnel.running ? 'on' : ''}`}>
      <div className="internet-access-row">
        <div>
          <div className="internet-access-title">
            Доступ из интернета: {tunnel.running ? 'включён' : 'выключен'}
          </div>
          <div className="internet-access-note">
            {tunnel.running
              ? <>Адрес: <b>{tunnel.url}</b></>
              : 'Студенты смогут зайти из любой сети, а не только из вашей Wi-Fi.'}
          </div>
        </div>
        {tunnel.editable && tunnel.available && (
          <button
            type="button"
            className={tunnel.running ? 'secondary-btn small' : 'submit-btn small'}
            onClick={() => toggle(tunnel.running ? 'stop' : 'start')}
            disabled={busy}
          >
            {busy ? (tunnel.running ? 'Выключаю...' : 'Подключаю...') : tunnel.running ? 'Выключить' : 'Включить'}
          </button>
        )}
      </div>
      {!tunnel.editable && !tunnel.running && (
        <div className="internet-access-note">Включается на компьютере, где запущен сервер.</div>
      )}
      {tunnel.editable && !tunnel.available && (
        <div className="internet-access-note">Компонент cloudflared не найден — переустановите программу.</div>
      )}
      {error && <div className="setup-message error">{error}</div>}
      {tunnel.running && (
        <div className="internet-access-note">
          Работает, пока запущен сервер. После перезапуска адрес изменится — ссылки нужно будет отправить заново.
        </div>
      )}
    </div>
  )
}

export default InternetAccess
