'use client'

import { useEffect, useState } from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import { X, Copy, Check } from 'lucide-react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { useAppStore } from '@/lib/store'
import { api } from '@/lib/api'

interface CodeViewerDialogProps {
  citation: {
    file_path: string
    start_line: number
    end_line: number
  }
  onClose: () => void
}

export function CodeViewerDialog({ citation, onClose }: CodeViewerDialogProps) {
  const selectedRepo = useAppStore((state) => state.selectedRepo)

  const [content, setContent] = useState('')
  const [language, setLanguage] = useState('text')
  const [loading, setLoading] = useState(true)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    loadFileContent()
  }, [citation])

  const loadFileContent = async () => {
    if (!selectedRepo) return

    setLoading(true)
    try {
      const response = await api.getFileContent(
        selectedRepo,
        citation.file_path
      )
      setContent(response.content)
      setLanguage(response.language)
    } catch (error) {
      console.error('Failed to load file content:', error)
      setContent('// Failed to load file content')
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = async () => {
    const lines = content.split('\n')
    const snippet = lines
      .slice(citation.start_line - 1, citation.end_line)
      .join('\n')

    await navigator.clipboard.writeText(snippet)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const highlightLines =
    citation.start_line && citation.end_line
      ? Array.from(
          { length: citation.end_line - citation.start_line + 1 },
          (_, i) => citation.start_line + i
        )
      : []

  return (
    <Dialog.Root open={true} onOpenChange={onClose}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50" />

        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-card p-6 rounded-lg shadow-lg w-full max-w-4xl max-h-[80vh] border border-border flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div>
              <Dialog.Title className="text-lg font-bold">
                {citation.file_path}
              </Dialog.Title>
              <p className="text-sm text-muted-foreground">
                Lines {citation.start_line}-{citation.end_line}
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleCopy}
                className="p-2 hover:bg-accent rounded-md transition-colors"
                title="Copy cited lines"
              >
                {copied ? (
                  <Check className="w-4 h-4 text-green-500" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
              </button>

              <Dialog.Close className="p-2 hover:bg-accent rounded-md">
                <X className="w-4 h-4" />
              </Dialog.Close>
            </div>
          </div>

          <div className="flex-1 overflow-auto rounded-md border border-border">
            {loading ? (
              <div className="p-4 text-center text-muted-foreground">
                Loading...
              </div>
            ) : (
              <SyntaxHighlighter
                language={language}
                style={vscDarkPlus}
                showLineNumbers
                wrapLines
                lineProps={(lineNumber) => {
                  const isHighlighted =
                    highlightLines.includes(lineNumber)
                  return {
                    style: {
                      backgroundColor: isHighlighted
                        ? 'rgba(255, 255, 0, 0.1)'
                        : undefined,
                    },
                  }
                }}
              >
                {content}
              </SyntaxHighlighter>
            )}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
