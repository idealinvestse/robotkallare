from fastapi import Request, HTTPException
from twilio.request_validator import RequestValidator
from twilio.twiml.voice_response import VoiceResponse, Gather
from .config import get_settings

settings = get_settings()
validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)

def validate_twilio_request(request: Request, body: bytes) -> None:
    url = str(request.url)
    signature = request.headers.get("X-Twilio-Signature", "")
    if not validator.validate(url, body.decode(), signature):
        raise HTTPException(status_code=401, detail="Invalid Twilio signature")

def build_twiml() -> str:
    vr = VoiceResponse()
    gather = Gather(
        num_digits=1,
        timeout=5,
        action="/dtmf",
        method="POST",
    )
    gather.play(url="https://example.com/your-pre-recorded-message.mp3")
    vr.append(gather)
    vr.say("We did not receive input. Goodbye.")
    vr.hangup()
    return str(vr)
