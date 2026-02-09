'use client'

import { useEffect } from 'react'
import { Plus, FolderGit2, Loader2 } from 'lucide-react'
import { useAppStore } from '@/lib/store'
import { AddRepoDialog } from '../repo/AddRepoDialog'
import { cn } from '@/lib/utils'

export function Sidebar() {
  const {
    repos,
    selectedRepo,
    showAddRepo,
    setSelectedRepo,
    setShowAddRepo,
    fetchRepos,
  } = useAppStore()

  useEffect(() => {
    fetchRepos()
    const interval = setInterval(fetchRepos, 5000) // Poll for status updates
    return () => clearInterval(interval)
  }, [fetchRepos])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready':
        return 'bg-green-500'
      case 'indexing':
        return 'bg-yellow-500'
      case 'error':
        return 'bg-red-500'
      default:
        return 'bg-gray-500'
    }
  }

  return (
    <>
      <div className="w-64 border-r border-border bg-card flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-border">
          <h1 className="text-lg font-bold">Codebase Copilot</h1>
        </div>

        {/* Add Repo Button */}
        <div className="p-4">
          <button
            onClick={() => setShowAddRepo(true)}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Repository
          </button>
        </div>

        {/* Repositories List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {repos.length === 0 ? (
            <div className="text-center text-sm text-muted-foreground py-8">
              No repositories yet
            </div>
          ) : (
            repos.map((repo) => (
              <button
                key={repo.repo_id}
                onClick={() => setSelectedRepo(repo.repo_id)}
                className={cn(
                  'w-full text-left p-3 rounded-md transition-colors',
                  selectedRepo === repo.repo_id
                    ? 'bg-accent text-accent-foreground'
                    : 'hover:bg-accent/50'
                )}
              >
                <div className="flex items-start gap-2">
                  <FolderGit2 className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate">{repo.display_name}</div>
                    <div className="flex items-center gap-2 mt-1">
                      <div className={cn('w-2 h-2 rounded-full', getStatusColor(repo.status))} />
                      <span className="text-xs text-muted-foreground capitalize">
                        {repo.status}
                      </span>
                      {repo.status === 'indexing' && (
                        <Loader2 className="w-3 h-3 animate-spin" />
                      )}
                    </div>
                    {repo.chunk_count > 0 && (
                      <div className="text-xs text-muted-foreground mt-1">
                        {repo.chunk_count} chunks
                      </div>
                    )}
                  </div>
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      <AddRepoDialog open={showAddRepo} onOpenChange={setShowAddRepo} />
    </>
  )
}