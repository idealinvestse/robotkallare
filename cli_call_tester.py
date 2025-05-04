#!/usr/bin/env python
"""
GDial Call Tester - An Interactive CLI Tool

This tool allows developers to test GDial call functionality directly from the command line,
without needing to use the web interface. It supports both TTS and realtime AI calls,
with an easy-to-use interface, detailed logging, and proper error handling.

Features:
- Interactive mode with menu-driven interface
- Direct command mode for automation
- Colored output for better readability
- TTS and Realtime AI call initiation

Miljövariabler:
    SQLITE_DB - URL för databasanslutning (standard: sqlite:///./dialer.db)
    TWILIO_ACCOUNT_SID - Twilio-konto SID
    TWILIO_AUTH_TOKEN - Twilio-autentiseringstoken
    TWILIO_FROM_NUMBER - Avsändarnummer för samtal (E.164-format)
    PUBLIC_URL - Bas-URL för GDial API-server
    GDIAL_CLI_SIMULATION - Sätt till 'true' för att aktivera simuleringsläge
    GDIAL_CLI_NONINTERACTIVE - Sätt till 'true' för att förhindra alla interaktiva förfrågningar

Version: 1.0.0
Author: Ideal Invest
License: Proprietär
"""

import argparse
import asyncio
import os
import sys
import json
import uuid
import logging
import re
import time
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pathlib import Path

import httpx
from sqlmodel import Session, select, create_engine
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# Try to import colored output, with fallback for compatibility
try:
    from colorama import init as colorama_init, Fore, Back, Style
    colorama_init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    # Create dummy color objects if colorama is not available
    class DummyColor:
        def __getattr__(self, name):
            return ""
    Fore = DummyColor()
    Back = DummyColor()
    Style = DummyColor()
    HAS_COLOR = False

# Configure nice logging for CLI use
log_format = "%(levelname)s: %(message)s" if sys.stdout.isatty() else "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=log_format
)
logger = logging.getLogger("gdial-cli")

# Create a console logger for user messages
class ConsoleLogger:
    def info(self, msg, *args, **kwargs):
        if HAS_COLOR:
            print(f"{Fore.CYAN}{msg}{Style.RESET_ALL}", *args, **kwargs)
        else:
            print(f"INFO: {msg}", *args, **kwargs)
            
    def success(self, msg, *args, **kwargs):
        if HAS_COLOR:
            print(f"{Fore.GREEN}{msg}{Style.RESET_ALL}", *args, **kwargs)
        else:
            print(f"SUCCESS: {msg}", *args, **kwargs)
            
    def error(self, msg, *args, **kwargs):
        if HAS_COLOR:
            print(f"{Fore.RED}{msg}{Style.RESET_ALL}", *args, **kwargs)
        else:
            print(f"ERROR: {msg}", *args, **kwargs)
            
    def warning(self, msg, *args, **kwargs):
        if HAS_COLOR:
            print(f"{Fore.YELLOW}{msg}{Style.RESET_ALL}", *args, **kwargs)
        else:
            print(f"WARNING: {msg}", *args, **kwargs)
    
    def title(self, msg, *args, **kwargs):
        if HAS_COLOR:
            print(f"\n{Fore.BLUE}{Style.BRIGHT}{msg}{Style.RESET_ALL}", *args, **kwargs)
        else:
            border = "=" * len(msg)
            print(f"\n{border}\n{msg}\n{border}", *args, **kwargs)
    
    def section(self, msg, *args, **kwargs):
        if HAS_COLOR:
            print(f"{Fore.MAGENTA}{msg}{Style.RESET_ALL}", *args, **kwargs)
        else:
            print(f"\n--- {msg} ---", *args, **kwargs)
    
console = ConsoleLogger()

# Load environment variables - try multiple possible locations
def load_env_from_paths():
    """Try to load .env file from multiple paths to improve reliability."""
    paths = [
        ".env",                     # Current directory
        "../.env",                  # Parent directory
        os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")  # Script directory
    ]
    
    for path in paths:
        if os.path.exists(path):
            console.info(f"Loading environment from: {path}")
            load_dotenv(path)
            return True
            
    console.warning("Could not find .env file in common paths.")
    return False
    
load_env_from_paths()

# Global simulation mode flag
SIMULATION_MODE = False

# Detect if we're in an interactive environment
def is_interactive():
    """Check if the script is running in an interactive environment."""
    import sys
    return sys.stdin.isatty() and os.environ.get("GDIAL_CLI_NONINTERACTIVE", "").lower() not in ("true", "1", "yes", "y")

