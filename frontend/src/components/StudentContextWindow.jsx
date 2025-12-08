import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../services/api'
import { useAuthStore } from '../store/authStore'
import './StudentContextWindow.css'

function StudentContextWindow({ sessionId }) {
  const [prompt, setPrompt] = useState('')
  const { user } = useAuthStore()
  const queryClient = useQueryClient()

  const sendMutation = useMutation({
    mutationFn: async (content) => {
      const response = await api.post('/chats/messages', {
        content,
        session_id: sessionId,
        chat_type: 'yandexgpt',
      })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['messages', sessionId, 'yandexgpt'])
      setPrompt('')
    },
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    if (prompt.trim()) {
      sendMutation.mutate(prompt.trim())
    }
  }

  return (
    <div className="student-context-window">
      <div className="context-window-header">
        <h3>КО студентов (Уровень 2)</h3>
        <div className="student-name">{user?.full_name}</div>
      </div>
      <div className="context-window-content">
        <p className="instruction">
          Введите ваш вопрос здесь. Преподаватель проверит его и отправит в YandexGPT.
        </p>
        <form className="prompt-form" onSubmit={handleSubmit}>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Объясните простыми словами принцип квантовой запутанности?"
            disabled={sendMutation.isPending}
            className="prompt-input"
            rows="4"
          />
          <button
            type="submit"
            disabled={!prompt.trim() || sendMutation.isPending}
            className="submit-prompt-btn"
          >
            {sendMutation.isPending ? 'Отправка...' : 'Отправить на проверку'}
          </button>
        </form>
        <div className="status-info">
          <p>
            После отправки ваш вопрос будет проверен преподавателем. 
            После одобрения он будет отправлен в YandexGPT, и ответ появится в основном чате.
          </p>
        </div>
      </div>
    </div>
  )
}

export default StudentContextWindow

