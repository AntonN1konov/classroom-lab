import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../services/api'
import { useAuthStore } from '../store/authStore'
import './StudentContextWindows.css'

function StudentContextWindows({ sessionId }) {
  const { user } = useAuthStore()
  const queryClient = useQueryClient()

  const { data: session } = useQuery({
    queryKey: ['session', sessionId],
    queryFn: async () => {
      const response = await api.get(`/sessions/${sessionId}`)
      return response.data
    },
  })

  const { data: pendingMessages } = useQuery({
    queryKey: ['pending-messages', sessionId],
    queryFn: async () => {
      const response = await api.get(`/chats/messages/${sessionId}?chat_type=yandexgpt`)
      return response.data.filter((msg) => msg.status === 'pending')
    },
    refetchInterval: 2000,
  })

  const approveMutation = useMutation({
    mutationFn: async (messageId) => {
      const response = await api.post(`/yandexgpt/approve/${messageId}`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['pending-messages', sessionId])
      queryClient.invalidateQueries(['messages', sessionId, 'yandexgpt'])
    },
  })

  const rejectMutation = useMutation({
    mutationFn: async (messageId) => {
      const response = await api.patch(`/chats/messages/${messageId}/status?status=rejected`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['pending-messages', sessionId])
    },
  })

  if (!session) {
    return <div className="loading">Загрузка...</div>
  }

  return (
    <div className="student-context-windows">
      <div className="context-windows-header">
        <h3>КО студентов (Уровень 2)</h3>
      </div>
      <div className="context-windows-content">
        {pendingMessages && pendingMessages.length > 0 ? (
          <div className="pending-messages-list">
            {pendingMessages.map((msg) => (
              <div key={msg.id} className="pending-message-card">
                <div className="message-info">
                  <div className="student-name">{msg.author_name}</div>
                  <div className="message-text">{msg.content}</div>
                </div>
                <div className="message-actions">
                  <button
                    onClick={() => approveMutation.mutate(msg.id)}
                    disabled={approveMutation.isPending}
                    className="approve-btn"
                  >
                    Отправить в YandexGPT
                  </button>
                  <button
                    onClick={() => rejectMutation.mutate(msg.id)}
                    disabled={rejectMutation.isPending}
                    className="reject-btn"
                  >
                    Отклонить
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="no-pending-messages">
            Нет сообщений, ожидающих одобрения
          </div>
        )}
      </div>
    </div>
  )
}

export default StudentContextWindows

