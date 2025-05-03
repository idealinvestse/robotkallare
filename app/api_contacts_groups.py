"""API endpoints for contacts and groups."""
import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select

from app.database import get_session
from app.models import Contact, ContactGroup

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["contacts-groups"])

@router.get("/api/contacts")
async def get_contacts(db: Session = Depends(get_session)):
    """Get all contacts."""
    contacts = db.exec(select(Contact)).all()
    return contacts

@router.get("/api/groups")
async def get_groups(db: Session = Depends(get_session)):
    """Get all contact groups."""
    groups = db.exec(select(ContactGroup)).all()
    return groups