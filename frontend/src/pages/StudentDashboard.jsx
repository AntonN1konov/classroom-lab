import { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import api from '../services/api'
import { useAuthStore } from '../store/authStore'
import SessionSelector from '../components/SessionSelector'
import YandexGPTChat from '../components/YandexGPTChat'
import GroupChat from '../components/GroupChat'
import StudentContextWindow from '../components/StudentContextWindow'
import './StudentDashboard.css'

function StudentDashboard() {
  const location = useLocation()
  // После перехода по приглашению открываем сессию, в которую вступили
  const [selectedSession, setSelectedSession] = useState(location.state?.sessionId || null)
  const { user } = useAuthStore()

  const { data: sessions, isLoading } = useQuery({
    queryKey: ['sessions'],
    queryFn: async () => {
      const response = await api.get('/sessions/')
      return response.data
    },
  })

  useEffect(() => {
    if (sessions && sessions.length > 0 && !selectedSession) {
      setSelectedSession(sessions[0].id)
    }
  }, [sessions, selectedSession])

  if (isLoading) {
    return <div className="loading">Загрузка...</div>
  }

  if (!sessions || sessions.length === 0) {
    return (
      <div className="no-sessions">
        <p>У вас пока нет сессий. Попросите у преподавателя ссылку-приглашение.</p>
      </div>
    )
  }

  return (
    <div className="student-dashboard">
      <div className="dashboard-header">
        <h2>Виртуальный кабинет-лаборатория | Студент</h2>
      </div>

      <div className="dashboard-content">
        <div className="dashboard-left">
          <SessionSelector
            sessions={sessions}
            selectedSession={selectedSession}
            onSelectSession={setSelectedSession}
          />
        </div>

        {selectedSession && (
          <div className="dashboard-main">
            <div className="dashboard-row">
              <div className="dashboard-col">
                <YandexGPTChat sessionId={selectedSession} readOnly={true} />
              </div>
              <div className="dashboard-col">
                <GroupChat sessionId={selectedSession} />
              </div>
            </div>
            <div className="dashboard-row">
              <StudentContextWindow sessionId={selectedSession} />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default StudentDashboard