# Check for required environment variables
def check_environment():
    """Check that all required environment variables are set.
    Returns True if all required variables are available, or if simulation mode is activated.
    In non-interactive mode, will make reasonable default choices.
    """
    global SIMULATION_MODE
    
    # Check if simulation mode is requested via environment variable
    if os.environ.get("GDIAL_CLI_SIMULATION", "").lower() in ("true", "1", "yes", "y"):
        SIMULATION_MODE = True
        console.warning("Running in SIMULATION MODE - no actual calls will be made")
        return True
    
    # Define tiers of required variables
    critical_vars = [  # These are absolutely necessary
        "TWILIO_ACCOUNT_SID", 
        "TWILIO_AUTH_TOKEN",
        "TWILIO_FROM_NUMBER"
    ]
    
    important_vars = [  # These can be worked around
        "DATABASE_URL",
        "PUBLIC_URL"
    ]
    
    # Check if we're running in interactive mode
    interactive = is_interactive()
    
    # Check critical variables
    missing_critical = [var for var in critical_vars if not os.environ.get(var)]
    if missing_critical:
        console.error("Missing critical environment variables:")
        for var in missing_critical:
            console.error(f" - {var}")
        console.info("These variables are required for any call functionality.")
        console.info("Please set these variables in your .env file or environment.")
        
        # In non-interactive mode, automatically switch to simulation mode
        if not interactive:
            console.warning("Non-interactive mode detected - automatically switching to simulation mode")
            SIMULATION_MODE = True
            os.environ["GDIAL_CLI_SIMULATION"] = "true"  # Set for future runs
            return True
            
        # In interactive mode, ask the user
        response = input("\nWould you like to run in simulation mode instead? (y/n): ").strip().lower()
        if response in ("y", "yes"):
            SIMULATION_MODE = True
            console.warning("Activating SIMULATION MODE - no actual calls will be made")
            os.environ["GDIAL_CLI_SIMULATION"] = "true"  # Set for future runs
            return True
        return False
    
    # Check important but non-critical variables
    missing_important = [var for var in important_vars if not os.environ.get(var)]
    if missing_important:
        console.warning("Missing some recommended environment variables:")
        for var in missing_important:
            console.warning(f" - {var}")
        
        if "DATABASE_URL" in missing_important:
            console.info("Without DATABASE_URL, some features like message listing won't work.")
            os.environ["DATABASE_URL"] = "sqlite:///./gdial_cli_dummy.db"  # Set dummy DB
            console.info("Using an in-memory database for this session.")
            
        if "PUBLIC_URL" in missing_important:
            default_url = "http://localhost:8000"
            os.environ["PUBLIC_URL"] = default_url
            console.info(f"Using default PUBLIC_URL: {default_url}")
        
        # In non-interactive mode, automatically continue
        if not interactive:
            console.info("Non-interactive mode detected - automatically continuing with limited features")
            return True
            
        # In interactive mode, ask the user
        response = input("\nContinue anyway? Some features may be limited (y/n): ").strip().lower()
        if response not in ("y", "yes"):
            return False
    
    return True

# Import app modules safely
def safely_import_app_modules():
    """Safely import modules from the app package and handle errors."""
    global SIMULATION_MODE
    
    try:
        # First try to patch the config handling to be more forgiving
        # This is a monkey patch to make the Settings class more tolerant of .env file issues
        import app.config
        import re
        from typing import Any, Dict
        from pydantic_settings import BaseSettings
        
        # Store original __init__ to call after our preprocessing
        original_init = app.config.Settings.__init__
        
        def safer_settings_init(self, **data: Any):
            """A more forgiving Settings __init__ that cleans up problematic environment variables."""
            # Process any environment variable that might have comments
            for key in list(data.keys()):
                if isinstance(data[key], str):
                    # Strip comments from strings that should be numeric
                    if key.endswith("_MINUTES") or key.endswith("_SECONDS") or key.endswith("_SEC") or key.endswith("_ATTEMPTS"):
                        # Extract only the numeric part from the beginning
                        match = re.match(r'^\s*(\d+)', data[key])
                        if match:
                            data[key] = int(match.group(1))
                            
                    # Special case for array-like strings
                    if key.endswith("_TYPES") and data[key].startswith("[") and data[key].endswith("]"): 
                        try:
                            import json
                            # Try to parse as JSON if possible
                            data[key] = json.loads(data[key])
                        except:
                            # Otherwise just keep as is
                            pass
                    
            # Call the original init with cleaned data
            original_init(self, **data)
            
        # Apply our monkey patch
        app.config.Settings.__init__ = safer_settings_init
        
        # Now try to import what we need
        from sqlmodel import Session, create_engine
        from app.config import get_settings
        
        return True
    except Exception as e:
        console.error(f"Failed to safely import app modules: {e}")
        console.warning("Running in restricted mode with limited functionality")
        SIMULATION_MODE = True
        return False

# Only call this once at startup
app_modules_available = safely_import_app_modules()

def get_db_session():
    """Safely get a database session if possible."""
    if not app_modules_available:
        return None
        
    try:
        from sqlmodel import Session, create_engine
        from app.config import get_settings
        
        settings = get_settings()
        # GDial använder SQLITE_DB attributet istället för database_url
        db_url = getattr(settings, 'SQLITE_DB', 'sqlite:///./dialer.db')
        engine = create_engine(db_url)
        return Session(engine)
    except Exception as e:
        console.error(f"Database connection error: {e}")
        return None

# Phone number validation
def validate_phone_number(phone):
    """Validate that the phone number is in E.164 format."""
    if not phone.startswith("+"):
        return False
    # Remove the + and check if the rest is numeric
    return phone[1:].isdigit()

