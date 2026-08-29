const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api';

export interface FormatInfo {
  format_id: string;
  ext: string;
  resolution?: string;
  height?: number;
  fps?: number;
  vcodec?: string;
  acodec?: string;
  filesize?: number;
  filesize_approx?: number;
  tbr?: number;
  format_note?: string;
  quality_label?: string;
  quality?: string;
}

export interface MediaInfo {
  id: string;
  title: string;
  thumbnail?: string;
  duration?: number;
  duration_string?: string;
  uploader?: string;
  uploader_url?: string;
  webpage_url: string;
  extractor: string;
  description?: string;
  view_count?: number;
  like_count?: number;
  upload_date?: string;
  formats: FormatInfo[];
  available_heights?: number[];
  has_audio?: boolean;
  has_video?: boolean;
  best_video?: FormatInfo;
  best_audio?: FormatInfo;
}

export interface JobInfo {
  job_id: string;
  status: string;
  created_at: string;
  updated_at: string;
  url: string;
  title?: string;
  thumbnail?: string;
  type?: string;
  quality?: string;
  format?: string;
  progress: number;
  download_url?: string;
  filename?: string;
  error?: string;
  expires_at?: string;
  speed?: string;
  eta?: string;
  downloaded_bytes?: number;
  total_bytes?: number;
  message?: string;
}

export interface ProgressUpdate {
  job_id: string;
  status: string;
  progress: number;
  speed?: string;
  eta?: string;
  downloaded_bytes?: number;
  total_bytes?: number;
  message?: string;
  filename?: string;
  error?: string;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const msg =
      body?.message ||
      body?.detail?.message ||
      (typeof body?.detail === 'string' ? body.detail : null) ||
      `Request failed (${res.status})`;
    throw new Error(msg);
  }
  return res.json();
}

export const api = {
  analyze: (url: string) =>
    request<{ success: boolean; data: MediaInfo }>('/analyze', {
      method: 'POST',
      body: JSON.stringify({ url }),
    }),

  startDownload: (payload: {
    url: string;
    format_id?: string;
    audio_only?: boolean;
    audio_format?: string;
    video_quality?: string;
  }) =>
    request<JobInfo>('/download', {
      method: 'POST',
      body: JSON.stringify({
        url: payload.url,
        type: payload.audio_only ? 'audio' : 'video',
        quality: payload.video_quality || 'best',
        format: payload.audio_only ? (payload.audio_format || 'mp3') : 'mp4',
        format_id: payload.format_id || null,
      }),
    }),

  getJob: (jobId: string) => request<JobInfo>(`/jobs/${jobId}`),

  listJobs: (limit = 20) => request<JobInfo[]>(`/jobs?limit=${limit}`),

  health: () => request<Record<string, unknown>>('/health'),
};

export function createProgressSocket(
  jobId: string,
  onUpdate: (data: ProgressUpdate | JobInfo) => void,
  onError?: (err: Event) => void
): WebSocket {
  const protocol =
    typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'wss' : 'ws';
  const host =
    process.env.NEXT_PUBLIC_WS_HOST ||
    (typeof window !== 'undefined' ? window.location.host : 'localhost:8000');
  const ws = new WebSocket(`${protocol}://${host}/api/ws/${jobId}`);

  ws.onmessage = (ev) => {
    try {
      const data = JSON.parse(ev.data);
      if (data.type === 'ping') return;
      onUpdate(data);
    } catch {
      /* ignore */
    }
  };
  ws.onerror = onError || (() => {});
  return ws;
}
