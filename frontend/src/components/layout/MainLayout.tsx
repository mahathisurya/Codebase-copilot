'use client'

import { useState } from 'react'
import { Sidebar } from './Sidebar'
import { ChatPanel } from '../chat/ChatPanel'
import { CitationsPanel } from '../citations/CitationsPanel'
import { useAppStore } from '@/lib/store'

export function MainLayout() {
  const [showCitations, setShowCitations] = useState(true)
  const selectedRepo = useAppStore((state) => state.selectedRepo)

  return (
    <div className="flex h-screen bg-background">
      {/* Left Sidebar */}
      <Sidebar />

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {!selectedRepo ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <h2 className="text-2xl font-bold mb-2">Welcome to Codebase Copilot</h2>
              <p className="text-muted-foreground">
                Add a repository to start asking questions
              </p>
            </div>
          </div>
        ) : (
          <ChatPanel />
        )}
      </div>

      {/* Right Citations Panel */}
      {showCitations && selectedRepo && (
        <CitationsPanel onClose={() => setShowCitations(false)} />
      )}
    </div>
  )
}