# Models (minimal versions to avoid importing the entire app)
class Message:
    """Simplified Message model for CLI use."""
    id: uuid.UUID
    name: str
    content: str
    is_template: bool
    created_at: datetime

class Contact:
    """Simplified Contact model for CLI use."""
    id: uuid.UUID
    phone_number: str
    name: str
    email: Optional[str]

# Twilio client setup
def get_twilio_client():
    """Set up and return a Twilio client."""
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    
    if not account_sid or not auth_token:
        logger.error("Twilio credentials not found in environment variables")
        sys.exit(1)
        
    return Client(account_sid, auth_token)

# API functions
async def list_messages(interactive=False):
    """List all available messages from the database and optionally allow selection."""
    try:
        session = get_db_session()
        if not session:
            console.error("Could not connect to database.")
            return None
            
        messages = session.execute(select(Message)).all()
        
        if not messages:
            console.warning("No messages found in the database.")
            return None
        
        # Display the messages
        console.title("Available Messages")
        header = f"{Fore.WHITE}{Style.BRIGHT}{'#':<4} | {'ID':<38} | {'NAME':<30} | {'CONTENT'}{Style.RESET_ALL}" if HAS_COLOR else \
                f"{'#':<4} | {'ID':<38} | {'NAME':<30} | {'CONTENT'}"
        console.info(header)
        print("-----+-" + "-"*38 + "-+-" + "-"*30 + "-+-" + "-"*50)
        
        # Create a list to store message data
        message_list = []
        
        # Display messages with numbers for selection
        for i, msg in enumerate(messages, 1):
            message = msg[0]  # Extract from Row
            message_list.append(message)  # Save for potential selection
            content_preview = (message.content[:47] + '...') if len(message.content) > 50 else message.content
            row = f"{i:<4} | {str(message.id):<38} | {message.name[:27]+'...' if len(message.name) > 30 else message.name:<30} | {content_preview}"
            print(row)
            
        # If in interactive mode, allow selection
        if interactive and messages:
            print()
            while True:
                try:
                    selection = input("Select a message number (or 0 to cancel): ")
                    if selection.strip() == "0":
                        return None
                    idx = int(selection) - 1
                    if 0 <= idx < len(message_list):
                        return message_list[idx]
                    else:
                        console.error(f"Please select a number between 1 and {len(message_list)}")
                except ValueError:
                    console.error("Please enter a number")
        
        return message_list
            
    except Exception as e:
        console.error(f"Error listing messages: {e}")
        return None

async def get_message_by_id(message_id: str):
    """Get a message by ID."""
    try:
        session = get_db_session()
        message = session.execute(
            select(Message).where(Message.id == uuid.UUID(message_id))
        ).first()
        
        if not message:
            logger.error(f"Message with ID {message_id} not found")
            return None
            
        return message[0]  # Extract from Row
    except Exception as e:
        logger.error(f"Error getting message: {e}")
        return None

async def create_contact(phone_number: str):
    """Create a contact with the given phone number and return its ID."""
    global SIMULATION_MODE
    
    # If we're in simulation mode, return a fake contact ID
    if SIMULATION_MODE:
        simulated_id = str(uuid.uuid4())
        console.info(f"SIMULATION: Using simulated contact ID: {simulated_id}")
        return simulated_id
    
    # Try to use the database
    session = get_db_session()
    if not session:
        console.warning("Database connection failed, switching to simulation mode")
        SIMULATION_MODE = True
        simulated_id = str(uuid.uuid4())
        console.info(f"SIMULATION: Using simulated contact ID: {simulated_id}")
        return simulated_id
        
    try:
        # Try to import models - this could fail if app modules weren't initialized correctly
        try:
            from app.models import Contact as AppContact
        except ImportError as ie:
            console.error(f"Failed to import Contact model: {ie}")
            console.warning("Switching to simulation mode")
            SIMULATION_MODE = True
            simulated_id = str(uuid.uuid4())
            console.info(f"SIMULATION: Using simulated contact ID: {simulated_id}")
            return simulated_id
        
        # Determine correct phone field name
        # GDial kan använda antingen 'phone' eller 'phone_number' fält beroende på version
        phone_field_name = None
        for field_name in ['phone', 'phone_number']:
            if hasattr(AppContact, field_name):
                phone_field_name = field_name
                break
                
        if not phone_field_name:
            console.error("Could not determine phone field name in Contact model")
            console.warning("Switching to simulation mode")
            SIMULATION_MODE = True
            simulated_id = str(uuid.uuid4())
            console.info(f"SIMULATION: Using simulated contact ID: {simulated_id}")
            return simulated_id
            
        # Check if contact with this phone already exists
        try:
            if phone_field_name == 'phone':
                result = session.exec(select(AppContact).where(AppContact.phone == phone_number)).first()
            else:  # phone_number
                result = session.exec(select(AppContact).where(AppContact.phone_number == phone_number)).first()
            
            if result:
                console.info(f"Using existing contact: {result.name} ({getattr(result, phone_field_name)})")
                return result.id
        except Exception as lookup_err:
            console.error(f"Error looking up contact: {lookup_err}")
            # Continue to create new contact
        
        # Create a new contact - handle either phone field name
        try:
            contact_data = {
                "name": "CLI Test Contact",
                phone_field_name: phone_number,
                "email": f"cli_test_{uuid.uuid4()}@example.com"
            }
            
            contact = AppContact(**contact_data)
            session.add(contact)
            session.commit()
            session.refresh(contact)
            
            console.success(f"Created new contact with ID: {contact.id}")
            return contact.id
        except Exception as create_err:
            console.error(f"Error creating contact: {create_err}")
            raise  # Re-raise to be caught by outer exception handler
        
    except Exception as e:
        console.error(f"Error creating contact: {e}")
        console.warning("Switching to simulation mode")
        SIMULATION_MODE = True
        simulated_id = str(uuid.uuid4())
        console.info(f"SIMULATION: Using simulated contact ID: {simulated_id}")
        return simulated_id

