'use client';

import { useState } from 'react';
import { Image as ImageIcon, Upload, Loader2, Download } from 'lucide-react';

export default function ImagesPage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [width, setWidth] = useState('');
  const [height, setHeight] = useState('');
  const [quality, setQuality] = useState(85);
  const [format, setFormat] = useState('JPEG');
  const [keepAspect, setKeepAspect] = useState(true);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ filename: string; size: number; download_url: string } | null>(null);

  const onFile = (f: File | null) => {
    setFile(f);
    setResult(null);
    if (preview) URL.revokeObjectURL(preview);
    setPreview(f ? URL.createObjectURL(f) : null);
  };

  const process = async () => {
    if (!file) return;
    setLoading(true);
    setResult(null);
    try {
      const fd = new FormData();
      fd.append('file', file);
      if (width) fd.append('width', width);
      if (height) fd.append('height', height);
      fd.append('quality', String(quality));
      fd.append('format', format);
      fd.append('keep_aspect', String(keepAspect));
      const res = await fetch('/api/images/process', { method: 'POST', body: fd });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail?.message || data?.message || 'Failed');
      setResult(data);
    } catch (e: any) {
      alert(e.message || 'Processing failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 md:p-10 max-w-3xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold flex items-center gap-2">
        <ImageIcon className="h-6 w-6" /> Image Compress & Resize
      </h1>
      <p className="text-sm text-[hsl(var(--muted-foreground))]">
        Upload an image, set size / quality / format, then download the result. Browser will ask where to save.
      </p>

      <label className="flex flex-col items-center justify-center gap-3 border-2 border-dashed border-[hsl(var(--border))] rounded-2xl p-10 cursor-pointer hover:bg-[hsl(var(--muted))]/40 transition-colors">
        <Upload className="h-8 w-8 text-[hsl(var(--muted-foreground))]" />
        <span className="text-sm">{file ? file.name : 'Click to choose image (JPG, PNG, WEBP…)'}</span>
        <input
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) => onFile(e.target.files?.[0] || null)}
        />
      </label>

      {preview && (
        <div className="rounded-xl overflow-hidden border border-[hsl(var(--border))] max-h-64 flex justify-center bg-[hsl(var(--muted))]">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={preview} alt="preview" className="max-h-64 object-contain" />
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <label className="text-sm flex flex-col gap-1">
          Width (px)
          <input type="number" min={1} value={width} onChange={(e) => setWidth(e.target.value)}
            placeholder="auto" className="h-10 rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--background))] px-3" />
        </label>
        <label className="text-sm flex flex-col gap-1">
          Height (px)
          <input type="number" min={1} value={height} onChange={(e) => setHeight(e.target.value)}
            placeholder="auto" className="h-10 rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--background))] px-3" />
        </label>
        <label className="text-sm flex flex-col gap-1">
          Quality ({quality})
          <input type="range" min={10} max={100} value={quality} onChange={(e) => setQuality(Number(e.target.value))} />
        </label>
        <label className="text-sm flex flex-col gap-1">
          Format
          <select value={format} onChange={(e) => setFormat(e.target.value)}
            className="h-10 rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--background))] px-3">
            <option value="JPEG">JPEG</option>
            <option value="PNG">PNG</option>
            <option value="WEBP">WebP</option>
          </select>
        </label>
      </div>

      <label className="flex items-center gap-2 text-sm cursor-pointer">
        <input type="checkbox" checked={keepAspect} onChange={(e) => setKeepAspect(e.target.checked)} />
        Keep aspect ratio
      </label>

      <button
        onClick={process}
        disabled={!file || loading}
        className="inline-flex items-center gap-2 px-5 h-11 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-medium disabled:opacity-50"
      >
        {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <ImageIcon className="h-4 w-4" />}
        Process Image
      </button>

      {result && (
        <div className="rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-4 flex items-center justify-between gap-4">
          <div className="text-sm">
            <div className="font-medium">{result.filename}</div>
            <div className="text-[hsl(var(--muted-foreground))]">{(result.size / 1024).toFixed(1)} KB</div>
          </div>
          <a
            href={result.download_url}
            download={result.filename}
            className="inline-flex items-center gap-2 px-4 h-10 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium"
          >
            <Download className="h-4 w-4" /> Download to PC
          </a>
        </div>
      )}
    </div>
  );
}
