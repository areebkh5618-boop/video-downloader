'use client';

import { History, Trash2, ExternalLink, X } from 'lucide-react';
import { useAppStore } from '@/lib/store';
import { cn } from '@/lib/utils';

export function HistoryPanel({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { history, clearHistory, removeFromHistory } = useAppStore();

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-md bg-[hsl(var(--card))] border-l border-[hsl(var(--border))] shadow-2xl animate-slide-up flex flex-col">
        <div className="flex items-center justify-between p-4 border-b border-[hsl(var(--border))]">
          <div className="flex items-center gap-2 font-semibold">
            <History className="h-5 w-5" />
            Download History
          </div>
          <div className="flex items-center gap-2">
            {history.length > 0 && (
              <button
                onClick={clearHistory}
                className="text-xs text-[hsl(var(--muted-foreground))] hover:text-red-500 flex items-center gap-1"
              >
                <Trash2 className="h-3.5 w-3.5" />
                Clear
              </button>
            )}
            <button onClick={onClose} className="p-1 rounded-lg hover:bg-[hsl(var(--muted))]">
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {history.length === 0 ? (
            <p className="text-center text-sm text-[hsl(var(--muted-foreground))] py-12">
              No downloads yet
            </p>
          ) : (
            history.map((item) => (
              <div
                key={item.id}
                className="group flex items-start gap-3 p-3 rounded-xl border border-[hsl(var(--border))] hover:bg-[hsl(var(--muted))]/50 transition-colors"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{item.title}</p>
                  <p className="text-xs text-[hsl(var(--muted-foreground))] truncate mt-0.5">
                    {item.filename || item.url}
                  </p>
                  <p className="text-[10px] text-[hsl(var(--muted-foreground))] mt-1">
                    {new Date(item.created_at).toLocaleString()}
                  </p>
                </div>
                <button
                  onClick={() => removeFromHistory(item.id)}
                  className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-500/10 text-[hsl(var(--muted-foreground))] hover:text-red-500 transition-all"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}