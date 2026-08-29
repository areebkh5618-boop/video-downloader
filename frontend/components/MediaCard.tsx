'use client';

import { Clock, Eye, User, Globe, Download, Music, Video } from 'lucide-react';
import type { MediaInfo, FormatInfo } from '@/lib/api';
import { formatBytes, formatDuration, cn } from '@/lib/utils';
import { useState } from 'react';

interface Props {
  media: MediaInfo;
  onDownload: (opts: {
    format_id?: string;
    audio_only?: boolean;
    audio_format?: string;
    video_quality?: string;
  }) => void;
  downloading?: boolean;
}

export function MediaCard({ media, onDownload, downloading }: Props) {
  const [selectedFormat, setSelectedFormat] = useState<string>('best');
  const [audioOnly, setAudioOnly] = useState(false);
  const [audioFmt, setAudioFmt] = useState('mp3');

  const videoFormats = media.formats.filter(
    (f) => f.vcodec && f.vcodec !== 'none'
  );
  const audioFormats = media.formats.filter(
    (f) => f.acodec && f.acodec !== 'none' && (!f.vcodec || f.vcodec === 'none')
  );

  const handleDownload = () => {
    if (audioOnly) {
      onDownload({ audio_only: true, audio_format: audioFmt });
    } else if (selectedFormat === 'best') {
      onDownload({ video_quality: 'best' });
    } else if (['2160','1440','1080','720','480','360','good','normal','low'].includes(selectedFormat)) {
      onDownload({ video_quality: selectedFormat });
    } else {
      onDownload({ format_id: selectedFormat });
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto animate-slide-up">
      <div className="rounded-2xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] overflow-hidden shadow-lg">
        <div className="flex flex-col md:flex-row">
          {/* Thumbnail */}
          <div className="relative w-full md:w-80 aspect-video bg-[hsl(var(--muted))] shrink-0">
            {media.thumbnail ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={media.thumbnail}
                alt={media.title}
                className="absolute inset-0 w-full h-full object-cover"
              />
            ) : (
              <div className="absolute inset-0 flex items-center justify-center text-[hsl(var(--muted-foreground))]">
                <Video className="h-12 w-12 opacity-40" />
              </div>
            )}
            {media.duration_string && (
              <span className="absolute bottom-2 right-2 px-2 py-0.5 rounded bg-black/80 text-white text-xs font-medium">
                {media.duration_string}
              </span>
            )}
          </div>

          {/* Info */}
          <div className="flex-1 p-5 md:p-6 flex flex-col gap-3">
            <div>
              <h2 className="text-lg md:text-xl font-semibold leading-snug line-clamp-2">
                {media.title}
              </h2>
              <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm text-[hsl(var(--muted-foreground))]">
                {media.uploader && (
                  <span className="inline-flex items-center gap-1">
                    <User className="h-3.5 w-3.5" />
                    {media.uploader}
                  </span>
                )}
                {media.extractor && (
                  <span className="inline-flex items-center gap-1 capitalize">
                    <Globe className="h-3.5 w-3.5" />
                    {media.extractor}
                  </span>
                )}
                {media.view_count != null && (
                  <span className="inline-flex items-center gap-1">
                    <Eye className="h-3.5 w-3.5" />
                    {media.view_count.toLocaleString()}
                  </span>
                )}
                {media.duration != null && (
                  <span className="inline-flex items-center gap-1">
                    <Clock className="h-3.5 w-3.5" />
                    {formatDuration(media.duration)}
                  </span>
                )}
              </div>
            </div>

            {/* Mode toggle */}
            <div className="flex gap-2 mt-1">
              <button
                onClick={() => setAudioOnly(false)}
                className={cn(
                  'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
                  !audioOnly
                    ? 'bg-brand-600 text-white'
                    : 'bg-[hsl(var(--muted))] text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]'
                )}
              >
                <Video className="h-4 w-4" />
                Video
              </button>
              <button
                onClick={() => setAudioOnly(true)}
                className={cn(
                  'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
                  audioOnly
                    ? 'bg-brand-600 text-white'
                    : 'bg-[hsl(var(--muted))] text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]'
                )}
              >
                <Music className="h-4 w-4" />
                Audio only
              </button>
            </div>

            {/* Format selection */}
            <div className="mt-1">
              {audioOnly ? (
                <select
                  value={audioFmt}
                  onChange={(e) => setAudioFmt(e.target.value)}
                  className="w-full md:w-56 h-10 rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--background))] px-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/40"
                >
                  <option value="mp3">MP3 (192 kbps)</option>
                  <option value="m4a">M4A / AAC</option>
                  <option value="opus">Opus</option>
                  <option value="wav">WAV (lossless)</option>
                </select>
              ) : (
                <select
                  value={selectedFormat}
                  onChange={(e) => setSelectedFormat(e.target.value)}
                  className="w-full md:w-72 h-10 rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--background))] px-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/40"
                >
                  <option value="best">Best available (incl. 4K)</option>
                  <option value="2160">4K / 2160p</option>
                  <option value="1440">1440p</option>
                  <option value="1080">1080p</option>
                  <option value="720">720p</option>
                  <option value="480">480p</option>
                  <option value="360">360p</option>
                  <option value="good">Good (≤1080p)</option>
                  <option value="normal">Normal (≤720p)</option>
                  <option value="low">Low (≤480p)</option>
                  {videoFormats.slice(0, 15).map((f) => (
                    <option key={f.format_id} value={f.format_id}>
                      {f.quality_label || f.quality || f.resolution || f.format_id} • {f.ext.toUpperCase()}
                      {f.filesize || f.filesize_approx
                        ? ` • ${formatBytes(f.filesize || f.filesize_approx)}`
                        : ''}
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* Download button */}
            <div className="mt-auto pt-2">
              <button
                onClick={handleDownload}
                disabled={downloading}
                className={cn(
                  'inline-flex items-center gap-2 px-6 h-11 rounded-xl font-medium',
                  'bg-brand-600 hover:bg-brand-500 text-white shadow-md',
                  'disabled:opacity-60 disabled:cursor-not-allowed transition-all'
                )}
              >
                <Download className="h-4 w-4" />
                {downloading ? 'Starting…' : 'Download'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}