async def make_tts_call(phone_number: str, message_id: str = None, message_text: str = None):
    """Make a TTS call using Twilio."""
    if not message_id and not message_text:
        console.error("Either message_id or message_text must be provided")
        return None
        
    if not validate_phone_number(phone_number):
        console.error(f"Invalid phone number format: {phone_number}")
        console.info("Phone number should be in E.164 format (e.g., +1234567890)")
        return None
    
    # Check environment
    if not check_environment():
        return None
        
    # Get config from environment
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    from_number = os.environ.get("TWILIO_FROM_NUMBER")
    base_url = os.environ.get("PUBLIC_URL", "http://localhost:8000")
    
    # Show progress indicator
    console.section("Initiating TTS Call")
    console.info(f"From: {from_number}")
    console.info(f"To: {phone_number}")
    
    # Check if we're in simulation mode
    if SIMULATION_MODE:
        console.info("SIMULATION: Creating simulated call (no actual API calls)")
        simulated_id = str(uuid.uuid4())
        simulated_result = {
            "id": simulated_id,
            "name": "Simulated Campaign",
            "status": "queued",
            "target_contact_count": 1,
            "queued_contact_count": 1,
            "message_id": message_id or "00000000-0000-0000-0000-000000000000",
            "created_at": datetime.now().isoformat()
        }
        console.success(f"SIMULATION: Call initiated successfully!")
        console.info(f"Campaign ID: {simulated_id}")
        console.info("\nSIMULATION: This is a simulated call, no actual call will be made.")
        return simulated_result
    
    try:
        # Handle message creation or selection
        processed_message_id = message_id
        
        # If we have message_text but no message_id, create a temporary message
        if message_text and not message_id:
            try:
                from app.models import Message as AppMessage
                session = get_db_session()
                if not session:
                    console.error("Database connection failed")
                    console.info("Using a simulated message ID instead.")
                    processed_message_id = str(uuid.uuid4())
                else:                
                    console.info("Creating temporary message...")
                    temp_message = AppMessage(
                        name="CLI Temporary Message",
                        content=message_text,
                        is_template=False
                    )
                    session.add(temp_message)
                    session.commit()
                    session.refresh(temp_message)
                    processed_message_id = str(temp_message.id)
                    console.success(f"Created temporary message with ID: {processed_message_id}")
            except Exception as e:
                console.error(f"Failed to create message in database: {e}")
                console.info("Using a simulated message ID instead.")
                processed_message_id = str(uuid.uuid4())
        
        # Create a contact for this phone number
        console.info("Setting up contact for call...")
        contact_id = await create_contact(phone_number)
        if not contact_id:
            console.error("Could not create or find contact in database")
            contact_id = str(uuid.uuid4())  # Generate a temporary ID
            console.info(f"Using temporary contact ID: {contact_id}")
            
        # Initiate the call through outreach API
        console.info("Submitting call request to GDial API...")
        try:
            # Försök hitta rätt API-sökväg för servern
            # Standardmappningar till olika GDial-deployments
            base_urls = [
                base_url,  # Använd konfigurerad URL först
                base_url.rstrip("/"),  # Utan trailing slash
                base_url.rstrip("/") + "/api",  # Med /api suffix
                "http://localhost:3003",  # Utvecklingsserver
                "http://127.0.0.1:3003"   # Alternativ lokal
            ]
            
            # Ta bort dubbletter
            base_urls = list(dict.fromkeys(base_urls))
            
            # Möjliga API-sökvägar
            possible_paths = [
                "/outreach/",          # Standard-endpoint
                "/api/outreach/",       # Med API-prefix
                "/v1/outreach/",        # Versionsprefix
                "/api/v1/outreach/"     # Kombinerad sökväg
            ]
            
            payload = {
                "message_id": processed_message_id,
                "contact_ids": [str(contact_id)],
                "campaign_name": "CLI Test Call",
                "description": "Test call initiated from CLI",
                "call_mode": "tts"
            }
            headers = {"Content-Type": "application/json"}
            
            response = None
            success = False
            error_messages = []
            successful_url = None
            
            async with httpx.AsyncClient() as client:
                # Försök olika kombinationer av bas-URL och sökvägar
                for base in base_urls:
                    for path in possible_paths:
                        try:
                            url = f"{base}{path}"
                            console.info(f"Trying API endpoint: {url}")
                            
                            # Set reasonable timeout for API requests
                            response = await client.post(url, json=payload, headers=headers, timeout=5.0)
                            
                            if response.status_code == 201 or response.status_code == 200:
                                console.success(f"Successfully connected to API endpoint: {url}")
                                success = True
                                successful_url = url
                                # Spara lösningen för framtida användning
                                os.environ['GDIAL_CLI_LAST_SUCCESSFUL_API'] = url
                                break
                            else:
                                # Om 404, försök vidare. Om annat fel, logga mer detaljerat.
                                if response.status_code != 404:
                                    error_messages.append(f"[{url}] Status {response.status_code}: {response.text}")
                        except httpx.RequestError as e:
                            # Ingen server kör här - fortsätt försöka med andra kombinationer
                            pass
                    
                    if success:
                        break  # Bryt yttre loopen när vi hittat en fungerande kombination
            
            if not success:
                console.error("Failed to connect to any API endpoint")
                if error_messages:  # Visa bara detaljerade fel om det finns några
                    console.error("Details:")
                    for error in error_messages[:3]:  # Begränsa till några få felmeddelanden
                        console.error(f" - {error}")
                console.info("Check that the GDial API server is running and PUBLIC_URL is correct.")
                console.info(f"Current PUBLIC_URL: {base_url}")
                
                if SIMULATION_MODE:
                    console.info("\nContinuing in simulation mode...")
                    simulated_id = str(uuid.uuid4())
                    simulated_result = {
                        "id": simulated_id,
                        "name": "Simulated Campaign (API unavailable)",
                        "status": "queued",
                        "target_contact_count": 1,
                        "queued_contact_count": 1,
                        "message_id": processed_message_id,
                        "created_at": datetime.now().isoformat()
                    }
                    console.success(f"SIMULATION: Call initiated successfully!")
                    console.info(f"Campaign ID: {simulated_id}")
                    return simulated_result
                return None
                    
                result = response.json()
                console.success(f"Call initiated successfully!")
                console.info(f"Campaign ID: {result['id']}")
                
                # Encourage user to check call status
                print()
                console.info("The call should be initiated shortly.")
                console.info("Use 'status' command to check call status once Twilio processes it.")
                return result
        except httpx.RequestError as e:
            console.error(f"Failed to reach GDial API: {e}")
            console.error("Check that the API server is running and PUBLIC_URL is correct.")
            return None
            
    except Exception as e:
        console.error(f"Error making TTS call: {e}")
        logger.exception("Detailed error information:")
        return None

