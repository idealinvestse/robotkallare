from typing import List, Optional
from datetime import datetime
from uuid import UUID as UUID4
from pydantic import BaseModel

from .core import MessageResponse, GroupBrief, CallLogResponse

class CallRunCreate(BaseModel):
    """Schema for creating a new call run"""
    name: str
    description: Optional[str] = None
    message_id: Optional[UUID4] = None
    group_id: Optional[UUID4] = None
    contacts: Optional[List[UUID4]] = None

class CallRunUpdate(BaseModel):
    """Schema for updating a call run"""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class CallRunResponse(BaseModel):
    """Schema for call run information in API responses"""
    id: UUID4
    name: str
    description: Optional[str] = None
    message_id: Optional[UUID4] = None
    group_id: Optional[UUID4] = None
    status: str
    total_calls: int
    completed_calls: int
    answered_calls: int
    started_at: datetime
    completed_at: Optional[datetime] = None

class CallRunDetailResponse(CallRunResponse):
    """Schema for detailed call run information, including associated calls"""
    message: Optional[MessageResponse] = None
    group: Optional[GroupBrief] = None
    calls: List[CallLogResponse] = []