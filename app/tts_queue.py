"""
TTS job queue management for RabbitMQ. Handles enqueueing jobs, status, and audio path retrieval.
"""
import os
import json
import pika
from uuid import UUID
from pathlib import Path
from app.config import get_settings

# In-memory job status for demo (replace with Redis/DB for prod)
TTS_JOB_STATUS = {}
TTS_AUDIO_PATH = {}

settings = get_settings()
AUDIO_DIR = Path("static/audio")

# RabbitMQ connection helper
def get_rmq_conn():
    params = pika.URLParameters(settings.RABBITMQ_URL)
    return pika.BlockingConnection(params)

def enqueue_tts_job(job_id, text, voice, output_format, voice_pitch=0.0, voice_speed=1.0):
    """
    Enqueue a TTS job with detailed control parameters.
    """
    TTS_JOB_STATUS[str(job_id)] = "queued"
    conn = get_rmq_conn()
    channel = conn.channel()
    channel.queue_declare(queue="gdial.tts", durable=True)
    job_data = {
        "job_id": str(job_id),
        "text": text,
        "voice": voice,
        "output_format": output_format,
        "voice_pitch": voice_pitch,
        "voice_speed": voice_speed
    }
    channel.basic_publish(
        exchange="",
        routing_key="gdial.tts",
        body=json.dumps(job_data),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    conn.close()

def set_tts_job_status(job_id, status, audio_path=None):
    TTS_JOB_STATUS[str(job_id)] = status
    if audio_path:
        TTS_AUDIO_PATH[str(job_id)] = str(audio_path)

def get_tts_job_status(job_id):
    return TTS_JOB_STATUS.get(str(job_id), None)

def get_tts_audio_path(job_id):
    return TTS_AUDIO_PATH.get(str(job_id), None)