async def make_realtime_ai_call(phone_number: str):
    """Make a realtime AI call using Twilio."""
    if not validate_phone_number(phone_number):
        console.error(f"Invalid phone number format: {phone_number}")
        console.info("Phone number should be in E.164 format (e.g., +1234567890)")
        return None
    
    # Check environment
    if not check_environment():
        return None
        
    # Get config from environment
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    from_number = os.environ.get("TWILIO_FROM_NUMBER")
    base_url = os.environ.get("PUBLIC_URL", "http://localhost:8000")
    
    # Show progress indicator
    console.section("Initiating Realtime AI Call")
    console.info(f"From: {from_number}")
    console.info(f"To: {phone_number}")
    console.info("Mode: Realtime AI Assistant")
    
    # Check if we're in simulation mode
    if SIMULATION_MODE:
        console.info("SIMULATION: Creating simulated AI call (no actual API calls)")
        simulated_id = str(uuid.uuid4())
        simulated_result = {
            "id": simulated_id,
            "name": "Simulated AI Campaign",
            "status": "queued",
            "target_contact_count": 1,
            "queued_contact_count": 1,
            "call_mode": "realtime_ai",
            "created_at": datetime.now().isoformat()
        }
        console.success(f"SIMULATION: AI Call initiated successfully!")
        console.info(f"Campaign ID: {simulated_id}")
        console.info("\nSIMULATION: This is a simulated call, no actual call will be made.")
        return simulated_result
        
    try:
        # Create a contact for this phone number
        console.info("Setting up contact for call...")
        contact_id = await create_contact(phone_number)
        if not contact_id:
            console.error("Could not create or find contact in database")
            contact_id = str(uuid.uuid4())  # Generate a temporary ID
            console.info(f"Using temporary contact ID: {contact_id}")
            
        # Initiate the call through outreach API
        console.info("Submitting AI call request to GDial API...")
        try:
            # Återanvänd senaste framgångsrika API-URL om möjligt
            cached_api = os.environ.get('GDIAL_CLI_LAST_SUCCESSFUL_API', None)
            
            # Annars använd samma URL-mappning som för TTS-samtal
            base_urls = [
                base_url.rstrip("/"),  # Utan trailing slash
                base_url,                # Original
                base_url.rstrip("/") + "/api",  # Med /api suffix
                "http://localhost:3003",  # Utvecklingsserver
                "http://127.0.0.1:3003"   # Alternativ lokal
            ]
            
            # Prioritera cachad API om den finns
            if cached_api:
                # Extrahera basURL från full URL
                from urllib.parse import urlparse
                parsed = urlparse(cached_api)
                cached_base = f"{parsed.scheme}://{parsed.netloc}"
                # Lägg till först i listan
                if cached_base not in base_urls:
                    base_urls.insert(0, cached_base)
            
            # Ta bort dubbletter
            base_urls = list(dict.fromkeys(base_urls))
            
            # Möjliga API-sökvägar
            possible_paths = [
                "/outreach/",           # Standard-endpoint
                "/api/outreach/",       # Med API-prefix
                "/v1/outreach/",        # Versionsprefix
                "/api/v1/outreach/"     # Kombinerad sökväg
            ]
            
            # Om vi har en komplett cachad URL-sökväg, använd den först
            if cached_api:
                from urllib.parse import urlparse
                parsed = urlparse(cached_api)
                cached_path = parsed.path
                # Se till att det finns i listan och är först
                if cached_path not in possible_paths:
                    possible_paths.insert(0, cached_path)
            
            payload = {
                "contact_ids": [str(contact_id)],
                "campaign_name": "CLI Test AI Call",
                "description": "Realtime AI test call initiated from CLI",
                "call_mode": "realtime_ai"
            }
            headers = {"Content-Type": "application/json"}
            
            response = None
            success = False
            error_messages = []
            successful_url = None
            
            async with httpx.AsyncClient() as client:
                # Om vi har en exakt cachad URL, försök med den först
                if cached_api:
                    try:
                        console.info(f"Trying cached API endpoint: {cached_api}")
                        response = await client.post(cached_api, json=payload, headers=headers, timeout=5.0)
                        
                        if response.status_code == 201 or response.status_code == 200:
                            console.success(f"Successfully connected to API endpoint: {cached_api}")
                            return response.json()
                    except:
                        console.info("Cached API endpoint failed, trying alternatives...")
                
                # Försök olika kombinationer av bas-URL och sökvägar
                for base in base_urls:
                    for path in possible_paths:
                        try:
                            url = f"{base}{path}"
                            console.info(f"Trying API endpoint: {url}")
                            
                            # Set reasonable timeout for API requests
                            response = await client.post(url, json=payload, headers=headers, timeout=5.0)
                            
                            if response.status_code == 201 or response.status_code == 200:
                                console.success(f"Successfully connected to API endpoint: {url}")
                                success = True
                                successful_url = url
                                # Spara lösningen för framtida användning
                                os.environ['GDIAL_CLI_LAST_SUCCESSFUL_API'] = url
                                break
                            else:
                                # Om 404, försök vidare. Om annat fel, logga mer detaljerat.
                                if response.status_code != 404:
                                    error_messages.append(f"[{url}] Status {response.status_code}: {response.text}")
                        except httpx.RequestError as e:
                            # Ingen server kör här - fortsätt försöka med andra kombinationer
                            pass
                    
                    if success:
                        break  # Bryt yttre loopen när vi hittat en fungerande kombination
            
            if not success:
                console.error("Failed to connect to any API endpoint")
                if error_messages:  # Visa bara detaljerade fel om det finns några
                    console.error("Details:")
                    for error in error_messages[:3]:  # Begränsa till några få felmeddelanden
                        console.error(f" - {error}")
                console.info("Check that the GDial API server is running and PUBLIC_URL is correct.")
                console.info(f"Current PUBLIC_URL: {base_url}")
                
                if SIMULATION_MODE:
                    console.info("\nContinuing in simulation mode...")
                    simulated_id = str(uuid.uuid4())
                    simulated_result = {
                        "id": simulated_id,
                        "name": "Simulated AI Campaign (API unavailable)",
                        "status": "queued",
                        "target_contact_count": 1,
                        "queued_contact_count": 1,
                        "call_mode": "realtime_ai",
                        "created_at": datetime.now().isoformat()
                    }
                    console.success(f"SIMULATION: AI Call initiated successfully!")
                    console.info(f"Campaign ID: {simulated_id}")
                    return simulated_result
                return None
                    
                result = response.json()
                console.success(f"AI call initiated successfully!")
                console.info(f"Campaign ID: {result['id']}")
                
                # Encourage user to check call status and provide explanatory info
                print()
                console.info("The AI call should be initiated shortly.")
                console.info("When the call connects, you'll be speaking with the OpenAI-powered assistant.")
                console.info("The conversation will be processed in real-time using the configured AI settings.")
                console.info("Use 'status' command to check call status once Twilio processes it.")
                return result
                
        except httpx.RequestError as e:
            console.error(f"Failed to reach GDial API: {e}")
            console.error("Check that the API server is running and PUBLIC_URL is correct.")
            return None
            
    except Exception as e:
        console.error(f"Error making realtime AI call: {e}")
        logger.exception("Detailed error information:")
        return None

