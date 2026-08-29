'use client';

import { useEffect, useState } from 'react';
import { History, Search, Trash2, RefreshCw } from 'lucide-react';

interface HistoryItem {
  id: string;
  title: string;
  url: string;
  thumbnail?: string;
  format?: string;
  quality?: string;
  status: string;
  filename?: string;
  filesize?: number;
  type?: string;
  created_at: string;
}

export default function HistoryPage() {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  const load = async (q = search) => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ limit: '100' });
      if (q) params.set('search', q);
      const res = await fetch(`/api/history?${params}`);
      const data = await res.json();
      setItems(data.items || []);
    } catch {
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const clearAll = async () => {
    if (!confirm('Clear all history?')) return;
    await fetch('/api/history', { method: 'DELETE' });
    load();
  };

  const remove = async (id: string) => {
    await fetch(`/api/history/${id}`, { method: 'DELETE' });
    setItems((prev) => prev.filter((i) => i.id !== id));
  };

  return (
    <div className="p-6 md:p-10 max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <History className="h-6 w-6" /> History
        </h1>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[hsl(var(--muted-foreground))]" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && load()}
              placeholder="Search…"
              className="h-9 pl-9 pr-3 rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--background))] text-sm w-48"
            />
          </div>
          <button onClick={() => load()} className="p-2 rounded-lg hover:bg-[hsl(var(--muted))]">
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          {items.length > 0 && (
            <button onClick={clearAll} className="text-xs text-red-500 hover:underline flex items-center gap-1">
              <Trash2 className="h-3.5 w-3.5" /> Clear all
            </button>
          )}
        </div>
      </div>

      {items.length === 0 ? (
        <p className="text-center text-[hsl(var(--muted-foreground))] py-16">No download history yet</p>
      ) : (
        <div className="space-y-2">
          {items.map((item) => (
            <div
              key={item.id}
              className="group flex items-center gap-4 p-3 rounded-xl border border-[hsl(var(--border))] hover:bg-[hsl(var(--muted))]/40 transition-colors"
            >
              {item.thumbnail ? (
                <img src={item.thumbnail} alt="" className="h-12 w-20 object-cover rounded-lg shrink-0" />
              ) : (
                <div className="h-12 w-20 rounded-lg bg-[hsl(var(--muted))] shrink-0" />
              )}
              <div className="flex-1 min-w-0">
                <div className="font-medium text-sm truncate">{item.title}</div>
                <div className="text-xs text-[hsl(var(--muted-foreground))] mt-0.5 flex flex-wrap gap-x-3">
                  <span>{new Date(item.created_at).toLocaleString()}</span>
                  {item.format && <span>{item.format}</span>}
                  {item.quality && <span>{item.quality}</span>}
                  <span className="capitalize">{item.status}</span>
                </div>
              </div>
              <button
                onClick={() => remove(item.id)}
                className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg hover:bg-red-500/10 text-[hsl(var(--muted-foreground))] hover:text-red-500 transition-all"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}