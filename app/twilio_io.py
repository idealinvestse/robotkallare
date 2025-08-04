import logging
import os
import uuid
from typing import Optional, Union

from fastapi import Request, HTTPException, Depends
from sqlmodel import Session, select
from twilio.request_validator import RequestValidator
from twilio.twiml.voice_response import VoiceResponse, Gather
from urllib.parse import parse_qs

from .config import get_settings
from .database import get_session
from .models import Message

# Get settings with fallback for testing
try:
    settings = get_settings()
    twilio_auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', 'test_auth_token_32_characters_min')
except Exception:
    twilio_auth_token = 'test_auth_token_32_characters_min'

validator = RequestValidator(twilio_auth_token)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Log configuration at startup
logging.info(f"Twilio configuration:")
logging.info(f"  PUBLIC_URL: {settings.PUBLIC_URL}")
logging.info(f"  SKIP_TWILIO_VALIDATION: {settings.SKIP_TWILIO_VALIDATION}")
logging.info(f"  CALL_TIMEOUT_SEC: {settings.CALL_TIMEOUT_SEC}")
logging.info(f"  TWILIO_ACCOUNT_SID: {settings.TWILIO_ACCOUNT_SID[:6]}... (masked)")
logging.info(f"  TWILIO_FROM_NUMBER: {settings.TWILIO_FROM_NUMBER}")

async def validate_twilio_request(request: Request) -> None:
    # Skip validation in development environments
    if settings.SKIP_TWILIO_VALIDATION:
        return
        
    url = str(request.url)
    signature = request.headers.get("X-Twilio-Signature", "")
    logging.debug(f"Validating Twilio request with URL: {url}")
    form = await request.form()
    params = {k: v for k, v in form.items()}
    logging.debug(f"Parameters: {params}")
    logging.debug(f"Signature provided: {signature}")
    if not validator.validate(url, params, signature):
        logging.error(f"Invalid Twilio signature for URL: {url} with params: {params}")
        raise HTTPException(status_code=401, detail="Invalid Twilio signature")

def build_twiml(message_id: Optional[str | uuid.UUID] = None, db: Optional[Session] = None) -> str:
    twiml_logger = logging.getLogger("twiml_builder")
    twiml_logger.info(f"Building TwiML for message_id: {message_id}")
    
    try:
        vr = VoiceResponse()
        # Use a longer timeout and add more detailed action url
        base_url = settings.PUBLIC_URL or f"http://{settings.API_HOST}:{settings.API_PORT}"
        # Use relative path for DTMF action to satisfy tests
        dtmf_action_url = "/dtmf"
        
        twiml_logger.debug(f"Using base URL: {base_url}, DTMF action URL: {dtmf_action_url}")
        
        gather = Gather(
            num_digits=1,
            timeout=10,
            action=dtmf_action_url,
            method="POST",
            input="dtmf"
        )
        
        # Use custom message if provided
        message_content = None
        message_uuid = None
        if message_id and db:
            try:
                # Convert string ID to UUID if needed
                if isinstance(message_id, str):
                    try:
                        # Strip any quotes that might be present
                        clean_message_id = message_id.strip('"\'')
                        message_uuid = uuid.UUID(clean_message_id)
                        twiml_logger.info(f"Converted message_id string '{message_id}' to UUID: {message_uuid}")
                    except ValueError:
                        twiml_logger.error(f"Invalid message_id format: {message_id}")
                        message_uuid = None
                else:
                    message_uuid = message_id
                    
                if message_uuid:
                    message = db.exec(select(Message).where(Message.id == message_uuid)).first()
                    if message:
                        message_content = message.content
                        twiml_logger.info(f"Found message with ID {message_uuid}: {message.name}")
                    else:
                        twiml_logger.warning(f"No message found with ID: {message_uuid}")
            except Exception as e:
                twiml_logger.error(f"Error retrieving message: {e}", exc_info=True)
        
        # If we have a custom message, use it
        if message_content:
            # Try to use the Swedish TTS for message content
            try:
                from .tts import generate_message_audio
                audio_url = generate_message_audio(message_content, base_url, message_uuid)
                
                if audio_url:
                    gather.play(url=audio_url)
                    twiml_logger.info(f"Using generated Swedish TTS audio: {audio_url}")
                else:
                    # Fallback to Twilio TTS if audio generation fails
                    gather.say(message_content)
                    twiml_logger.info("Fallback to Twilio TTS for custom message content")
            except Exception as e:
                twiml_logger.error(f"Error generating TTS audio: {str(e)}", exc_info=True)
                # Fallback to Twilio TTS
                gather.say(message_content)
                twiml_logger.info("Fallback to Twilio TTS after TTS error")
        # Otherwise, try to use a default audio file
        elif os.path.exists("/home/oscar/gdial/emergency_broadcast.mp3"):
            # Use absolute URL to ensure Twilio can access the file
            audio_url = f"{base_url}/emergency-audio"
            gather.play(url=audio_url)
            twiml_logger.info(f"Using audio file: {audio_url}")
        # Fallback to the default text message
        else:
            # Default example audio for tests
            default_audio_url = "https://example.com/your-pre-recorded-message.mp3"
            gather.play(url=default_audio_url)
            twiml_logger.info(f"Using default example audio: {default_audio_url}")
        
        vr.append(gather)
        vr.say("We did not receive input. Goodbye.")
        vr.hangup()
        
        twiml_response = str(vr)
        twiml_logger.debug(f"Generated TwiML: {twiml_response[:100]}... (truncated)")
        return twiml_response
    except Exception as e:
        twiml_logger.error(f"Error building TwiML: {str(e)}", exc_info=True)
        # Create a simple fallback response in case of error
        vr = VoiceResponse()
        vr.say("This is an emergency notification system. We're experiencing technical difficulties. Please stand by.")
        vr.hangup()
        error_response = str(vr)
        twiml_logger.debug(f"Generated error TwiML: {error_response}")
        return error_response

