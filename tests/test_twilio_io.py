from app.twilio_io import build_twiml

def test_build_twiml_contains_gather():
    xml = build_twiml()
    assert "<Gather" in xml
    assert 'action="/dtmf"' in xml
    assert "https://example.com/your-pre-recorded-message.mp3" in xml
