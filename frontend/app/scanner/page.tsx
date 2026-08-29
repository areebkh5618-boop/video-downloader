'use client';

import { useState, useRef } from 'react';
import { ScanLine, Loader2, Download, Camera, Upload, Plus, X } from 'lucide-react';

export default function ScannerPage() {
  const [pages, setPages] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>([]);
  const [mode, setMode] = useState<'document' | 'bw' | 'color'>('document');
  const [autoCrop, setAutoCrop] = useState(true);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ filename: string; size: number; download_url: string; pages: number } | null>(null);
  const camRef = useRef<HTMLInputElement>(null);

  const addFiles = (list: FileList | null) => {
    if (!list) return;
    const imgs = Array.from(list).filter((f) => f.type.startsWith('image/'));
    setPages((p) => [...p, ...imgs].slice(0, 30));
    setPreviews((prev) => [...prev, ...imgs.map((f) => URL.createObjectURL(f))].slice(0, 30));
    setResult(null);
  };

  const removePage = (i: number) => {
    setPages((p) => p.filter((_, idx) => idx !== i));
    setPreviews((p) => {
      URL.revokeObjectURL(p[i]);
      return p.filter((_, idx) => idx !== i);
    });
  };

  const scan = async () => {
    if (!pages.length) return;
    setLoading(true);
    setResult(null);
    try {
      const fd = new FormData();
      pages.forEach((f) => fd.append('files', f));
      fd.append('mode', mode);
      fd.append('auto_crop', String(autoCrop));
      fd.append('export', 'pdf');
      const res = await fetch('/api/scanner/scan', { method: 'POST', body: fd });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail?.message || 'Scan failed');
      setResult(data);
    } catch (e: any) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 md:p-10 max-w-3xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold flex items-center gap-2">
        <ScanLine className="h-6 w-6" /> Document Scanner
      </h1>
      <p className="text-sm text-[hsl(var(--muted-foreground))]">
        CamScanner-style: capture or upload pages → auto edge crop → enhance → multi-page PDF.
        Browser will ask where to save the result.
      </p>

      <div className="flex flex-wrap gap-2">
        <label className="inline-flex items-center gap-2 px-4 h-10 rounded-xl bg-brand-600 text-white text-sm font-medium cursor-pointer">
          <Upload className="h-4 w-4" /> Upload photos
          <input type="file" accept="image/*" multiple className="hidden" onChange={(e) => addFiles(e.target.files)} />
        </label>
        <button
          type="button"
          onClick={() => camRef.current?.click()}
          className="inline-flex items-center gap-2 px-4 h-10 rounded-xl bg-[hsl(var(--muted))] text-sm font-medium"
        >
          <Camera className="h-4 w-4" /> Camera
        </button>
        <input
          ref={camRef}
          type="file"
          accept="image/*"
          capture="environment"
          className="hidden"
          onChange={(e) => addFiles(e.target.files)}
        />
      </div>

      {previews.length > 0 && (
        <div className="grid grid-cols-3 sm:grid-cols-4 gap-3">
          {previews.map((src, i) => (
            <div key={i} className="relative aspect-[3/4] rounded-xl overflow-hidden border border-[hsl(var(--border))] card-3d">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={src} alt={`page ${i + 1}`} className="w-full h-full object-cover" />
              <button
                onClick={() => removePage(i)}
                className="absolute top-1 right-1 p-1 rounded-full bg-black/70 text-white"
              >
                <X className="h-3.5 w-3.5" />
              </button>
              <span className="absolute bottom-1 left-1 text-[10px] px-1.5 py-0.5 rounded bg-black/70 text-white">
                {i + 1}
              </span>
            </div>
          ))}
          <label className="aspect-[3/4] rounded-xl border-2 border-dashed border-[hsl(var(--border))] flex items-center justify-center cursor-pointer hover:bg-[hsl(var(--muted))]/40">
            <Plus className="h-6 w-6 text-[hsl(var(--muted-foreground))]" />
            <input type="file" accept="image/*" multiple className="hidden" onChange={(e) => addFiles(e.target.files)} />
          </label>
        </div>
      )}

      <div className="card-3d p-5 space-y-4">
        <div className="flex flex-wrap gap-2">
          {(['document', 'bw', 'color'] as const).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`px-3 h-9 rounded-lg text-sm capitalize ${
                mode === m ? 'bg-brand-600 text-white' : 'bg-[hsl(var(--muted))]'
              }`}
            >
              {m === 'bw' ? 'B&W' : m}
            </button>
          ))}
        </div>
        <label className="flex items-center gap-2 text-sm cursor-pointer">
          <input type="checkbox" checked={autoCrop} onChange={(e) => setAutoCrop(e.target.checked)} />
          Auto-detect document edges (perspective crop)
        </label>
        <button
          onClick={scan}
          disabled={!pages.length || loading}
          className="inline-flex items-center gap-2 px-5 h-11 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-medium disabled:opacity-50"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <ScanLine className="h-4 w-4" />}
          Scan to PDF ({pages.length} page{pages.length !== 1 ? 's' : ''})
        </button>
      </div>

      {result && (
        <div className="card-3d p-4 flex items-center justify-between gap-4">
          <div className="text-sm">
            <div className="font-medium">{result.filename}</div>
            <div className="text-[hsl(var(--muted-foreground))]">
              {result.pages} pages · {(result.size / 1024).toFixed(1)} KB
            </div>
          </div>
          <a
            href={result.download_url}
            download={result.filename}
            className="inline-flex items-center gap-2 px-4 h-10 rounded-xl bg-emerald-600 text-white text-sm font-medium"
          >
            <Download className="h-4 w-4" /> Download to PC
          </a>
        </div>
      )}
    </div>
  );
}
