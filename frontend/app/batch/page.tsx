'use client';

import { useState } from 'react';
import { Layers, Play, Loader2 } from 'lucide-react';

export default function BatchPage() {
  const [text, setText] = useState('');
  const [type, setType] = useState<'video' | 'audio'>('video');
  const [quality, setQuality] = useState('best');
  const [format, setFormat] = useState('mp4');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleSubmit = async () => {
    const urls = text
      .split('\n')
      .map((l) => l.trim())
      .filter(Boolean);
    if (!urls.length) return;

    setLoading(true);
    setResult(null);
    try {
      const res = await fetch('/api/batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          urls,
          type,
          quality: type === 'video' ? quality : undefined,
          format: type === 'audio' ? format : 'mp4',
          bitrate: type === 'audio' ? '192' : undefined,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.message || data?.detail?.message || 'Batch failed');
      setResult(data);
    } catch (err: any) {
      alert(err.message || 'Batch failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 md:p-10 max-w-3xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold flex items-center gap-2">
        <Layers className="h-6 w-6" /> Batch Download
      </h1>
      <p className="text-[hsl(var(--muted-foreground))] text-sm">
        Paste multiple URLs (one per line). Max 30 URLs per batch.
      </p>

      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={10}
        placeholder={'https://www.youtube.com/watch?v=...\nhttps://www.tiktok.com/@user/video/...\nhttps://vimeo.com/...'}
        className="w-full rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-4 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-brand-500/40"
      />

      <div className="flex flex-wrap gap-4 items-center">
        <select
          value={type}
          onChange={(e) => setType(e.target.value as any)}
          className="h-10 rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--background))] px-3 text-sm"
        >
          <option value="video">Video</option>
          <option value="audio">Audio only</option>
        </select>

        {type === 'video' ? (
          <select
            value={quality}
            onChange={(e) => setQuality(e.target.value)}
            className="h-10 rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--background))] px-3 text-sm"
          >
            <option value="best">Best</option>
            <option value="good">Good (≤1080p)</option>
            <option value="normal">Normal (≤720p)</option>
            <option value="low">Low (≤480p)</option>
            <option value="1080">1080p</option>
            <option value="720">720p</option>
            <option value="480">480p</option>
          </select>
        ) : (
          <select
            value={format}
            onChange={(e) => setFormat(e.target.value)}
            className="h-10 rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--background))] px-3 text-sm"
          >
            <option value="mp3">MP3</option>
            <option value="m4a">M4A</option>
            <option value="wav">WAV</option>
            <option value="flac">FLAC</option>
          </select>
        )}

        <button
          onClick={handleSubmit}
          disabled={loading || !text.trim()}
          className="ml-auto inline-flex items-center gap-2 px-5 h-10 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-medium disabled:opacity-50"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
          Start Batch
        </button>
      </div>

      {result && (
        <div className="rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-4 text-sm space-y-2">
          <p>
            <strong>{result.queued}</strong> jobs queued
            {result.errors?.length > 0 && (
              <span className="text-red-500 ml-2">({result.errors.length} failed validation)</span>
            )}
          </p>
          <p className="text-[hsl(var(--muted-foreground))]">
            Go to <a href="/downloads" className="text-brand-500 underline">Downloads</a> to monitor progress.
          </p>
        </div>
      )}
    </div>
  );
}