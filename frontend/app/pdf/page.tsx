'use client';

import { useState } from 'react';
import { FileText, Loader2, Download, Merge, Scissors, Minimize2 } from 'lucide-react';

type Result = { filename: string; size: number; download_url: string };

export default function PdfPage() {
  const [tab, setTab] = useState<'merge' | 'split' | 'compress'>('merge');
  const [files, setFiles] = useState<FileList | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [ranges, setRanges] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<Result[]>([]);

  const run = async () => {
    setLoading(true);
    setResults([]);
    try {
      if (tab === 'merge') {
        if (!files?.length) throw new Error('Select PDFs to merge');
        const fd = new FormData();
        Array.from(files).forEach((f) => fd.append('files', f));
        const res = await fetch('/api/pdf/merge', { method: 'POST', body: fd });
        const data = await res.json();
        if (!res.ok) throw new Error(data?.detail?.message || 'Merge failed');
        setResults([data]);
      } else if (tab === 'split') {
        if (!file) throw new Error('Select a PDF');
        const fd = new FormData();
        fd.append('file', file);
        if (ranges.trim()) fd.append('ranges', ranges.trim());
        const res = await fetch('/api/pdf/split', { method: 'POST', body: fd });
        const data = await res.json();
        if (!res.ok) throw new Error(data?.detail?.message || 'Split failed');
        setResults(data.items || []);
      } else {
        if (!file) throw new Error('Select a PDF');
        const fd = new FormData();
        fd.append('file', file);
        const res = await fetch('/api/pdf/compress', { method: 'POST', body: fd });
        const data = await res.json();
        if (!res.ok) throw new Error(data?.detail?.message || 'Compress failed');
        setResults([data]);
      }
    } catch (e: any) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 md:p-10 max-w-3xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold flex items-center gap-2">
        <FileText className="h-6 w-6" /> PDF Tools
      </h1>

      <div className="flex gap-2 flex-wrap">
        {([
          ['merge', Merge, 'Merge'],
          ['split', Scissors, 'Split'],
          ['compress', Minimize2, 'Compress'],
        ] as const).map(([k, Icon, label]) => (
          <button
            key={k}
            onClick={() => { setTab(k); setResults([]); }}
            className={`flex items-center gap-2 px-4 h-10 rounded-xl text-sm font-medium transition-all ${
              tab === k ? 'bg-brand-600 text-white shadow-lg shadow-brand-600/20' : 'bg-[hsl(var(--muted))] text-[hsl(var(--muted-foreground))]'
            }`}
          >
            <Icon className="h-4 w-4" /> {label}
          </button>
        ))}
      </div>

      <div className="card-3d p-5 space-y-4">
        {tab === 'merge' ? (
          <label className="block text-sm">
            Select multiple PDFs
            <input type="file" accept="application/pdf" multiple className="mt-2 block w-full text-sm"
              onChange={(e) => setFiles(e.target.files)} />
          </label>
        ) : (
          <>
            <label className="block text-sm">
              Select PDF
              <input type="file" accept="application/pdf" className="mt-2 block w-full text-sm"
                onChange={(e) => setFile(e.target.files?.[0] || null)} />
            </label>
            {tab === 'split' && (
              <label className="block text-sm">
                Page ranges (optional, e.g. 1-3,5,8-10). Empty = each page separate.
                <input value={ranges} onChange={(e) => setRanges(e.target.value)}
                  className="mt-2 w-full h-10 rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--background))] px-3"
                  placeholder="1-3,5" />
              </label>
            )}
          </>
        )}

        <button onClick={run} disabled={loading}
          className="inline-flex items-center gap-2 px-5 h-11 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-medium disabled:opacity-50">
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
          Run
        </button>
      </div>

      {results.length > 0 && (
        <div className="space-y-2">
          {results.map((r) => (
            <div key={r.filename} className="card-3d p-4 flex items-center justify-between gap-3">
              <div className="text-sm min-w-0">
                <div className="font-medium truncate">{r.filename}</div>
                <div className="text-[hsl(var(--muted-foreground))]">{(r.size / 1024).toFixed(1)} KB</div>
              </div>
              <a href={r.download_url} download={r.filename}
                className="shrink-0 inline-flex items-center gap-1 px-3 h-9 rounded-lg bg-emerald-600 text-white text-xs font-medium">
                <Download className="h-3.5 w-3.5" /> Download to PC
              </a>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
