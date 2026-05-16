import { useState, useRef, useEffect } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''
const PROVIDERS = ['groq', 'gemini', 'local']

export default function ChatBox() {
  const [messages, setMessages] = useState([
    { role: 'assistant', text: 'Hello! How can I help you today?' },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [selectedProvider, setSelectedProvider] = useState('groq')
  const [models, setModels] = useState([])
  const [selectedModel, setSelectedModel] = useState('')
  const [modelsLoading, setModelsLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    setModels([])
    setSelectedModel('')
    setModelsLoading(true)
    fetch(`${API_BASE}/api/chat/models?provider=${selectedProvider}`)
      .then((res) => res.json())
      .then((data) => {
        if (data.models && data.models.length > 0) {
          setModels(data.models)
          setSelectedModel(data.models[0].id)
        }
      })
      .catch(() => {})
      .finally(() => setModelsLoading(false))
  }, [selectedProvider])

  async function sendMessage(e) {
    e.preventDefault()
    const text = input.trim()
    if (!text || loading) return

    setMessages((prev) => [...prev, { role: 'user', text }])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch(`${API_BASE}/api/chat/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          provider: selectedProvider,
          model: selectedModel || undefined,
        }),
      })
      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.detail || 'Unknown error')
      }
      setMessages((prev) => [...prev, { role: 'assistant', text: data.reply }])
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: `Error: ${err.message || 'Something went wrong. Please try again.'}` },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <section id="chat">
      <div className="chat-header">
        <h2>Chat</h2>
        <div className="chat-header-right">
          <div className="chat-selectors">
          <div className="model-selector">
            <label htmlFor="provider-select">Provider:</label>
            <select
              id="provider-select"
              value={selectedProvider}
              onChange={(e) => setSelectedProvider(e.target.value)}
              disabled={loading}
            >
              {PROVIDERS.map((p) => (
                <option key={p} value={p}>
                  {p.charAt(0).toUpperCase() + p.slice(1)}
                </option>
              ))}
            </select>
          </div>
          <div className="model-selector">
            <label htmlFor="model-select">Model:</label>
            <select
              id="model-select"
              value={selectedModel}
              onChange={(e) => {
                setSelectedModel(e.target.value)
              }}
              disabled={loading || modelsLoading || models.length === 0}
            >
              {modelsLoading && <option value="">Loading…</option>}
              {!modelsLoading && models.length === 0 && <option value="">No models available</option>}
              {models.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.display_name}
                </option>
              ))}
            </select>
          </div>
        </div>
        </div>
      </div>
      <div className="chat-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`chat-bubble ${msg.role}`}>
            {msg.text}
          </div>
        ))}
        {loading && (
          <div className="chat-bubble assistant chat-typing">
            <span></span><span></span><span></span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <form className="chat-input-row" onSubmit={sendMessage}>
        <input
          type="text"
          className="chat-input"
          placeholder="Type a message…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
          aria-label="Chat message"
        />
        <button type="submit" className="chat-send" disabled={loading || !input.trim()}>
          Send
        </button>
      </form>
    </section>
  )
}
