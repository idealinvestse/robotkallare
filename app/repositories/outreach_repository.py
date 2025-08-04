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

    def get_all_campaigns(self, active_only: bool = True) -> list[OutreachCampaign]:
        """Get all outreach campaigns, optionally filtered by active status."""
        try:
            statement = select(OutreachCampaign)
            if active_only:
                statement = statement.where(OutreachCampaign.active == True)
            return list(self.session.exec(statement).all())
        except Exception as e:
            logger.error(f"Error fetching all campaigns: {e}")
            return []

    def get_campaigns_by_status(self, status: str) -> list[OutreachCampaign]:
        """Get campaigns by status."""
        try:
            statement = select(OutreachCampaign).where(OutreachCampaign.status == status)
            return list(self.session.exec(statement).all())
        except Exception as e:
            logger.error(f"Error fetching campaigns by status {status}: {e}")
            return []

    def delete_campaign(self, campaign_id: uuid.UUID) -> bool:
        """Soft delete a campaign by setting active=False."""
        try:
            campaign = self.get_campaign_by_id(campaign_id)
            if campaign:
                campaign.active = False
                self.session.add(campaign)
                self.session.commit()
                logger.info(f"Soft deleted campaign: {campaign.name} ({campaign_id})")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting campaign {campaign_id}: {e}")
            self.session.rollback()
            return False

    def update_campaign_status(self, campaign_id: uuid.UUID, status: str) -> bool:
        """Update campaign status."""
        try:
            campaign = self.get_campaign_by_id(campaign_id)
            if campaign:
                campaign.status = status
                self.session.add(campaign)
                self.session.commit()
                logger.info(f"Updated campaign {campaign_id} status to {status}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating campaign {campaign_id} status: {e}")
            self.session.rollback()
            return False

    def update_campaign_counts(self, campaign_id: uuid.UUID, queued_count: int = None, 
                             sent_count: int = None, failed_count: int = None) -> bool:
        """Update campaign contact counts."""
        try:
            campaign = self.get_campaign_by_id(campaign_id)
            if campaign:
                if queued_count is not None:
                    campaign.queued_contact_count = queued_count
                if sent_count is not None:
                    campaign.sent_contact_count = sent_count
                if failed_count is not None:
                    campaign.failed_contact_count = failed_count
                
                self.session.add(campaign)
                self.session.commit()
                logger.info(f"Updated campaign {campaign_id} counts")
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating campaign {campaign_id} counts: {e}")
            self.session.rollback()
            return False
