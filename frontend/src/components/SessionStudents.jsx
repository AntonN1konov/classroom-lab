import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../services/api'
import './SessionManager.css'
import './SessionStudents.css'

function SessionStudents({ sessionId }) {
  const [showModal, setShowModal] = useState(false)
  const [search, setSearch] = useState('')
  const [error, setError] = useState('')
  const queryClient = useQueryClient()

  const { data: session, isLoading } = useQuery({
    queryKey: ['session', sessionId],
    queryFn: async () => {
      const response = await api.get(`/sessions/${sessionId}`)
      return response.data
    },
    enabled: !!sessionId,
  })

  const { data: users, isLoading: usersLoading } = useQuery({
    queryKey: ['users'],
    queryFn: async () => {
      const response = await api.get('/users/', { params: { limit: 1000 } })
      return response.data
    },
    enabled: showModal,
  })

  const onError = (err) => {
    setError(err.response?.data?.detail || 'Не удалось выполнить операцию')
  }

  const addMutation = useMutation({
    mutationFn: async (studentId) => {
      const response = await api.post(`/sessions/${sessionId}/students/${studentId}`)
      return response.data
    },
    onSuccess: () => {
      setError('')
      queryClient.invalidateQueries({ queryKey: ['session', sessionId] })
    },
    onError,
  })

  const removeMutation = useMutation({
    mutationFn: async (studentId) => {
      const response = await api.delete(`/sessions/${sessionId}/students/${studentId}`)
      return response.data
    },
    onSuccess: () => {
      setError('')
      queryClient.invalidateQueries({ queryKey: ['session', sessionId] })
    },
    onError,
  })

  const students = session?.students || []
  const memberIds = new Set(students.map((s) => s.id))
  const query = search.trim().toLowerCase()

  // В списке для добавления — только студенты, которых ещё нет в сессии
  const availableStudents = (users || [])
    .filter((u) => u.role === 'student' && u.is_active && !memberIds.has(u.id))
    .filter((u) =>
      !query ||
      u.full_name.toLowerCase().includes(query) ||
      u.username.toLowerCase().includes(query) ||
      u.email.toLowerCase().includes(query)
    )

  const handleRemove = (student) => {
    removeMutation.mutate(student.id)
  }

  const openModal = () => {
    setError('')
    setSearch('')
    setShowModal(true)
  }

  const isMutating = addMutation.isPending || removeMutation.isPending

  return (
    <div className="session-students">
      <div className="session-students-header">
        <h3>Студенты</h3>
        <span className="session-students-count">{students.length}</span>
      </div>

      {isLoading ? (
        <div className="session-students-empty">Загрузка...</div>
      ) : students.length === 0 ? (
        <div className="session-students-empty">В сессии пока нет студентов</div>
      ) : (
        <ul className="session-students-list">
          {students.map((student) => (
            <li key={student.id} className="session-student-item">
              <div className="session-student-info">
                <div className="session-student-name">{student.full_name}</div>
                <div className="session-student-meta">@{student.username}</div>
              </div>
              <button
                className="session-student-remove"
                onClick={() => handleRemove(student)}
                disabled={isMutating}
                title="Удалить из сессии"
              >
                ✕
              </button>
            </li>
          ))}
        </ul>
      )}

      {error && !showModal && <div className="session-students-error">{error}</div>}

      <button className="add-student-btn" onClick={openModal}>
        + Добавить студента
      </button>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content add-student-modal" onClick={(e) => e.stopPropagation()}>
            <h3>Добавить студента в сессию</h3>

            <input
              type="text"
              className="add-student-search"
              placeholder="Поиск по имени, логину или email"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              autoFocus
            />

            {error && <div className="session-students-error">{error}</div>}

            <div className="add-student-list">
              {usersLoading ? (
                <div className="session-students-empty">Загрузка...</div>
              ) : availableStudents.length === 0 ? (
                <div className="session-students-empty">
                  {query ? 'Никого не найдено' : 'Нет студентов для добавления'}
                </div>
              ) : (
                availableStudents.map((student) => (
                  <div key={student.id} className="add-student-item">
                    <div className="session-student-info">
                      <div className="session-student-name">{student.full_name}</div>
                      <div className="session-student-meta">
                        @{student.username} · {student.email}
                      </div>
                    </div>
                    <button
                      className="add-student-item-btn"
                      onClick={() => addMutation.mutate(student.id)}
                      disabled={isMutating}
                    >
                      Добавить
                    </button>
                  </div>
                ))
              )}
            </div>

            <div className="modal-actions">
              <button type="button" onClick={() => setShowModal(false)} className="cancel-btn">
                Готово
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default SessionStudents
