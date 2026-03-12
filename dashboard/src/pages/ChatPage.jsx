import { useState, useEffect, useRef } from 'react'
import { Send, Bot, User, AlertTriangle, Trash2 } from 'lucide-react'
import { motion } from 'framer-motion'
import { sendChatMessage, fetchChatHistory } from '../api'

/**
 * ChatPage - local LLM chatbot with draft-only guardrails.
 * Falls back to template responses when Ollama is not running.
 */
export default function ChatPage() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [sessionId] = useState(() => `s_${Date.now()}`)
  const bottomRef = useRef(null)

  // Load history on mount
  useEffect(() => {
    fetchChatHistory(sessionId)
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setMessages(data.map((m) => ({
            role: m.role,
            content: m.content,
            timestamp: m.timestamp,
          })))
        }
      })
      .catch(() => {})
  }, [sessionId])

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async (e) => {
    e.preventDefault()
    const text = input.trim()
    if (!text) return

    const userMsg = { role: 'user', content: text, timestamp: new Date().toISOString() }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setSending(true)

    try {
      const res = await sendChatMessage(text, sessionId)
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: res.reply || res.response,
          timestamp: res.timestamp || new Date().toISOString(),
          draft_warning: res.draft_warning,
        },
      ])
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `Error: ${err.message || 'Failed to get response'}`,
          timestamp: new Date().toISOString(),
          isError: true,
        },
      ])
    }

    setSending(false)
  }

  const handleClear = () => {
    setMessages([])
  }

  return (
    <div className="flex flex-col h-[calc(100vh-7rem)]">
      {/* Header */}
      <div className="flex items-center justify-between pb-4">
        <div>
          <h1 className="text-2xl font-bold">Chat Assistant</h1>
          <p className="text-sm text-gray-500">Local LLM - Zero-Cloud - Draft-Only</p>
        </div>
        {messages.length > 0 && (
          <button
            onClick={handleClear}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg text-gray-500 hover:bg-gray-100 transition-colors"
          >
            <Trash2 size={14} /> Clear
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto rounded-xl border border-gray-200 bg-white shadow-sm p-4 space-y-3">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center text-gray-400">
            <Bot size={48} className="mb-3 opacity-50" />
            <p className="text-sm font-medium">No messages yet</p>
            <p className="text-xs mt-1 max-w-sm">
              Ask me about your data, drafts, clients, or how to use Autify Engine.
              I can help with analysis, but all actions require your explicit approval.
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.role !== 'user' && (
              <div className="w-8 h-8 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center flex-shrink-0">
                <Bot size={16} />
              </div>
            )}

            <div
              className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm ${
                msg.role === 'user'
                  ? 'bg-brand-600 text-white'
                  : msg.isError
                    ? 'bg-red-50 text-red-700 border border-red-200'
                    : 'bg-gray-100 text-gray-800'
              }`}
            >
              {msg.draft_warning && (
                <div className="flex items-center gap-1.5 text-amber-600 text-xs font-medium mb-1.5">
                  <AlertTriangle size={12} />
                  Draft-Only: Action requires your manual approval
                </div>
              )}
              <p className="whitespace-pre-wrap">{msg.content}</p>
              <p className="text-[10px] mt-1 opacity-50">
                {msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString() : ''}
              </p>
            </div>

            {msg.role === 'user' && (
              <div className="w-8 h-8 rounded-full bg-gray-200 text-gray-600 flex items-center justify-center flex-shrink-0">
                <User size={16} />
              </div>
            )}
          </motion.div>
        ))}

        {sending && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center">
              <Bot size={16} />
            </div>
            <div className="bg-gray-100 rounded-2xl px-4 py-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0ms]" />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:150ms]" />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:300ms]" />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSend} className="flex gap-2 pt-3">
        <input
          type="text"
          className="flex-1 border border-gray-300 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-brand-500 outline-none"
          placeholder="Type a message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={sending}
          autoFocus
        />
        <button
          type="submit"
          disabled={sending || !input.trim()}
          className="px-4 py-2.5 rounded-xl bg-brand-600 text-white hover:bg-brand-700 transition-colors disabled:opacity-50"
        >
          <Send size={18} />
        </button>
      </form>
    </div>
  )
}
