'use client';

import { useState } from 'react';
import { UrlInput } from '@/components/UrlInput';
import { MediaCard } from '@/components/MediaCard';
import { ProgressPanel } from '@/components/ProgressPanel';
import { api, type MediaInfo, type JobInfo } from '@/lib/api';
import { useAppStore } from '@/lib/store';

export default function HomePage() {
  const [media, setMedia] = useState<MediaInfo | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [job, setJob] = useState<JobInfo | null>(null);
  const [downloading, setDownloading] = useState(false);
  const { setCurrentMedia, setActiveJob } = useAppStore();

  const handleAnalyze = async (url: string) => {
    setAnalyzing(true);
    setMedia(null);
    setJob(null);
    try {
      const res = await api.analyze(url);
      setMedia(res.data);
      setCurrentMedia(res.data);
    } catch (err: any) {
      alert(err.message || 'Analysis failed');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleDownload = async (opts: {
    format_id?: string;
    audio_only?: boolean;
    audio_format?: string;
    video_quality?: string;
  }) => {
    if (!media) return;
    setDownloading(true);
    try {
      const payload: any = {
        url: media.webpage_url,
        type: opts.audio_only ? 'audio' : 'video',
        quality: opts.video_quality || 'best',
        format: opts.audio_only ? (opts.audio_format || 'mp3') : 'mp4',
      };
      if (opts.format_id) payload.format_id = opts.format_id;

      const newJob = await api.startDownload(payload);
      setJob(newJob);
      setActiveJob(newJob);
    } catch (err: any) {
      alert(err.message || 'Failed to start download');
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="flex flex-col items-center px-4 py-10 md:py-16 gap-10 max-w-5xl mx-auto">
      {!media && !job && (
        <div className="text-center max-w-xl animate-fade-in">
          <h1 className="text-3xl md:text-4xl font-bold tracking-tight">
            Download any video or audio
          </h1>
          <p className="mt-3 text-[hsl(var(--muted-foreground))] text-lg">
            Paste a link from YouTube, TikTok, Instagram, X, Vimeo and 1000+ sites.
          </p>
        </div>
      )}

      <UrlInput
        onAnalyze={handleAnalyze}
        loading={analyzing}
        disabled={!!job && !['completed', 'failed', 'cancelled'].includes(job.status)}
      />

      {media && !job && (
        <MediaCard media={media} onDownload={handleDownload} downloading={downloading} />
      )}

      {job && <ProgressPanel job={job} />}
    </div>
  );
}