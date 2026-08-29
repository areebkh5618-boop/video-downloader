'use client';

import { useEffect, useState } from 'react';
import { Download, RefreshCw, XCircle, CheckCircle2, Loader2, Trash2, FolderOpen } from 'lucide-react';
import { api, type JobInfo } from '@/lib/api';
import { cn, formatBytes } from '@/lib/utils';

interface LocalFile {
  filename: string;
  size: number;
  download_url: string;
}

export default function DownloadsPage() {
  const [jobs, setJobs] = useState<JobInfo[]>([]);
  const [files, setFiles] = useState<LocalFile[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      const [j, f] = await Promise.all([
        api.listJobs(50).catch(() => []),
        fetch('/api/files').then((r) => r.json()).then((d) => d.items || []).catch(() => []),
      ]);
      setJobs(j);
      setFiles(f);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const t = setInterval(load, 3000);
    return () => clearInterval(t);
  }, []);

  const sections = {
    active: jobs.filter((j) => ['waiting', 'downloading', 'processing', 'merging', 'analyzing'].includes(j.status)),
    completed: jobs.filter((j) => j.status === 'completed'),
    failed: jobs.filter((j) => j.status === 'failed' || j.status === 'cancelled'),
  };

  return (
    <div className="p-6 md:p-10 max-w-5xl mx-auto space-y-10">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Download className="h-6 w-6" /> Downloads
        </h1>
        <button onClick={load} className="p-2 rounded-lg hover:bg-[hsl(var(--muted))]">
          <RefreshCw className={cn('h-4 w-4', loading && 'animate-spin')} />
        </button>
      </div>

      <p className="text-sm text-[hsl(var(--muted-foreground))]">
        Files are also saved in the <code className="px-1 rounded bg-[hsl(var(--muted))]">downloads</code> folder next to the project.
        Click <strong>Download to PC</strong> — browser will ask where to save.
      </p>

      {/* Local files on disk */}
      <section>
        <h2 className="text-sm font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))] mb-3 flex items-center gap-2">
          <FolderOpen className="h-4 w-4" /> Saved on disk ({files.length})
        </h2>
        {files.length === 0 ? (
          <p className="text-sm text-[hsl(var(--muted-foreground))] py-2">No files yet</p>
        ) : (
          <div className="space-y-2">
            {files.map((f) => (
              <div key={f.filename} className="rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-3 flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <div className="text-sm font-medium truncate">{f.filename}</div>
                  <div className="text-xs text-[hsl(var(--muted-foreground))]">{formatBytes(f.size)}</div>
                </div>
                <a
                  href={f.download_url}
                  download={f.filename}
                  className="shrink-0 px-3 h-8 rounded-lg bg-emerald-600 text-white text-xs font-medium flex items-center gap-1 hover:bg-emerald-500"
                >
                  <Download className="h-3.5 w-3.5" /> Download to PC
                </a>
              </div>
            ))}
          </div>
        )}
      </section>

      {(['active', 'completed', 'failed'] as const).map((key) => (
        <section key={key}>
          <h2 className="text-sm font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))] mb-3">
            {key === 'active' ? 'Downloading / Queued' : key.charAt(0).toUpperCase() + key.slice(1)}
            <span className="ml-2 opacity-60">({sections[key].length})</span>
          </h2>

          {sections[key].length === 0 ? (
            <p className="text-sm text-[hsl(var(--muted-foreground))] py-2">No items</p>
          ) : (
            <div className="space-y-3">
              {sections[key].map((job) => (
                <div
                  key={job.job_id}
                  className="rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-4 flex gap-4 items-start"
                >
                  <div className={cn(
                    'mt-1 h-9 w-9 rounded-full flex items-center justify-center shrink-0',
                    job.status === 'completed' && 'bg-emerald-500/15 text-emerald-500',
                    (job.status === 'failed' || job.status === 'cancelled') && 'bg-red-500/15 text-red-500',
                    !['completed', 'failed', 'cancelled'].includes(job.status) && 'bg-brand-500/15 text-brand-500'
                  )}>
                    {job.status === 'completed' && <CheckCircle2 className="h-4 w-4" />}
                    {(job.status === 'failed' || job.status === 'cancelled') && <XCircle className="h-4 w-4" />}
                    {!['completed', 'failed', 'cancelled'].includes(job.status) && <Loader2 className="h-4 w-4 animate-spin" />}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate">{job.title || job.url}</div>
                    <div className="text-xs text-[hsl(var(--muted-foreground))] mt-0.5 flex flex-wrap gap-x-3">
                      <span className="capitalize">{job.status}</span>
                      {job.quality && <span>{job.quality}</span>}
                      {job.format && <span>{job.format}</span>}
                    </div>
                    {!['completed', 'failed', 'cancelled'].includes(job.status) && (
                      <div className="mt-2 h-1.5 rounded-full bg-[hsl(var(--muted))] overflow-hidden">
                        <div className="h-full bg-brand-500 rounded-full transition-all" style={{ width: `${job.progress}%` }} />
                      </div>
                    )}
                    {job.error && <p className="mt-1 text-xs text-red-500">{job.error}</p>}
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    {job.status === 'completed' && (job.download_url || job.filename) && (
                      <a
                        href={job.download_url || (job.filename ? `/api/files/${encodeURIComponent(job.filename)}` : '#')}
                        download={job.filename || true}
                        className="px-3 h-8 rounded-lg bg-emerald-600 text-white text-xs font-medium flex items-center gap-1 hover:bg-emerald-500"
                      >
                        <Download className="h-3.5 w-3.5" /> Download to PC
                      </a>
                    )}
                    {!['completed', 'failed', 'cancelled'].includes(job.status) && (
                      <button
                        onClick={async () => {
                          await fetch(`/api/jobs/${job.job_id}`, { method: 'DELETE' });
                          load();
                        }}
                        className="p-1.5 rounded-lg hover:bg-red-500/10 text-[hsl(var(--muted-foreground))] hover:text-red-500"
                        title="Cancel"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      ))}
    </div>
  );
}
