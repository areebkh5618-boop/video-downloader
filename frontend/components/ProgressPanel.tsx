'use client';

import { useEffect, useRef, useState } from 'react';
import { CheckCircle2, XCircle, Loader2, Download } from 'lucide-react';
import type { JobInfo } from '@/lib/api';
import { createProgressSocket, api } from '@/lib/api';
import { cn, formatBytes } from '@/lib/utils';
import { useAppStore } from '@/lib/store';

interface Props {
  job: JobInfo;
  onComplete?: (job: JobInfo) => void;
}

export function ProgressPanel({ job: initialJob, onComplete }: Props) {
  const { setActiveJob, addToHistory } = useAppStore();
  const [job, setJob] = useState<JobInfo>(initialJob);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    setJob(initialJob);
  }, [initialJob.job_id]);

  useEffect(() => {
    if (!job || ['completed', 'failed', 'cancelled'].includes(job.status)) return;

    const ws = createProgressSocket(
      job.job_id,
      (data) => {
        const updated = { ...job, ...data } as JobInfo;
        setJob(updated);
        setActiveJob(updated);

        if (['completed', 'failed', 'cancelled'].includes(data.status)) {
          if (data.status === 'completed') {
            addToHistory({
              id: job.job_id,
              title: job.title || data.filename || 'Download',
              url: job.url,
              filename: data.filename,
              status: 'completed',
              created_at: job.created_at,
            });
            onComplete?.(updated);
          }
          ws.close();
        }
      },
      () => {
        // fallback polling
        const interval = setInterval(async () => {
          try {
            const fresh = await api.getJob(job.job_id);
            setJob(fresh);
            setActiveJob(fresh);
            if (['completed', 'failed', 'cancelled'].includes(fresh.status)) {
              clearInterval(interval);
            }
          } catch {}
        }, 2000);
        return () => clearInterval(interval);
      }
    );
    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, [job?.job_id]);

  if (!job) return null;

  const isDone = job.status === 'completed';
  const isFailed = job.status === 'failed';
  const isActive = !isDone && !isFailed;

  return (
    <div className="w-full max-w-2xl mx-auto animate-slide-up">
      <div className="rounded-2xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-5 shadow-lg">
        <div className="flex items-start gap-4">
          <div
            className={cn(
              'mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-full',
              isDone && 'bg-emerald-500/15 text-emerald-500',
              isFailed && 'bg-red-500/15 text-red-500',
              isActive && 'bg-brand-500/15 text-brand-500'
            )}
          >
            {isDone && <CheckCircle2 className="h-5 w-5" />}
            {isFailed && <XCircle className="h-5 w-5" />}
            {isActive && <Loader2 className="h-5 w-5 animate-spin" />}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-2">
              <h3 className="font-medium truncate">
                {job.title || 'Preparing download…'}
              </h3>
              <span className="text-sm tabular-nums text-[hsl(var(--muted-foreground))]">
                {Math.round(job.progress)}%
              </span>
            </div>

            {/* Progress bar */}
            <div className="mt-3 h-2 rounded-full bg-[hsl(var(--muted))] overflow-hidden">
              <div
                className={cn(
                  'h-full rounded-full transition-all duration-300',
                  isDone && 'bg-emerald-500',
                  isFailed && 'bg-red-500',
                  isActive && 'bg-brand-500',
                  isActive && job.progress === 0 && 'progress-indeterminate w-1/3'
                )}
                style={
                  isActive && job.progress > 0
                    ? { width: `${job.progress}%` }
                    : isDone || isFailed
                    ? { width: '100%' }
                    : undefined
                }
              />
            </div>

            <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-[hsl(var(--muted-foreground))]">
              <span className="capitalize">{job.status.replace('_', ' ')}</span>
              {job.speed && <span>{job.speed}</span>}
              {job.eta && <span>ETA {job.eta}</span>}
              {job.downloaded_bytes != null && (
                <span>
                  {formatBytes(job.downloaded_bytes)}
                  {job.total_bytes
                    ? ` / ${formatBytes(job.total_bytes)}`
                    : ''}
                </span>
              )}
            </div>

            {job.error && (
              <p className="mt-2 text-sm text-red-500">{job.error}</p>
            )}

            {isDone && job.download_url && (
              <a
                href={job.download_url}
                download={job.filename || true}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-4 inline-flex items-center gap-2 px-4 h-10 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium transition-colors"
              >
                <Download className="h-4 w-4" />
                Download to PC
                {job.filename && (
                  <span className="opacity-80 text-xs ml-1 truncate max-w-[180px]">
                    {job.filename}
                  </span>
                )}
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}