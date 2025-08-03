import uuid
from datetime import datetime
from typing import List, Optional

from sqlmodel import Session

# Assuming these repositories exist or will be created
from app.repositories.contact_repository import ContactRepository
from app.repositories.group_repository import GroupRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.outreach_repository import OutreachRepository # Now using the repository

# Models
from app.models import Contact, ContactGroup, Message, OutreachCampaign, PhoneNumber # User

# Queue mechanism
from app.publisher import QueuePublisher # Changed import source
from app.logger import logger # Assuming a logger setup

class OutreachService:
    def __init__(
        self, 
        session: Session, 
        contact_repo: ContactRepository,
        group_repo: GroupRepository,
        outreach_repo: OutreachRepository,
        call_orchestration_service=None,
        queue_publisher=None
    ):
        """Initialize OutreachService with dependency injection.
        
        Args:
            session: Database session
            contact_repo: Contact repository
            group_repo: Group repository  
            outreach_repo: Outreach repository
            call_orchestration_service: Call orchestration service
            queue_publisher: Queue publisher for background tasks
        """
        self.session = session
        self.contact_repo = contact_repo
        self.group_repo = group_repo
        self.message_repo = MessageRepository(session)
        self.outreach_repo = outreach_repo
        self.queue_publisher = queue_publisher
        
        # Import here to avoid circular imports
        if call_orchestration_service is None:
            from app.services.call_orchestration_service import CallOrchestrationService
            self.call_orchestration_service = CallOrchestrationService(session)
        else:
            self.call_orchestration_service = call_orchestration_service
        
        logger.info("OutreachService initialized with new architecture.")

    async def initiate_outreach(
        self,
        *, # Enforce keyword arguments
        message_id: Optional[uuid.UUID] = None,
        group_id: Optional[uuid.UUID] = None,
        contact_ids: Optional[List[uuid.UUID]] = None,
        campaign_name: Optional[str] = None,
        description: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None, # Assuming User model and auth integration
        call_mode: str = "tts" # Default to TTS for backward compatibility
    ) -> OutreachCampaign:
        """Initiates a combined Call + SMS outreach campaign.

        Validates inputs, retrieves contacts, creates a campaign record,
        and publishes individual outreach jobs to a queue.
        """
        logger.info(f"Initiating outreach campaign '{campaign_name or 'Unnamed'}' with message ID {message_id}")

        # --- 1. Validation ---
        if not (bool(group_id) ^ bool(contact_ids)):
            raise ValueError("Either group_id or contact_ids must be provided")

        # Message validation depends on call mode
        message = None
        if call_mode != "realtime_ai":
            # Non-realtime modes require a valid message
            if not message_id:
                raise ValueError("message_id is required unless call_mode is realtime_ai")
                
            message = self.message_repo.get_message_by_id(message_id)
            if not message:
                raise ValueError(f"Message with ID {message_id} not found")

        # --- 2. Retrieve Contacts ---
        contacts_to_reach: List[Contact] = []
        target_group: Optional[ContactGroup] = None
        if group_id:
            contacts_to_reach = self.group_repo.get_contacts_by_group_id(group_id)
            if not contacts_to_reach:
                raise ValueError(f"Group with ID {group_id} not found or has no contacts")
            logger.info(f"Targeting group with ID {group_id} with {len(contacts_to_reach)} contacts.")
        elif contact_ids:
            contacts_to_reach = self.contact_repo.get_contacts_by_ids(contact_ids)
            if len(contacts_to_reach) != len(contact_ids):
                # Handle partial matches if necessary, for now require all contacts found
                found_ids = {c.id for c in contacts_to_reach}
                missing_ids = [cid for cid in contact_ids if cid not in found_ids]
                logger.warning(f"Could not find all specified contacts. Missing: {missing_ids}")
                raise ValueError(f"Could not find all contacts: {missing_ids}")
            logger.info(f"Targeting {len(contacts_to_reach)} specific contacts.")

        if not contacts_to_reach:
            logger.warning("No contacts found for the specified target. Cannot initiate outreach.")
            # Depending on requirements, could return an empty campaign or raise error
            raise ValueError("No contacts found for outreach")

        # Filter contacts without phone numbers (optional, depending on requirements)
        valid_contacts = [c for c in contacts_to_reach if c.phone_numbers]
        if len(valid_contacts) < len(contacts_to_reach):
            logger.warning(f"{len(contacts_to_reach) - len(valid_contacts)} contacts skipped due to missing phone numbers.")
        if not valid_contacts:
            raise ValueError("No contacts with phone numbers found for outreach")

        # --- 3. Create Campaign Record ---
        campaign = OutreachCampaign(
            name=campaign_name or f"Campaign {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            description=description,
            message_id=message_id,  # For realtime_ai, this will be None
            target_group_id=group_id,
            target_contact_count=len(valid_contacts), # Base count on contacts we will actually queue
            queued_contact_count=0,
            status="pending",
            initiated_by_user_id=user_id # Pass if available
        )
        # Persist the initial campaign record using the repository
        campaign = self.outreach_repo.create_campaign(campaign)

        # --- 4. Process Contacts Based on Call Mode ---
        queued_count = 0
        publish_errors = 0
        
        # Import here to avoid circular imports
        from app.services.call_service import CallService
        call_service = CallService(self.session)
        
        for contact in valid_contacts:
            try:
                if call_mode == "tts":
                    # Use CallOrchestrationService for TTS calls
                    result = await self.call_orchestration_service.dial_contacts(
                        contact_ids=[contact.id],
                        message_id=message_id,
                        call_run_name=f"Campaign {campaign.id} - {contact.name}",
                        call_run_description=f"TTS call for campaign {campaign.id}"
                    )
                    if result.success:
                        logger.info(f"Initiated TTS call to {contact.name}")
                        queued_count += 1
                    else:
                        logger.error(f"Failed TTS call to {contact.name}: {result.errors}")
                        
                elif call_mode == "custom":
                    # For custom calls, we need custom message content
                    # This would typically come from the campaign or be generated
                    custom_message = f"Custom message for campaign {campaign.id}"
                    
                    result = await self.call_orchestration_service.make_custom_call(
                        contact_id=contact.id,
                        message_content=custom_message,
                        save_as_template=False,
                        call_run_id=None  # Could link to campaign if needed
                    )
                    
                    if result.success:
                        logger.info(f"Initiated custom call to {contact.name}")
                        queued_count += 1
                    else:
                        logger.error(f"Failed custom call to {contact.name}: {result.errors}")
                else:
                    # For other call modes, use direct orchestration
                    result = await self.call_orchestration_service.dial_contacts(
                        contact_ids=[contact.id],
                        message_id=message_id,
                        call_run_name=f"Campaign {campaign.id} - {contact.name}",
                        call_run_description=f"{call_mode} call for campaign {campaign.id}"
                    )
                    
                    if result.success:
                        logger.info(f"Initiated {call_mode} call to {contact.name}")
                        queued_count += 1
                    else:
                        logger.error(f"Failed {call_mode} call to {contact.name}: {result.errors}")
            except Exception as e:
                publish_errors += 1
                logger.error(f"Failed to process contact {contact.id}: {e}", exc_info=True)

        # --- 5. Update Campaign Status & Counts ---
        campaign.queued_contact_count = queued_count
        if queued_count == 0 and campaign.target_contact_count > 0:
            campaign.status = "failed"
            campaign.completed_at = datetime.now() # Mark as completed if failed immediately
            logger.error(f"Outreach campaign {campaign.id} failed: 0 jobs queued.")
        elif publish_errors > 0:
            campaign.status = "partial_failure" # Or another status indicating issues
            logger.warning(f"Outreach campaign {campaign.id} had {publish_errors} job publishing errors.")
        elif queued_count == campaign.target_contact_count:
            campaign.status = "queued"
            logger.info(f"Outreach campaign {campaign.id} fully queued with {queued_count} jobs.")
        else:
            # This case might occur if valid_contacts changed mid-loop?
            campaign.status = "unknown_state"
            logger.error(f"Outreach campaign {campaign.id} ended in unexpected state.")

        # Update the campaign record in the database
        updated_campaign = self.outreach_repo.update_campaign(campaign)

        # --- 6. Return --- 
        return updated_campaign
