from typing import List, Optional
from datetime import datetime
from uuid import UUID as UUID4
from pydantic import BaseModel

class OutreachCampaignResponse(BaseModel):
    id: UUID4
    name: str
    description: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    # Lägg till fler fält om det behövs för din domän
