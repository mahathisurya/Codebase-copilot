'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Loader2 } from 'lucide-react'
import { useAppStore } from '@/lib/store'
import { ChatMessage } from './ChatMessage'
import { api } from '@/lib/api'

export function ChatPanel() {
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const selectedRepo = useAppStore((s: any) => s.selectedRepo)

  // ✅ messages are per-repo; always fall back to []
  const messages = useAppStore((s: any) =>
    selectedRepo ? s.messagesByRepo?.[selectedRepo] ?? [] : []
  )

  const addMessage = useAppStore((s: any) => s.addMessage)
  const setCitationsForRepo = useAppStore((s: any) => s.setCitationsForRepo)
  const setConfidenceForRepo = useAppStore((s: any) => s.setConfidenceForRepo)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || !selectedRepo || loading) return

    const userMessage = { role: 'user' as const, content: input }

    // ✅ store the user message for this repo
    addMessage(selectedRepo, userMessage)

    setInput('')
    setLoading(true)

    try {
      const response = await api.chat({
        repo_id: selectedRepo,
        messages: [...messages, userMessage],
        top_k: 8,
        model: 'openai',
      })

      const assistantMessage = {
        role: 'assistant' as const,
        content: response.answer_markdown,
      }

      addMessage(selectedRepo, assistantMessage)
      setCitationsForRepo(selectedRepo, response.citations ?? [])
      setConfidenceForRepo(selectedRepo, response.confidence ?? null)
    } catch (error: any) {
      const errorMessage = {
        role: 'assistant' as const,
        content: `Error: ${error.response?.data?.detail || 'Failed to get response'}`,
      }
      addMessage(selectedRepo, errorMessage)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex-1 flex flex-col">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <h3 className="text-xl font-semibold mb-2">
                Ask me anything about this codebase
              </h3>
              <p className="text-muted-foreground">
                I&apos;ll provide answers with precise file and line citations
              </p>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message: { role: 'user' | 'assistant'; content: string }, index: number) => (
              <ChatMessage key={index} message={message} />
            ))}
            {loading && (
              <div className="flex items-center gap-2 text-muted-foreground">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Thinking...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-border p-4">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about the code..."
            disabled={loading}
            className="flex-1 px-4 py-2 border border-input rounded-md bg-background disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  )
}
