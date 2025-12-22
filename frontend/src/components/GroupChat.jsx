import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../services/api'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'
import './GroupChat.css'

function GroupChat({ sessionId }) {
  const [message, setMessage] = useState('')
  const messagesEndRef = useRef(null)
  const queryClient = useQueryClient()

  const { data: messages, isLoading } = useQuery({
    queryKey: ['messages', sessionId, 'group'],
    queryFn: async () => {
      const response = await api.get(`/chats/messages/${sessionId}?chat_type=group`)
      return response.data
    },
    refetchInterval: 2000,
  })

  const sendMutation = useMutation({
    mutationFn: async (content) => {
      const response = await api.post('/chats/messages', {
        content,
        session_id: sessionId,
        chat_type: 'group',
      })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['messages', sessionId, 'group'])
      setMessage('')
    },
  })

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (message.trim()) {
      sendMutation.mutate(message.trim())
    }
  }

  return (
    <div className="group-chat">
      <div className="chat-header">
        <h3>Групповой чат</h3>
      </div>
      <div className="chat-messages">
        {isLoading ? (
          <div className="loading">Загрузка сообщений...</div>
        ) : messages && messages.length > 0 ? (
          messages.map((msg) => (
            <div key={msg.id} className="message">
              <div className="message-header">
                <span className="message-author">{msg.author_name}</span>
                <span className="message-time">
                  {format(new Date(msg.created_at), 'HH:mm', { locale: ru })}
                </span>
              </div>
              <div className="message-content">{msg.content}</div>
            </div>
          ))
        ) : (
          <div className="empty-messages">Нет сообщений</div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <form className="chat-input-form" onSubmit={handleSubmit}>
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Введите сообщение..."
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
    </div>
  )
}

export default GroupChat

