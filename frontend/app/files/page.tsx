'use client';

import { useEffect, useState } from 'react';
import { FolderOpen, Download, Trash2, RefreshCw } from 'lucide-react';
import { formatBytes } from '@/lib/utils';

interface LocalFile {
  filename: string;
  size: number;
  download_url: string;
}

export default function FilesPage() {
  const [files, setFiles] = useState<LocalFile[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/files');
      const data = await res.json();
      setFiles(data.items || []);
    } catch {
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const remove = async (name: string) => {
    if (!confirm(`Delete ${name}?`)) return;
    await fetch(`/api/files/${encodeURIComponent(name)}`, { method: 'DELETE' });
    setFiles((f) => f.filter((x) => x.filename !== name));
  };

  return (
    <div className="p-6 md:p-10 max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <FolderOpen className="h-6 w-6" /> File Manager
        </h1>
        <button onClick={load} className="p-2 rounded-lg hover:bg-[hsl(var(--muted))]">
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>
      <p className="text-sm text-[hsl(var(--muted-foreground))]">
        Files stored in project <code className="px-1 rounded bg-[hsl(var(--muted))]">downloads/</code> folder.
        Download triggers browser Save As dialog.
      </p>

      {files.length === 0 ? (
        <p className="text-center text-[hsl(var(--muted-foreground))] py-16">No files yet</p>
      ) : (
        <div className="space-y-2">
          {files.map((f) => (
            <div key={f.filename} className="card-3d p-3 flex items-center gap-3">
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium truncate">{f.filename}</div>
                <div className="text-xs text-[hsl(var(--muted-foreground))]">{formatBytes(f.size)}</div>
              </div>
              <a
                href={f.download_url}
                download={f.filename}
                className="px-3 h-8 rounded-lg bg-emerald-600 text-white text-xs font-medium inline-flex items-center gap-1"
              >
                <Download className="h-3.5 w-3.5" /> Download
              </a>
              <button onClick={() => remove(f.filename)} className="p-1.5 rounded-lg hover:bg-red-500/10 text-[hsl(var(--muted-foreground))] hover:text-red-500">
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
