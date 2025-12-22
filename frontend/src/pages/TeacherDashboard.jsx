import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../services/api'
import SessionSelector from '../components/SessionSelector'
import YandexGPTChat from '../components/YandexGPTChat'
import GroupChat from '../components/GroupChat'
import StudentContextWindows from '../components/StudentContextWindows'
import SessionManager from '../components/SessionManager'
import './TeacherDashboard.css'

function TeacherDashboard() {
  const [selectedSession, setSelectedSession] = useState(null)
  const queryClient = useQueryClient()

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

  return (
    <div className="teacher-dashboard">
      <div className="dashboard-header">
        <h2>Виртуальный кабинет-лаборатория | Преподаватель</h2>
        <SessionManager />
      </div>

      <div className="dashboard-content">
        <div className="dashboard-left">
          <SessionSelector
            sessions={sessions || []}
            selectedSession={selectedSession}
            onSelectSession={setSelectedSession}
          />
        </div>

        {selectedSession && (
          <div className="dashboard-main">
            <div className="dashboard-row">
              <div className="dashboard-col">
                <YandexGPTChat sessionId={selectedSession} />
              </div>
              <div className="dashboard-col">
                <GroupChat sessionId={selectedSession} />
              </div>
            </div>
            <div className="dashboard-row">
              <StudentContextWindows sessionId={selectedSession} />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default TeacherDashboard