async def check_call_status(call_sid: str, watch=False):
    """Check the status of a specific call.
    
    If watch=True, will continuously poll for updates until call ends.
    """
    try:
        if not call_sid:
            console.error("Call SID is required")
            return None
            
        # Clean up SID if needed (remove spaces, etc)
        call_sid = call_sid.strip()
        
        # Check environment
        if not check_environment():
            return None
            
        # Initialize variables for watch mode
        last_status = None
        start_time = time.time()
        poll_interval = 3  # seconds between polls

        # Get Twilio client
        client = get_twilio_client()
        
        # Function to fetch and display call status
        def display_status(call, call_log=None, first_check=False):
            if first_check or last_status != call.status:
                console.title(f"Call Status: {call_sid}")
                
                # Use colors for different statuses
                status_color = Fore.YELLOW
                if call.status in ["completed", "answered"]:
                    status_color = Fore.GREEN
                elif call.status in ["failed", "busy", "no-answer", "canceled"]:
                    status_color = Fore.RED
                elif call.status in ["in-progress", "ringing"]:
                    status_color = Fore.CYAN
                    
                status_display = f"{status_color}{call.status}{Style.RESET_ALL}" if HAS_COLOR else call.status
                console.info(f"Status: {status_display}")
                console.info(f"Direction: {call.direction}")
                console.info(f"From: {call.from_}")
                console.info(f"To: {call.to}")
                
                if call.duration and call.duration != "0":
                    console.info(f"Duration: {call.duration} seconds")
                
                if call.start_time:
                    console.info(f"Start Time: {call.start_time}")
                
                if call.end_time:
                    console.info(f"End Time: {call.end_time}")
                    
                if call.price:
                    console.info(f"Price: {call.price} {call.price_unit}")
            
                # Display additional details from our database if available
                if call_log:
                    console.section("Additional Call Details")
                    console.info(f"Campaign ID: {call_log.campaign_id}")
                    console.info(f"Contact ID: {call_log.contact_id}")
                    console.info(f"Answered: {call_log.answered}")
                    if call_log.duration:
                        console.info(f"Duration: {call_log.duration} seconds")
                    if call_log.error:
                        console.error(f"Error: {call_log.error}")
                
            return call.status
        
        # Initial check
        call = client.calls(call_sid).fetch()
        
        # Get additional details from our database if available
        session = get_db_session()
        call_log = None
        
        if session:
            from app.models import CallLog
            call_log_result = session.execute(
                select(CallLog).where(CallLog.sid == call_sid)
            ).first()
            if call_log_result:
                call_log = call_log_result[0]
        
        # Display initial status
        last_status = display_status(call, call_log, True)
        
        # If not watching, return after initial check
        if not watch:
            return call
            
        # In watch mode, continuously poll for updates
        console.info("\nWatching for call status updates (Ctrl+C to stop)...")
        try:
            while call.status not in ["completed", "failed", "busy", "no-answer", "canceled"]:
                time.sleep(poll_interval)
                call = client.calls(call_sid).fetch()
                
                # Update call log from database
                if session:
                    call_log_result = session.execute(
                        select(CallLog).where(CallLog.sid == call_sid)
                    ).first()
                    if call_log_result:
                        call_log = call_log_result[0]
                        
                last_status = display_status(call, call_log)
                
            # Call completed, show final status
            elapsed = time.time() - start_time
            console.success(f"Call finished with status: {call.status} (watched for {elapsed:.1f} seconds)")
            return call
        except KeyboardInterrupt:
            console.info("Status monitoring stopped by user.")
            return call
        
    except TwilioRestException as e:
        console.error(f"Twilio error checking call status: {e}")
        return None
    except Exception as e:
        console.error(f"Error checking call status: {e}")
        logger.exception("Detailed error information:")
        return None

