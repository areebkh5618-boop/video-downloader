'use client';

import { useState } from 'react';
import { Search, Loader2, Link2, ClipboardPaste } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Props {
  onAnalyze: (url: string) => Promise<void>;
  loading?: boolean;
  disabled?: boolean;
}

export function UrlInput({ onAnalyze, loading, disabled }: Props) {
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');

  const pasteFromClipboard = async () => {
    try {
      const text = await navigator.clipboard.readText();
      const trimmed = (text || '').trim();
      if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
        setUrl(trimmed);
        setError('');
      } else if (trimmed) {
        setUrl(trimmed);
      }
    } catch {
      setError('Clipboard access denied — paste manually (Ctrl+V)');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    const trimmed = url.trim();
    if (!trimmed) {
      setError('Please paste a media URL');
      return;
    }
    try {
      new URL(trimmed);
    } catch {
      setError('Invalid URL');
      return;
    }
    try {
      await onAnalyze(trimmed);
    } catch (err: any) {
      setError(err.message || 'Analysis failed');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-3xl mx-auto">
      <div className="relative group card-3d !p-0 overflow-hidden">
        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
          <Link2 className="h-5 w-5 text-[hsl(var(--muted-foreground))]" />
        </div>
        <input
          type="url"
          value={url}
          onChange={(e) => {
            setUrl(e.target.value);
            setError('');
          }}
          placeholder="Paste video or media URL..."
          disabled={loading || disabled}
          className={cn(
            'w-full h-14 pl-12 pr-44 rounded-2xl border-0 bg-transparent',
            'text-[hsl(var(--foreground))] placeholder:text-[hsl(var(--muted-foreground))]',
            'focus:outline-none focus:ring-0'
          )}
        />
        <div className="absolute right-2 top-2 bottom-2 flex gap-1.5">
          <button
            type="button"
            onClick={pasteFromClipboard}
            disabled={loading || disabled}
            className="px-3 rounded-xl text-[hsl(var(--muted-foreground))] hover:bg-[hsl(var(--muted))] hover:text-[hsl(var(--foreground))] transition-colors"
            title="Paste from clipboard"
          >
            <ClipboardPaste className="h-4 w-4" />
          </button>
          <button
            type="submit"
            disabled={loading || disabled || !url.trim()}
            className={cn(
              'px-5 rounded-xl font-medium',
              'bg-brand-600 hover:bg-brand-500 text-white',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              'flex items-center gap-2 transition-colors shadow-lg shadow-brand-600/20'
            )}
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Analyzing
              </>
            ) : (
              <>
                <Search className="h-4 w-4" />
                Analyze
              </>
            )}
          </button>
        </div>
      </div>
      {error && (
        <p className="mt-2 text-sm text-red-500 animate-fade-in">{error}</p>
      )}
    </form>
  );
}