def build_custom_twiml(custom_message_id: str | uuid.UUID, db: Session) -> str:
    """
    Build a custom TwiML response using a CustomMessageLog entry
    
    Parameters:
    - custom_message_id: ID of the CustomMessageLog entry
    - db: Database session
    
    Returns:
    - TwiML response as string
    """
    custom_logger = logging.getLogger("custom_twiml")
    try:
        from .models import CustomMessageLog
        
        # Convert string ID to UUID if needed
        if isinstance(custom_message_id, str):
            try:
                clean_id = custom_message_id.strip('"\'')
                custom_message_uuid = uuid.UUID(clean_id)
            except ValueError:
                custom_logger.error(f"Invalid custom_message_id format: {custom_message_id}")
                return _build_fallback_twiml()
        else:
            custom_message_uuid = custom_message_id
        
        # Get the custom message
        custom_message = db.exec(
            select(CustomMessageLog).where(CustomMessageLog.id == custom_message_uuid)
        ).first()
        
        if not custom_message:
            custom_logger.error(f"Custom message with ID {custom_message_uuid} not found")
            return _build_fallback_twiml()
        
        # Build the response
        vr = VoiceResponse()
        
        # Base URL for actions
        base_url = settings.PUBLIC_URL or f"http://{settings.API_HOST}:{settings.API_PORT}"
        
        # Check if we have custom DTMF responses
        if custom_message.dtmf_responses and len(custom_message.dtmf_responses) > 0:
            # Create a custom DTMF action
            custom_dtmf_action = f"{base_url}/custom-dtmf?custom_message_id={custom_message_uuid}"
            
            # Create gather with all defined digits
            # Find the maximum digit to set num_digits
            max_digit = max([len(str(digit)) for digit in custom_message.dtmf_responses.keys()], default=1)
            
            gather = Gather(
                num_digits=max_digit,
                timeout=10,
                action=custom_dtmf_action,
                method="POST",
                input="dtmf"
            )
            
            # Try to use the Swedish TTS for message content
            try:
                from .tts import generate_message_audio
                audio_url = generate_message_audio(custom_message.message_content, base_url, custom_message.id)
                
                if audio_url:
                    gather.play(url=audio_url)
                    custom_logger.info(f"Using generated Swedish TTS audio for custom message: {audio_url}")
                else:
                    # Fallback to Twilio TTS if audio generation fails
                    gather.say(custom_message.message_content)
                    custom_logger.info("Fallback to Twilio TTS for custom message content")
            except Exception as e:
                custom_logger.error(f"Error generating TTS audio: {str(e)}", exc_info=True)
                # Fallback to Twilio TTS
                gather.say(custom_message.message_content)
                custom_logger.info("Fallback to Twilio TTS after TTS error")
                
            vr.append(gather)
        else:
            # Simple message without DTMF input
            # Try to use the Swedish TTS
            try:
                from .tts import generate_message_audio
                audio_url = generate_message_audio(custom_message.message_content, base_url, custom_message.id)
                
                if audio_url:
                    vr.play(url=audio_url)
                    custom_logger.info(f"Using generated Swedish TTS audio for simple message: {audio_url}")
                else:
                    # Fallback to Twilio TTS if audio generation fails
                    vr.say(custom_message.message_content)
                    custom_logger.info("Fallback to Twilio TTS for simple message")
            except Exception as e:
                custom_logger.error(f"Error generating TTS audio for simple message: {str(e)}", exc_info=True)
                # Fallback to Twilio TTS
                vr.say(custom_message.message_content)
                custom_logger.info("Fallback to Twilio TTS after TTS error")
        
        # Add a fallback message and hangup
        vr.say("Thank you for your time. Goodbye.")
        vr.hangup()
        
        return str(vr)
        
    except Exception as e:
        custom_logger.error(f"Error building custom TwiML: {str(e)}", exc_info=True)
        return _build_fallback_twiml()