# Interactive menu functions
async def interactive_menu():
    """Display an interactive menu for the user."""
    while True:
        console.title("GDial Call Tester - Interactive Mode")
        print("Choose an action:")
        
        # Format menu options with colors if available
        options = [
            ("1", "Make a TTS call"),
            ("2", "Make a Realtime AI call"),
            ("3", "Check call status"),
            ("4", "Watch call progress"),
            ("5", "List available messages"),
            ("q", "Quit")
        ]
        
        for key, desc in options:
            if HAS_COLOR:
                key_fmt = f"{Fore.GREEN}{key}{Style.RESET_ALL}"
                print(f"  {key_fmt}: {desc}")
            else:
                print(f"  {key}: {desc}")
                
        choice = input("\nEnter your choice: ").strip().lower()
        
        if choice == "1":
            await interactive_tts_call()
        elif choice == "2":
            await interactive_ai_call()
        elif choice == "3":
            await interactive_check_status(False)
        elif choice == "4":
            await interactive_check_status(True)
        elif choice == "5":
            await list_messages(interactive=True)
        elif choice == "q":
            console.info("Goodbye!")
            break
        else:
            console.error("Invalid choice. Please try again.")
        
        # Pause before showing menu again
        input("\nPress Enter to continue...")

async def interactive_tts_call():
    """Interactive interface for making a TTS call."""
    console.title("Make a TTS Call")
    
    # Ask for phone number
    while True:
        phone = input("Enter phone number (E.164 format, e.g., +1234567890): ").strip()
        if validate_phone_number(phone):
            break
        console.error("Invalid phone number format. Must start with + followed by digits.")
    
    # Ask for message source
    console.info("\nChoose message source:")
    options = [
        ("1", "Select from existing messages"),
        ("2", "Enter a new message"),
        ("3", "Go back")
    ]
    
    for key, desc in options:
        if HAS_COLOR:
            key_fmt = f"{Fore.GREEN}{key}{Style.RESET_ALL}"
            print(f"  {key_fmt}: {desc}")
        else:
            print(f"  {key}: {desc}")
    
    choice = input("\nEnter your choice: ").strip()
    
    message_id = None
    message_text = None
    
    if choice == "1":
        message = await list_messages(interactive=True)
        if message:
            message_id = str(message.id)
    elif choice == "2":
        message_text = input("\nEnter your message: ").strip()
        if not message_text:
            console.error("Message cannot be empty.")
            return
    elif choice == "3":
        return
    else:
        console.error("Invalid choice.")
        return
    
    # Make the call
    await make_tts_call(phone, message_id, message_text)

