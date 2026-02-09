'use client'

import { X, FileCode, ExternalLink } from 'lucide-react'
import { useAppStore } from '@/lib/store'
import { CodeViewerDialog } from './CodeViewerDialog'
import { useState } from 'react'

export function CitationsPanel({ onClose }: { onClose: () => void }) {
  const selectedRepo = useAppStore((state) => state.selectedRepo)
  const citations = useAppStore((state) => 
    selectedRepo ? state.citationsByRepo?.[selectedRepo] ?? [] : []
  )
  const currentConfidence = useAppStore((state) => 
    selectedRepo ? state.confidenceByRepo?.[selectedRepo] : null
  )
  const [selectedCitation, setSelectedCitation] = useState<any>(null)

  const getConfidenceColor = (confidence: string) => {
    switch (confidence) {
      case 'high':
        return 'text-green-600'
      case 'medium':
        return 'text-yellow-600'
      case 'low':
        return 'text-red-600'
      default:
        return 'text-muted-foreground'
    }
  }

  return (
    <>
      <div className="w-96 border-l border-border bg-card flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-border flex items-center justify-between">
          <h2 className="font-semibold">Sources & Citations</h2>
          <button onClick={onClose} className="p-1 hover:bg-accent rounded-md">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Confidence */}
        {currentConfidence && (
          <div className="p-4 border-b border-border text-sm">
            <span className="text-muted-foreground">Confidence: </span>
            <span className={`font-medium capitalize ${getConfidenceColor(currentConfidence)}`}>
              {currentConfidence}
            </span>
          </div>
        )}

        {/* Citations */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {citations.length === 0 ? (
            <div className="text-center text-sm text-muted-foreground py-8">
              No citations yet. Ask a question to see sources.
            </div>
          ) : (
            citations.map((citation, index) => (
              <button
                key={index}
                onClick={() => setSelectedCitation(citation)}
                className="w-full text-left p-3 border rounded-md hover:bg-accent"
              >
                <div className="flex gap-2">
                  <FileCode className="w-4 h-4 mt-1 text-primary" />
                  <div className="flex-1">
                    <div className="text-sm font-medium truncate">
                      {citation.file_path}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Lines {citation.start_line}-{citation.end_line}
                    </div>
                  </div>
                  <ExternalLink className="w-3 h-3 opacity-60" />
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      {selectedCitation && (
        <CodeViewerDialog
          citation={selectedCitation}
          onClose={() => setSelectedCitation(null)}
        />
      )}
    </>
  )
}
