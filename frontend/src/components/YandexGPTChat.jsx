import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../services/api'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'
import './YandexGPTChat.css'

function YandexGPTChat({ sessionId, readOnly = false }) {
  const [message, setMessage] = useState('')
  const messagesEndRef = useRef(null)
  const queryClient = useQueryClient()

  const { data: messages, isLoading } = useQuery({
    queryKey: ['messages', sessionId, 'yandexgpt'],
    queryFn: async () => {
      const response = await api.get(`/chats/messages/${sessionId}?chat_type=yandexgpt`)
      return response.data
    },
    refetchInterval: 2000,
  })

  const { data: llmStatus } = useQuery({
    queryKey: ['llm-status'],
    queryFn: async () => (await api.get('/setup/status')).data,
    refetchInterval: 30000,
  })

  const sendMutation = useMutation({
    mutationFn: async (prompt) => {
      const response = await api.post('/yandexgpt/send', {
        prompt,
        session_id: sessionId,
      })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['messages', sessionId, 'yandexgpt'])
      setMessage('')
    },
  })

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (message.trim() && !readOnly) {
      sendMutation.mutate(message.trim())
    }
  }

  return (
    <div className="yandexgpt-chat">
      <div className="chat-header">
        <h3>КО YandexGPT (Уровень 1)</h3>
        {llmStatus && (
          <span className={`llm-badge ${llmStatus.provider === 'demo' ? 'demo' : ''}`}>{llmStatus.label}</span>
        )}
      </div>
      <div className="chat-messages">
        {isLoading ? (
          <div className="loading">Загрузка сообщений...</div>
        ) : messages && messages.length > 0 ? (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`message ${msg.is_from_yandexgpt ? 'yandexgpt-message' : 'user-message'}`}
            >
              <div className="message-header">
                <span className="message-author">
                  {msg.is_from_yandexgpt ? 'ИИ' : msg.author_name}
                </span>
                <span className="message-time">
                  {format(new Date(msg.created_at), 'HH:mm', { locale: ru })}
                </span>
              </div>
              <div className="message-content">
                {msg.is_from_yandexgpt ? msg.yandexgpt_response : msg.content}
              </div>
            </div>
          ))
        ) : (
          <div className="empty-messages">
            Здравствуйте! Я YandexGPT. Чем могу помочь?
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      {sendMutation.isError && (
        <div className="chat-error">
          {sendMutation.error?.response?.data?.detail || 'Не удалось отправить запрос'}
        </div>
      )}
      {!readOnly && (
        <form className="chat-input-form" onSubmit={handleSubmit}>
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Введите запрос для YandexGPT..."
            disabled={sendMutation.isPending}
            className="chat-input"
          />
          <button
            type="submit"
            disabled={!message.trim() || sendMutation.isPending}
            className="chat-send-btn"
          >
            {sendMutation.isPending ? 'Отправка...' : 'Отправить'}
          </button>
        </form>
      )}
    </div>
  )
}

export default YandexGPTChat

