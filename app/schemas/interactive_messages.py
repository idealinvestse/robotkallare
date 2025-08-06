"""
Pydantic schemas för interaktiva meddelanden
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
import uuid


class InteractiveMessageOptionCreate(BaseModel):
    """Schema för att skapa ett svarsalternativ"""
    option_key: str = Field(..., description="Unik nyckel för alternativet")
    display_text: str = Field(..., description="Text som visas för användaren")
    button_color: str = Field(default="#3B82F6", description="Färg på knappen")
    sort_order: int = Field(default=1, description="Sorteringsordning")
    requires_comment: bool = Field(default=False, description="Kräver kommentar från användaren")
    auto_reply_message: Optional[str] = Field(None, description="Automatiskt svarmeddelande")


class InteractiveMessageOptionResponse(BaseModel):
    """Schema för svarsalternativ i respons"""
    id: uuid.UUID
    option_key: str
    display_text: str
    button_color: str
    sort_order: int
    requires_comment: bool
    auto_reply_message: Optional[str]

    class Config:
        from_attributes = True


class InteractiveMessageCreate(BaseModel):
    """Schema för att skapa ett interaktivt meddelande"""
    title: str = Field(..., description="Titel på meddelandet")
    content: str = Field(..., description="Innehåll i meddelandet")
    sender_name: Optional[str] = Field(None, description="Namn på avsändaren")
    theme_color: str = Field(default="#3B82F6", description="Temafärg")
    logo_url: Optional[str] = Field(None, description="URL till logotyp")
    expires_at: Optional[datetime] = Field(None, description="När meddelandet upphör att gälla")
    max_responses: int = Field(default=1, description="Max antal svar per mottagare")
    require_contact_info: bool = Field(default=False, description="Kräv kontaktinformation")
    contact_ids: List[uuid.UUID] = Field(default_factory=list, description="Lista med kontakt-ID:n")
    response_options: List[InteractiveMessageOptionCreate] = Field(
        default_factory=list, 
        description="Svarsalternativ"
    )


class InteractiveMessageResponse(BaseModel):
    """Schema för interaktivt meddelande i respons"""
    id: uuid.UUID
    token: str
    title: str
    content: str
    sender_name: Optional[str]
    theme_color: str
    logo_url: Optional[str]
    expires_at: Optional[datetime]
    max_responses: int
    require_contact_info: bool
    created_at: datetime
    is_active: bool
    response_options: List[InteractiveMessageOptionResponse]

    class Config:
        from_attributes = True


class InteractiveMessageRecipientResponse(BaseModel):
    """Schema för mottagare av interaktivt meddelande"""
    id: uuid.UUID
    contact_id: uuid.UUID
    sent_at: Optional[datetime]
    viewed_at: Optional[datetime]
    responded_at: Optional[datetime]
    response_count: int

    class Config:
        from_attributes = True


class InteractiveMessageUserResponse(BaseModel):
    """Schema för användarsvar på interaktivt meddelande"""
    id: uuid.UUID
    option_key: str
    contact_name: Optional[str]
    contact_phone: Optional[str]
    contact_email: Optional[str]
    user_comment: Optional[str]
    responded_at: datetime

    class Config:
        from_attributes = True


class InteractiveMessageUpdate(BaseModel):
    """Schema för att uppdatera ett interaktivt meddelande"""
    title: Optional[str] = None
    content: Optional[str] = None
    sender_name: Optional[str] = None
    theme_color: Optional[str] = None
    logo_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None


class InteractiveMessageListResponse(BaseModel):
    """Schema för lista av interaktiva meddelanden"""
    messages: List[InteractiveMessageResponse]
    total_count: int
    active_count: int
    expired_count: int
