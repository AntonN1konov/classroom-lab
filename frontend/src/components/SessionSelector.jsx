import './SessionSelector.css'

function SessionSelector({ sessions, selectedSession, onSelectSession }) {
  return (
    <div className="session-selector">
      <h3>Сессии</h3>
      <div className="session-list">
        {sessions.map((session) => (
          <div
            key={session.id}
            className={`session-item ${selectedSession === session.id ? 'active' : ''}`}
            onClick={() => onSelectSession(session.id)}
          >
            <div className="session-name">{session.name}</div>
            <div className="session-status">
              {session.is_active ? (
                <span className="status-active">Активна</span>
              ) : (
                <span className="status-inactive">Неактивна</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default SessionSelector