async def interactive_ai_call():
    """Interactive interface for making a realtime AI call."""
    console.title("Make a Realtime AI Call")
    
    # Ask for phone number
    while True:
        phone = input("Enter phone number (E.164 format, e.g., +1234567890): ").strip()
        if validate_phone_number(phone):
            break
        console.error("Invalid phone number format. Must start with + followed by digits.")
    
    # Display information about AI calls
    console.info("\nRealtime AI calls connect directly to an OpenAI-powered voice assistant.")
    console.info("The assistant will be able to hear and respond to the caller in real-time.")
    confirm = input("\nProceed with call? (y/n): ").strip().lower()
    
    if confirm == "y":
        await make_realtime_ai_call(phone)
    else:
        console.info("Call cancelled.")

async def interactive_check_status(watch_mode=False):
    """Interactive interface for checking call status."""
    mode = "Watch" if watch_mode else "Check"
    console.title(f"{mode} Call Status")
    
    call_sid = input("Enter Call SID: ").strip()
    if not call_sid:
        console.error("Call SID is required.")
        return
        
    await check_call_status(call_sid, watch=watch_mode)

async def main():
    """Main CLI entry point."""
    # Handle CLI arguments if provided, otherwise show interactive menu
    if len(sys.argv) > 1:
        # CLI mode - explicitly set non-interactive mode
        global SIMULATION_MODE
        os.environ["GDIAL_CLI_NONINTERACTIVE"] = "true"
        
        # For missing variables, automatically use simulation mode in CLI mode
        if not os.environ.get("SQLITE_DB"):
            console.warning("No database configuration found in CLI mode - automatically using simulation mode")
            SIMULATION_MODE = True
            os.environ["GDIAL_CLI_SIMULATION"] = "true"
        
        parser = argparse.ArgumentParser(description="GDial Call Testing Tool")
        
        # Create subparsers for different commands
        subparsers = parser.add_subparsers(dest="command", help="Command to run")
        
        # Call command
        call_parser = subparsers.add_parser("call", help="Make a test call")
        call_parser.add_argument("--mode", choices=["tts", "realtime_ai"], 
                                default="tts", help="Call mode")
        call_parser.add_argument("--phone", required=True, 
                               help="Phone number to call (E.164 format, e.g., +1234567890)")
        call_parser.add_argument("--message-id", help="Message ID for TTS mode")
        call_parser.add_argument("--message", help="Message text (will create temporary message)")
        call_parser.add_argument("--watch", action="store_true", help="Watch call progress until completion")
        
        # Status command
        status_parser = subparsers.add_parser("status", help="Check call status")
        status_parser.add_argument("call_sid", help="Call SID to check")
        status_parser.add_argument("--watch", action="store_true", help="Watch call progress until completion")
        
        # Messages command
        messages_parser = subparsers.add_parser("messages", help="List available messages")
        
        args = parser.parse_args()
        
        if not args.command:
            parser.print_help()
            return
            
        if args.command == "call":
            if args.mode == "tts" and not (args.message_id or args.message):
                call_parser.error("TTS mode requires either --message-id or --message")
                
            if args.mode == "tts":
                result = await make_tts_call(args.phone, args.message_id, args.message)
                if result and args.watch and "id" in result:
                    # Wait a bit for call to be initiated
                    console.info("Waiting for call to be initiated...")
                    time.sleep(5)
                    
                    # Try to find the call SID from the campaign
                    try:
                        session = get_db_session()
                        if session:
                            from app.models import CallLog
                            from sqlalchemy import desc
                            
                            # Look for calls associated with this campaign
                            campaign_id = result["id"]
                            call_log = session.execute(
                                select(CallLog).where(CallLog.campaign_id == campaign_id)
                                .order_by(desc(CallLog.created_at)).limit(1)
                            ).first()
                            
                            if call_log:
                                call_sid = call_log[0].sid
                                await check_call_status(call_sid, watch=True)
                    except Exception as e:
                        console.error(f"Could not find call SID for auto-watch: {e}")
            else:
                result = await make_realtime_ai_call(args.phone)
                
        elif args.command == "status":
            await check_call_status(args.call_sid, watch=args.watch)
            
        elif args.command == "messages":
            await list_messages()
    else:
        # Interactive mode
        console.title("GDial Call Testing Tool")
        console.info("Welcome to the GDial Call Testing Tool!")
        
        # Check environment first
        if not check_environment():
            console.error("\nPlease fix the missing environment variables before continuing.")
            sys.exit(1)
            
        await interactive_menu()

if __name__ == "__main__":
    asyncio.run(main())
