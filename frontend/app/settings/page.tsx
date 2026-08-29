'use client';

import { useEffect, useState } from 'react';
import { Settings, Save, Loader2 } from 'lucide-react';

const DEFAULTS = {
  default_video_quality: 'best',
  default_video_format: 'mp4',
  default_audio_format: 'mp3',
  default_audio_bitrate: '192',
  max_concurrent_downloads: 3,
  save_thumbnails: false,
  embed_metadata: true,
  subtitle_preference: 'none',
  auto_start_download: false,
  theme: 'system',
};

export default function SettingsPage() {
  const [form, setForm] = useState(DEFAULTS);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    fetch('/api/settings')
      .then((r) => r.json())
      .then((d) => setForm({ ...DEFAULTS, ...d }))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const save = async () => {
    setSaving(true);
    setSaved(false);
    try {
      const res = await fetch('/api/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      const data = await res.json();
      setForm({ ...DEFAULTS, ...data });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {
      alert('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const set = (key: string, value: any) => setForm((f) => ({ ...f, [key]: value }));

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <Loader2 className="h-6 w-6 animate-spin text-brand-500" />
      </div>
    );
  }

  return (
    <div className="p-6 md:p-10 max-w-2xl mx-auto space-y-8">
      <h1 className="text-2xl font-bold flex items-center gap-2">
        <Settings className="h-6 w-6" /> Settings
      </h1>

      <section className="space-y-4">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))]">Video</h2>
        <div className="grid gap-3">
          <label className="flex flex-col gap-1 text-sm">
            Default quality
            <select
              value={form.default_video_quality}
              onChange={(e) => set('default_video_quality', e.target.value)}
              className="h-10 rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--background))] px-3"
            >
              <option value="best">Best</option>
              <option value="good">Good (≤1080p)</option>
              <option value="normal">Normal (≤720p)</option>
              <option value="low">Low (≤480p)</option>
              <option value="1080">1080p</option>
              <option value="720">720p</option>
            </select>
          </label>
          <label className="flex flex-col gap-1 text-sm">
            Default format
            <select
              value={form.default_video_format}
              onChange={(e) => set('default_video_format', e.target.value)}
              className="h-10 rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--background))] px-3"
            >
              <option value="mp4">MP4</option>
              <option value="mkv">MKV</option>
              <option value="webm">WebM</option>
            </select>
          </label>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))]">Audio</h2>
        <div className="grid gap-3">
          <label className="flex flex-col gap-1 text-sm">
            Default format
            <select
              value={form.default_audio_format}
              onChange={(e) => set('default_audio_format', e.target.value)}
              className="h-10 rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--background))] px-3"
            >
              <option value="mp3">MP3</option>
              <option value="m4a">M4A</option>
              <option value="wav">WAV</option>
              <option value="flac">FLAC</option>
            </select>
          </label>
          <label className="flex flex-col gap-1 text-sm">
            Default bitrate
            <select
              value={form.default_audio_bitrate}
              onChange={(e) => set('default_audio_bitrate', e.target.value)}
              className="h-10 rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--background))] px-3"
            >
              <option value="320">320 kbps</option>
              <option value="256">256 kbps</option>
              <option value="192">192 kbps</option>
              <option value="128">128 kbps</option>
            </select>
          </label>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))]">General</h2>
        <div className="grid gap-3">
          <label className="flex flex-col gap-1 text-sm">
            Max simultaneous downloads
            <input
              type="number"
              min={1}
              max={10}
              value={form.max_concurrent_downloads}
              onChange={(e) => set('max_concurrent_downloads', Number(e.target.value))}
              className="h-10 rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--background))] px-3 w-24"
            />
          </label>

          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={form.save_thumbnails}
              onChange={(e) => set('save_thumbnails', e.target.checked)}
              className="rounded"
            />
            Save thumbnails
          </label>
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={form.embed_metadata}
              onChange={(e) => set('embed_metadata', e.target.checked)}
              className="rounded"
            />
            Embed metadata
          </label>
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={form.auto_start_download}
              onChange={(e) => set('auto_start_download', e.target.checked)}
              className="rounded"
            />
            Auto-start download after selection
          </label>
        </div>
      </section>

      <button
        onClick={save}
        disabled={saving}
        className="inline-flex items-center gap-2 px-5 h-10 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-medium disabled:opacity-50"
      >
        {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
        {saved ? 'Saved!' : 'Save Settings'}
      </button>
    </div>
  );
}