# AreebFetch – All-in-One Studio

Video/audio downloader + image tools + PDF tools + CamScanner-style document scanner.

## Stack
- Frontend: Next.js 14, TypeScript, Tailwind (OLED / 3D theme)
- Backend: FastAPI, yt-dlp **2026.8.19**, FFmpeg, Pillow, OpenCV, pypdf
- Docker Compose

## Features
- Universal video/audio download (4K, batch, playlist detect)
- Real-time progress (WebSocket)
- Image compress & resize
- PDF merge / split / compress
- Document scanner (auto edge crop → enhanced multi-page PDF)
- File manager + downloads folder bind-mount
- History, settings, clipboard paste

## Quick start
```bash
docker compose down
docker compose up -d --build
```
- App: http://localhost:3000  
- Files on PC: `./downloads/`

## Env (docker-compose)
- ENVIRONMENT=production
- DEBUG=false
- ALLOWED_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
- RATE_LIMIT=30/minute
- MAX_CONCURRENT_DOWNLOADS=3

## API map
| Area | Endpoints |
|------|-----------|
| Media | POST /api/analyze, /api/download, /api/batch, /api/playlist |
| Jobs | GET /api/jobs, /api/jobs/{id}, DELETE /api/jobs/{id} |
| Files | GET /api/files, GET /api/files/{name}, DELETE /api/files/{name} |
| Images | POST /api/images/process |
| PDF | POST /api/pdf/merge, /api/pdf/split, /api/pdf/compress |
| Scanner | POST /api/scanner/scan |
| History | GET/DELETE /api/history |
| Settings | GET/PUT /api/settings |
| Progress | WS /api/ws/{id}, SSE /api/sse/{id} |

Personal use only. No DRM bypass.
