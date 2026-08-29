"""
Phase 8: Real-time progress via WebSocket + SSE
"""
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from app.core.exceptions import JobNotFoundError, to_http_exception
from app.models.schemas import ProgressUpdate, JobStatus
from app.services.job_manager import job_manager

router = APIRouter()


@router.websocket("/ws/{job_id}")
async def ws_progress(websocket: WebSocket, job_id: str):
    await websocket.accept()
    job = await job_manager.get_job(job_id)
    if not job:
        await websocket.send_json({"error": "job_not_found"})
        await websocket.close()
        return

    queue: asyncio.Queue = asyncio.Queue()

    def on_update(update: ProgressUpdate):
        try:
            queue.put_nowait(update.model_dump(mode="json"))
        except Exception:
            pass

    job.subscribe(on_update)
    await websocket.send_json(job.to_info().model_dump(mode="json"))

    try:
        while True:
            try:
                data = await asyncio.wait_for(queue.get(), timeout=25.0)
                await websocket.send_json(data)
                if data.get("status") in ("completed", "failed", "cancelled"):
                    break
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        pass
    finally:
        job.unsubscribe(on_update)


@router.get("/sse/{job_id}")
async def sse_progress(job_id: str):
    job = await job_manager.get_job(job_id)
    if not job:
        raise to_http_exception(JobNotFoundError(job_id))

    async def generator():
        queue: asyncio.Queue = asyncio.Queue()

        def on_update(update: ProgressUpdate):
            try:
                queue.put_nowait(update)
            except Exception:
                pass

        job.subscribe(on_update)
        yield f"data: {job.to_info().model_dump_json()}\n\n"
        try:
            while True:
                try:
                    update = await asyncio.wait_for(queue.get(), timeout=20.0)
                    yield f"data: {update.model_dump_json()}\n\n"
                    if update.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
                        break
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            job.unsubscribe(on_update)

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )