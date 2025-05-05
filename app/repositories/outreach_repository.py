import uuid
from typing import Optional

from sqlmodel import Session, select

from ..models import OutreachCampaign
from ..logger import logger

class OutreachRepository:
    """Repository for database operations related to OutreachCampaigns."""

    def __init__(self, session: Session):
        self.session = session

    def create_campaign(self, campaign: OutreachCampaign) -> OutreachCampaign:
        """Adds a new OutreachCampaign record to the database."""
        logger.info(f"Creating OutreachCampaign: {campaign.name or campaign.id}")
        self.session.add(campaign)
        self.session.commit()
        self.session.refresh(campaign)
        logger.info(f"Created OutreachCampaign with ID: {campaign.id}")
        return campaign

    def get_campaign_by_id(self, campaign_id: uuid.UUID) -> Optional[OutreachCampaign]:
        """Retrieves an OutreachCampaign by its ID."""
        logger.debug(f"Fetching OutreachCampaign with ID: {campaign_id}")
        return self.session.get(OutreachCampaign, campaign_id)

    def update_campaign(self, campaign: OutreachCampaign) -> OutreachCampaign:
        """Updates an existing OutreachCampaign record."""
        logger.info(f"Updating OutreachCampaign ID: {campaign.id}, Status: {campaign.status}, Queued: {campaign.queued_contact_count}")
        self.session.add(campaign) # Add manages updates if the object is tracked
        self.session.commit()
        self.session.refresh(campaign)
        logger.info(f"Updated OutreachCampaign ID: {campaign.id}")
        return campaign

    # Additional methods like update_status, update_counts could be added for specific updates
