"""
Asynchronous TTS API endpoints for job creation, status polling, and audio retrieval.
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from uuid import UUID, uuid4
from app.tts_queue import enqueue_tts_job, get_tts_job_status, get_tts_audio_path
from app.config import get_settings
import os

router = APIRouter(prefix="/tts", tags=["tts"])

class TTSJobRequest(BaseModel):
    text: str
    voice: str = "google"  # or "coqui" in the future
    output_format: str = "mp3"
    voice_pitch: float = 0.0
    voice_speed: float = 1.0

class TTSJobResponse(BaseModel):
    job_id: UUID
    status: str

@router.post("/jobs", response_model=TTSJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_tts_job(request: TTSJobRequest):
    if not request.text:
        raise HTTPException(status_code=400, detail="Text is required.")
    job_id = uuid4()
    enqueue_tts_job(
        job_id,
        request.text,
        request.voice,
        request.output_format,
        request.voice_pitch,
        request.voice_speed
    )
    return TTSJobResponse(job_id=job_id, status="queued")

@router.get("/jobs/{job_id}", response_model=TTSJobResponse)
async def get_job_status(job_id: UUID):
    status_str = get_tts_job_status(job_id)
    if not status_str:
        raise HTTPException(status_code=404, detail="Job not found.")
    return TTSJobResponse(job_id=job_id, status=status_str)

@router.get("/audio/{job_id}")
async def get_audio(job_id: UUID):
    audio_path = get_tts_audio_path(job_id)
    if not audio_path or not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio not ready.")
    return FileResponse(audio_path, media_type="audio/mpeg")