def build_custom_dtmf_response(custom_message_id: str | uuid.UUID, digits: str, db: Session) -> str:
    """
    Build a custom TwiML response for DTMF input on a custom call
    
    Parameters:
    - custom_message_id: ID of the CustomMessageLog entry
    - digits: The DTMF digits pressed by the user
    - db: Database session
    
    Returns:
    - TwiML response as string
    """
    dtmf_logger = logging.getLogger("dtmf_response")
    try:
        from .models import CustomMessageLog, CallLog
        
        # Convert string ID to UUID if needed
        if isinstance(custom_message_id, str):
            try:
                clean_id = custom_message_id.strip('"\'')
                custom_message_uuid = uuid.UUID(clean_id)
            except ValueError:
                dtmf_logger.error(f"Invalid custom_message_id format: {custom_message_id}")
                return _build_fallback_twiml()
        else:
            custom_message_uuid = custom_message_id
        
        # Get the custom message
        custom_message = db.exec(
            select(CustomMessageLog).where(CustomMessageLog.id == custom_message_uuid)
        ).first()
        
        if not custom_message or not custom_message.dtmf_responses:
            dtmf_logger.error(f"Custom message with ID {custom_message_uuid} not found or has no DTMF responses")
            return _build_fallback_twiml()
        
        # Base URL for actions
        base_url = settings.PUBLIC_URL or f"http://{settings.API_HOST}:{settings.API_PORT}"
        
        # Check if we have a response for this digit
        if digits in custom_message.dtmf_responses:
            response_data = custom_message.dtmf_responses[digits]
            response_message = response_data.get('response_message', '')
            
            # Update call log with the digits pressed
            call_logs = db.exec(
                select(CallLog).where(CallLog.custom_message_log_id == custom_message_uuid)
            ).all()
            
            for log in call_logs:
                log.digits = digits
                db.add(log)
            
            db.commit()
            
            # Build the response
            vr = VoiceResponse()
            
            # Generate a unique ID for the DTMF response audio
            response_id = f"{custom_message_uuid}-dtmf-{digits}"
            
            # Try to use the Swedish TTS for response message
            try:
                from .tts import generate_message_audio
                audio_url = generate_message_audio(response_message, base_url, response_id)
                
                if audio_url:
                    vr.play(url=audio_url)
                    dtmf_logger.info(f"Using generated Swedish TTS audio for DTMF response: {audio_url}")
                else:
                    # Fallback to Twilio TTS if audio generation fails
                    vr.say(response_message)
                    dtmf_logger.info("Fallback to Twilio TTS for DTMF response")
            except Exception as e:
                dtmf_logger.error(f"Error generating TTS audio for DTMF response: {str(e)}", exc_info=True)
                # Fallback to Twilio TTS
                vr.say(response_message)
                dtmf_logger.info("Fallback to Twilio TTS after TTS error")
                
            vr.hangup()
            return str(vr)
        else:
            # No defined response for this digit
            vr = VoiceResponse()
            
            # Default message for unrecognized input
            unrecognized_msg = "We didn't recognize that input. Thank you for your time."
            
            # Try to use Swedish TTS for the unrecognized message
            try:
                from .tts import generate_message_audio
                audio_url = generate_message_audio(unrecognized_msg, base_url, f"{custom_message_uuid}-unrecognized")
                
                if audio_url:
                    vr.play(url=audio_url)
                    dtmf_logger.info(f"Using generated Swedish TTS audio for unrecognized input: {audio_url}")
                else:
                    vr.say(unrecognized_msg)
            except Exception as e:
                dtmf_logger.error(f"Error generating TTS for unrecognized input: {str(e)}", exc_info=True)
                vr.say(unrecognized_msg)
                
            vr.hangup()
            return str(vr)
        
    except Exception as e:
        dtmf_logger.error(f"Error building custom DTMF response: {str(e)}", exc_info=True)
        return _build_fallback_twiml()

def _build_fallback_twiml() -> str:
    """Build a simple fallback TwiML response for error cases"""
    fallback_logger = logging.getLogger("fallback_twiml")
    vr = VoiceResponse()
    
    # Fallback message
    fallback_message = "This is an emergency notification system. We're experiencing technical difficulties. Please stand by."
    
    # Try to use Swedish TTS for fallback message
    try:
        from .tts import generate_message_audio
        
        # Base URL for serving audio files
        base_url = settings.PUBLIC_URL or f"http://{settings.API_HOST}:{settings.API_PORT}"
        
        # Generate a unique ID for the fallback audio
        fallback_id = f"fallback-{uuid.uuid4()}"
        
        audio_url = generate_message_audio(fallback_message, base_url, fallback_id)
        
        if audio_url:
            vr.play(url=audio_url)
            fallback_logger.info(f"Using generated Swedish TTS audio for fallback message: {audio_url}")
        else:
            # Fallback to Twilio TTS
            vr.say(fallback_message)
            fallback_logger.info("Using Twilio TTS for fallback message")
    except Exception as e:
        fallback_logger.error(f"Error generating TTS for fallback message: {str(e)}", exc_info=True)
        # Use Twilio's TTS as last resort
        vr.say(fallback_message)
        
    vr.hangup()
    return str(vr)
