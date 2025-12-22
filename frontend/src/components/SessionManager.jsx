import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../services/api'
import './SessionManager.css'

function SessionManager() {
  const [showModal, setShowModal] = useState(false)
  const [sessionName, setSessionName] = useState('')
  const [sessionDescription, setSessionDescription] = useState('')
  const queryClient = useQueryClient()

  const createMutation = useMutation({
    mutationFn: async (data) => {
      const response = await api.post('/sessions/', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['sessions'])
      setShowModal(false)
      setSessionName('')
      setSessionDescription('')
    },
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    createMutation.mutate({
      name: sessionName,
      description: sessionDescription,
    })
  }

  return (
    <>
      <button onClick={() => setShowModal(true)} className="create-session-btn">
        Создать сессию
      </button>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Создать новую сессию</h3>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Название сессии</label>
                <input
                  type="text"
                  value={sessionName}
                  onChange={(e) => setSessionName(e.target.value)}
                  required
                  disabled={createMutation.isPending}
                />
              </div>
              <div className="form-group">
                <label>Описание</label>
                <textarea
                  value={sessionDescription}
                  onChange={(e) => setSessionDescription(e.target.value)}
                  rows="3"
                  disabled={createMutation.isPending}
                />
              </div>
              <div className="modal-actions">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="cancel-btn"
                >
                  Отмена
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="submit-btn"
                >
                  {createMutation.isPending ? 'Создание...' : 'Создать'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  )
}

export default SessionManager

