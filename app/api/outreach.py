import uuid
from typing import List, Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlmodel import Session

from app.database import get_session
from app.dependencies import get_outreach_service
from ..models import OutreachCampaign # For the response model
from ..schemas import OutreachCampaignResponse # Assuming a response schema exists or define one
from ..logger import logger
from datetime import datetime
# from ..api.auth import get_current_active_user # If auth is needed
# from ..models import User # If using auth

router = APIRouter(
    prefix="/outreach",
    tags=["outreach"],
    # dependencies=[Depends(get_current_active_user)], # Uncomment if auth required
)

# --- Request Body Schema ---
class OutreachRequest(BaseModel):
    message_id: Optional[uuid.UUID] = None
    group_id: Optional[uuid.UUID] = None
    contact_ids: Optional[List[uuid.UUID]] = None
    campaign_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    call_mode: Literal["tts", "audio_file"] = Field(
        default="tts",
        description=(
            "Specifies the mode for outgoing calls. "
            "'tts': Use Text-to-Speech based on the message_id. "
            "'audio_file': Play a pre-recorded audio file (requires message_id with audio)."
        )
    )

    @field_validator('message_id')
    @classmethod
    def validate_message_id(cls, v: Optional[uuid.UUID]) -> Optional[uuid.UUID]:
        """Validate that message_id is provided."""
        if v is None:
            raise ValueError("message_id is required")
        return v

    @model_validator(mode='after')
    def check_group_or_contacts(self) -> 'OutreachRequest':
        """Validate that exactly one of group_id or contact_ids is provided."""
        group_id = self.group_id
        contact_ids = self.contact_ids
        if not (bool(group_id) ^ bool(contact_ids)):
            raise ValueError('Must provide exactly one of group_id or contact_ids')
        return self

# --- Response Schema (Example - Adapt as needed) ---
# You might reuse OutreachCampaign or create a specific response schema
# from ..schemas import OutreachCampaignResponse
class OutreachCampaignCreateResponse(BaseModel):
    id: uuid.UUID
    name: Optional[str]
    status: str
    target_contact_count: int
    queued_contact_count: int
    message_id: uuid.UUID
    target_group_id: Optional[uuid.UUID]
    created_at: datetime

# --- API Endpoint --- 
@router.post("/", response_model=OutreachCampaignCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def initiate_outreach_campaign(
    request_data: OutreachRequest,
    outreach_service = Depends(get_outreach_service),
    # current_user: User = Depends(get_current_active_user) # Uncomment if auth required
):
    """Initiate an outreach campaign involving calls and potentially SMS.

    This endpoint starts a campaign targeting a specified group or list of contacts.
    The nature of the outgoing call is determined by the `call_mode` parameter:

    - **tts**: Synthesizes speech from the text associated with `message_id`.
    - **audio_file**: Plays a pre-recorded audio file associated with `message_id`.


    The campaign details and target contacts are queued for processing.
    Returns the details of the created campaign upon successful queuing.
    """
    logger.info(f"Received request to initiate outreach campaign: {request_data.campaign_name or 'Unnamed'}")

    # Use injected outreach service with new architecture

    try:
        # user_id = current_user.id # Uncomment if auth required
        user_id = None # Placeholder
        
        # Pass the call_mode to the outreach service
        campaign = await outreach_service.initiate_outreach(
            message_id=request_data.message_id,
            group_id=request_data.group_id,
            contact_ids=request_data.contact_ids,
            campaign_name=request_data.campaign_name,
            description=request_data.description,
            user_id=user_id,
            call_mode=request_data.call_mode
        )
        
        logger.info(f"Successfully initiated outreach campaign ID: {campaign.id}, Status: {campaign.status}")
        # Return a tailored response
        return OutreachCampaignCreateResponse(
            id=campaign.id,
            name=campaign.name,
            status=campaign.status,
            target_contact_count=campaign.target_contact_count,
            queued_contact_count=campaign.queued_contact_count,
            message_id=campaign.message_id,
            target_group_id=campaign.target_group_id,
            created_at=campaign.created_at
        )

    except ValueError as ve:
        logger.warning(f"Validation error initiating outreach: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Error initiating outreach campaign: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate outreach campaign"
        )
