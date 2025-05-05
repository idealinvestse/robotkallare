"""
Service for handling realtime AI calls using OpenAI and Twilio.
"""
import json
import base64
import asyncio
import logging
import websockets
from twilio.twiml.voice_response import VoiceResponse
from datetime import datetime
from typing import Optional, Dict, List, Any
from fastapi import WebSocket, WebSocketDisconnect
from sqlmodel import Session, select
from uuid import UUID

from app.config import get_settings
from app.repositories.call_repository import CallRepository
from app.models import RealtimeCall
from app.realtime.schemas import RealtimeCallStatus

logger = logging.getLogger(__name__)
settings = get_settings()


class RealtimeService:
    """Service for handling realtime AI calls."""

    async def _handle_connection_error(self, twilio_ws: WebSocket, message: str = None):
        """Send a TwiML <Say> fallback message to the caller and close the websocket."""
        settings = get_settings()
        fallback_message = message or getattr(settings, "REALTIME_CALL_FALLBACK_MESSAGE", "I'm having trouble connecting to the AI service. Please try again later.")
        logger.error(f"Realtime call error: {fallback_message}")
        response = VoiceResponse()
        response.say(fallback_message)
        await twilio_ws.send_text(str(response))
        await twilio_ws.close()
    
    def __init__(self, session: Session):
        """Initialize the service with a database session."""
        self.session = session
        self.repository = CallRepository(session)
        self.openai_api_key = settings.OPENAI_API_KEY
        self.voice = settings.REALTIME_VOICE
        self.system_message = settings.REALTIME_SYSTEM_MESSAGE
    
    async def log_call_start(self, call_sid: str, meta_str: str = None) -> UUID:
        """Log the start of a realtime call and return the record ID."""
        # Parse metadata to extract campaign/contact IDs if provided
        campaign_id = None
        contact_id = None
        
        if meta_str:
            try:
                meta_data = json.loads(meta_str)
                campaign_id = meta_data.get("campaign_id")
                contact_id = meta_data.get("contact_id")
            except:
                logger.error(f"Failed to parse call metadata: {meta_str}")
        
        # Create new call record
        realtime_call = RealtimeCall(
            call_sid=call_sid,
            campaign_id=campaign_id,
            contact_id=contact_id,
            status=RealtimeCallStatus.INITIATED.value
        )
        self.session.add(realtime_call)
        self.session.commit()
        self.session.refresh(realtime_call)
        
        logger.info(f"Logged realtime call start: {call_sid}, ID: {realtime_call.id}")
        return realtime_call.id
    
    async def update_call_status(self, call_sid: str, status: RealtimeCallStatus) -> bool:
        """Update the status of a realtime call."""
        query = select(RealtimeCall).where(RealtimeCall.call_sid == call_sid)
        call = self.session.exec(query).first()
        
        if call:
            call.status = status.value
            if status == RealtimeCallStatus.COMPLETED:
                call.ended_at = datetime.utcnow()
                # Calculate duration if we have start time
                if call.started_at:
                    call.duration_seconds = (call.ended_at - call.started_at).total_seconds()
            
            self.session.commit()
            logger.info(f"Updated call status: {call_sid} to {status.value}")
            return True
        else:
            logger.warning(f"Call not found for status update: {call_sid}")
            return False
    
    async def handle_media_stream(self, twilio_ws: WebSocket, meta_str: str = None):
        """Handle WebSocket connection between Twilio and OpenAI."""
        logger.info("New media stream connection")
        await twilio_ws.accept()
        
        # Verify if OpenAI API key is configured
        if not self.openai_api_key:
            logger.error("OpenAI API key is not configured. Unable to process realtime call.")
            # Send error message to caller using Twilio's text-to-speech
            await self._handle_connection_error(
                twilio_ws,
                "The AI service is not properly configured. Please try again later."
            )
            return
        
        # Check if the feature is enabled
        settings = get_settings()
        if not settings.REALTIME_ENABLED:
            logger.warning("Realtime AI calls are disabled. Rejecting connection.")
            await self._handle_connection_error(
                twilio_ws,
                "This feature is currently disabled. Please try again later."
            )
            return
        
        # These variables need to be accessible by nested functions
        stream_sid = None
        latest_media_timestamp = 0
        last_assistant_item = None
        mark_queue = []
        response_start_timestamp_twilio = None
        
        try:
            # Connect to OpenAI
            async with websockets.connect(
                'wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01',
                extra_headers={
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "OpenAI-Beta": "realtime=v1"
                }
            ) as openai_ws:
                # Initialize OpenAI session
                await self._initialize_session(openai_ws)
                
                # Define helper functions with access to the shared state
                async def receive_from_twilio():
                    """Receive audio from Twilio and forward to OpenAI."""
                    nonlocal stream_sid, latest_media_timestamp
                    try:
                        async for message in twilio_ws.iter_text():
                            data = json.loads(message)
                            
                            if data['event'] == 'media' and openai_ws.open:
                                latest_media_timestamp = int(data['media']['timestamp'])
                                
                                # Forward audio to OpenAI
                                audio_append = {
                                    "type": "input_audio_buffer.append",
                                    "audio": data['media']['payload']
                                }
                                await openai_ws.send(json.dumps(audio_append))
                            
                            elif data['event'] == 'start':
                                stream_sid = data['start']['streamSid']
                                logger.info(f"Stream started: {stream_sid}")
                                
                                # Log call start in database
                                if stream_sid:
                                    await self.log_call_start(stream_sid, meta_str)
                                    await self.update_call_status(
                                        stream_sid, 
                                        RealtimeCallStatus.CONNECTED
                                    )
                                
                                # Reset state variables
                                response_start_timestamp_twilio = None
                                latest_media_timestamp = 0
                                last_assistant_item = None
                                
                            elif data['event'] == 'mark':
                                if mark_queue:
                                    mark_queue.pop(0)
                            
                            elif data['event'] == 'stop':
                                logger.info(f"Stream stopped: {stream_sid}")
                                
                                # Update call status
                                if stream_sid:
                                    await self.update_call_status(
                                        stream_sid,
                                        RealtimeCallStatus.COMPLETED
                                    )
                                
                                # Close OpenAI connection
                                if openai_ws.open:
                                    await openai_ws.close()
                                return
                                
                    except WebSocketDisconnect:
                        logger.info("Twilio client disconnected")
                        
                        # Update call status
                        if stream_sid:
                            await self.update_call_status(
                                stream_sid,
                                RealtimeCallStatus.COMPLETED
                            )
                        
                        # Close OpenAI connection
                        if openai_ws.open:
                            await openai_ws.close()
                    except Exception as e:
                        logger.error(f"Error in receive_from_twilio: {e}")
                        
                        # Update call status on error
                        if stream_sid:
                            await self.update_call_status(
                                stream_sid,
                                RealtimeCallStatus.FAILED
                            )
                
                async def send_to_twilio():
                    """Receive responses from OpenAI and send to Twilio."""
                    nonlocal last_assistant_item, response_start_timestamp_twilio
                    
                    try:
                        async for openai_message in openai_ws:
                            response = json.loads(openai_message)
                            
                            # Log specific event types
                            log_event_types = ['error', 'response.content.done', 'response.done']
                            if response.get('type') in log_event_types:
                                logger.debug(f"OpenAI event: {response['type']}")
                            
                            # Audio data from OpenAI to Twilio
                            if response.get('type') == 'response.audio.delta' and 'delta' in response:
                                # Update call status to in_progress on first audio
                                if stream_sid and last_assistant_item is None:
                                    await self.update_call_status(
                                        stream_sid,
                                        RealtimeCallStatus.IN_PROGRESS
                                    )
                                
                                # Convert audio payload
                                audio_payload = base64.b64encode(
                                    base64.b64decode(response['delta'])
                                ).decode('utf-8')
                                
                                # Send to Twilio
                                audio_delta = {
                                    "event": "media",
                                    "streamSid": stream_sid,
                                    "media": {
                                        "payload": audio_payload
                                    }
                                }
                                await twilio_ws.send_json(audio_delta)
                                
                                # Set start timestamp for new response
                                if response_start_timestamp_twilio is None:
                                    response_start_timestamp_twilio = latest_media_timestamp
                                
                                # Update assistant item for potential interruption handling
                                if response.get('item_id'):
                                    last_assistant_item = response['item_id']
                                
                                # Send mark for timing
                                await _send_mark()
                            
                            # Handle interruptions
                            elif response.get('type') == 'input_audio_buffer.speech_started':
                                logger.debug("Speech started detected")
                                
                                if last_assistant_item:
                                    logger.debug(f"Interrupting response: {last_assistant_item}")
                                    await _handle_interruption()
                    
                    except Exception as e:
                        logger.error(f"Error in send_to_twilio: {e}")
                        
                        # Update call status on error
                        if stream_sid:
                            await self.update_call_status(
                                stream_sid,
                                RealtimeCallStatus.FAILED
                            )
                
                async def _handle_interruption():
                    """Handle interruption when user starts speaking during AI response."""
                    nonlocal last_assistant_item, response_start_timestamp_twilio
                    
                    if mark_queue and response_start_timestamp_twilio is not None:
                        elapsed_time = latest_media_timestamp - response_start_timestamp_twilio
                        
                        # Truncate the assistant's response
                        truncate_event = {
                            "type": "conversation.item.truncate",
                            "item_id": last_assistant_item,
                            "content_index": 0,
                            "audio_end_ms": elapsed_time
                        }
                        await openai_ws.send(json.dumps(truncate_event))
                        
                        # Clear Twilio's audio buffer
                        await twilio_ws.send_json({
                            "event": "clear",
                            "streamSid": stream_sid
                        })
                        
                        # Reset state
                        mark_queue.clear()
                        last_assistant_item = None
                        response_start_timestamp_twilio = None
                
                async def _send_mark():
                    """Send mark event to Twilio for timing."""
                    if stream_sid:
                        mark_event = {
                            "event": "mark",
                            "streamSid": stream_sid,
                            "mark": {"name": "responsePart"}
                        }
                        await twilio_ws.send_json(mark_event)
                        mark_queue.append('responsePart')
                
                # Start the bidirectional communication tasks
                await asyncio.gather(receive_from_twilio(), send_to_twilio())
                
        except Exception as e:
            logger.error(f"Error in handle_media_stream: {e}")
            
            # Update call status on error
            if stream_sid:
                await self.update_call_status(stream_sid, RealtimeCallStatus.FAILED)
    
    async def _initialize_session(self, openai_ws):
        """Initialize OpenAI session with configuration."""
        session_update = {
            "type": "session.update",
            "session": {
                "turn_detection": {"type": "server_vad"},
                "input_audio_format": "g711_ulaw",
                "output_audio_format": "g711_ulaw",
                "voice": self.voice,
                "instructions": self.system_message,
                "modalities": ["text", "audio"],
                "temperature": 0.8,
            }
        }
        logger.debug('Initializing OpenAI session')
        await openai_ws.send(json.dumps(session_update))

    async def send_initial_prompt(self, openai_ws, prompt: str = None):
        """Optionally send an initial prompt to make the AI speak first."""
        if not prompt:
            prompt = "Greet the caller and ask how you can help them today."
            
        initial_conversation_item = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": prompt
                    }
                ]
            }
        }
        await openai_ws.send(json.dumps(initial_conversation_item))
        await openai_ws.send(json.dumps({"type": "response.create"}))
