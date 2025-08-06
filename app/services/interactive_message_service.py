"""
Service för hantering av interaktiva meddelanden
"""
import uuid
import secrets
import string
from datetime import datetime, timedelta
from typing import List, Optional
from sqlmodel import Session, select

from app.models import (
    InteractiveMessage, InteractiveMessageOption, 
    InteractiveMessageRecipient, InteractiveMessageResponse,
    Contact
)
from app.schemas.interactive_messages import (
    InteractiveMessageCreate, InteractiveMessageResponse as InteractiveMessageResponseSchema,
    InteractiveMessageUpdate, InteractiveMessageListResponse
)


class InteractiveMessageService:
    """Service för hantering av interaktiva meddelanden"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def _generate_token(self, length: int = 32) -> str:
        """Generera en säker token för meddelandet"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    async def create_interactive_message(
        self, 
        message_data: InteractiveMessageCreate,
        user_id: Optional[uuid.UUID] = None
    ) -> InteractiveMessage:
        """Skapa ett nytt interaktivt meddelande"""
        
        # Generera unik token
        token = self._generate_token()
        while self.session.exec(select(InteractiveMessage).where(InteractiveMessage.token == token)).first():
            token = self._generate_token()
        
        # Skapa meddelandet
        message = InteractiveMessage(
            token=token,
            title=message_data.title,
            content=message_data.content,
            sender_name=message_data.sender_name,
            theme_color=message_data.theme_color,
            logo_url=message_data.logo_url,
            expires_at=message_data.expires_at,
            max_responses=message_data.max_responses,
            require_contact_info=message_data.require_contact_info
        )
        
        self.session.add(message)
        self.session.commit()
        self.session.refresh(message)
        
        # Skapa svarsalternativ
        for option_data in message_data.response_options:
            option = InteractiveMessageOption(
                message_id=message.id,
                option_key=option_data.option_key,
                display_text=option_data.display_text,
                button_color=option_data.button_color,
                sort_order=option_data.sort_order,
                requires_comment=option_data.requires_comment,
                auto_reply_message=option_data.auto_reply_message
            )
            self.session.add(option)
        
        # Skapa mottagare
        for contact_id in message_data.contact_ids:
            recipient = InteractiveMessageRecipient(
                message_id=message.id,
                contact_id=contact_id
            )
            self.session.add(recipient)
        
        self.session.commit()
        self.session.refresh(message)
        
        return message
    
    def get_interactive_message_by_token(self, token: str) -> Optional[InteractiveMessage]:
        """Hämta interaktivt meddelande via token"""
        return self.session.exec(
            select(InteractiveMessage).where(InteractiveMessage.token == token)
        ).first()
    
    def get_interactive_message_by_id(self, message_id: uuid.UUID) -> Optional[InteractiveMessage]:
        """Hämta interaktivt meddelande via ID"""
        return self.session.get(InteractiveMessage, message_id)
    
    def list_interactive_messages(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False
    ) -> InteractiveMessageListResponse:
        """Lista interaktiva meddelanden"""
        
        query = select(InteractiveMessage)
        
        if active_only:
            query = query.where(InteractiveMessage.is_active == True)
        
        # Räkna totalt
        total_count = len(self.session.exec(query).all())
        
        # Räkna aktiva
        active_count = len(self.session.exec(
            select(InteractiveMessage).where(InteractiveMessage.is_active == True)
        ).all())
        
        # Räkna utgångna
        expired_count = len(self.session.exec(
            select(InteractiveMessage).where(
                InteractiveMessage.expires_at < datetime.now()
            )
        ).all())
        
        # Hämta meddelanden med pagination
        messages = self.session.exec(
            query.order_by(InteractiveMessage.created_at.desc())
            .offset(skip)
            .limit(limit)
        ).all()
        
        return InteractiveMessageListResponse(
            messages=messages,
            total_count=total_count,
            active_count=active_count,
            expired_count=expired_count
        )
    
    def update_interactive_message(
        self,
        message_id: uuid.UUID,
        update_data: InteractiveMessageUpdate
    ) -> Optional[InteractiveMessage]:
        """Uppdatera interaktivt meddelande"""
        
        message = self.session.get(InteractiveMessage, message_id)
        if not message:
            return None
        
        # Uppdatera fält som är specificerade
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(message, field, value)
        
        self.session.commit()
        self.session.refresh(message)
        
        return message
    
    def deactivate_interactive_message(self, message_id: uuid.UUID) -> bool:
        """Deaktivera interaktivt meddelande"""
        
        message = self.session.get(InteractiveMessage, message_id)
        if not message:
            return False
        
        message.is_active = False
        self.session.commit()
        
        return True
    
    def record_message_view(self, token: str, contact_id: Optional[uuid.UUID] = None) -> bool:
        """Registrera att meddelandet har visats"""
        
        message = self.get_interactive_message_by_token(token)
        if not message:
            return False
        
        # Hitta mottagaren
        recipient_query = select(InteractiveMessageRecipient).where(
            InteractiveMessageRecipient.message_id == message.id
        )
        
        if contact_id:
            recipient_query = recipient_query.where(
                InteractiveMessageRecipient.contact_id == contact_id
            )
        
        recipient = self.session.exec(recipient_query).first()
        if recipient and not recipient.viewed_at:
            recipient.viewed_at = datetime.now()
            self.session.commit()
        
        return True
    
    def submit_response(
        self,
        token: str,
        option_key: str,
        contact_name: Optional[str] = None,
        contact_phone: Optional[str] = None,
        contact_email: Optional[str] = None,
        user_comment: Optional[str] = None,
        contact_id: Optional[uuid.UUID] = None
    ) -> Optional[InteractiveMessageResponse]:
        """Skicka in svar på interaktivt meddelande"""
        
        message = self.get_interactive_message_by_token(token)
        if not message or not message.is_active:
            return None
        
        # Kontrollera om meddelandet har gått ut
        if message.expires_at and message.expires_at < datetime.now():
            return None
        
        # Hitta svarsalternativet
        option = self.session.exec(
            select(InteractiveMessageOption).where(
                InteractiveMessageOption.message_id == message.id,
                InteractiveMessageOption.option_key == option_key
            )
        ).first()
        
        if not option:
            return None
        
        # Hitta mottagaren
        recipient_query = select(InteractiveMessageRecipient).where(
            InteractiveMessageRecipient.message_id == message.id
        )
        
        if contact_id:
            recipient_query = recipient_query.where(
                InteractiveMessageRecipient.contact_id == contact_id
            )
        
        recipient = self.session.exec(recipient_query).first()
        if not recipient:
            return None
        
        # Kontrollera max antal svar
        if recipient.response_count >= message.max_responses:
            return None
        
        # Skapa svaret
        response = InteractiveMessageResponse(
            message_id=message.id,
            recipient_id=recipient.id,
            option_id=option.id,
            contact_name=contact_name,
            contact_phone=contact_phone,
            contact_email=contact_email,
            user_comment=user_comment
        )
        
        self.session.add(response)
        
        # Uppdatera mottagaren
        recipient.responded_at = datetime.now()
        recipient.response_count += 1
        
        self.session.commit()
        self.session.refresh(response)
        
        return response
    
    def get_message_responses(self, message_id: uuid.UUID) -> List[InteractiveMessageResponse]:
        """Hämta alla svar för ett meddelande"""
        
        return self.session.exec(
            select(InteractiveMessageResponse)
            .where(InteractiveMessageResponse.message_id == message_id)
            .order_by(InteractiveMessageResponse.responded_at.desc())
        ).all()
    
    def get_message_statistics(self, message_id: uuid.UUID) -> dict:
        """Hämta statistik för ett meddelande"""
        
        message = self.session.get(InteractiveMessage, message_id)
        if not message:
            return {}
        
        # Räkna mottagare
        total_recipients = len(self.session.exec(
            select(InteractiveMessageRecipient)
            .where(InteractiveMessageRecipient.message_id == message_id)
        ).all())
        
        # Räkna visningar
        viewed_count = len(self.session.exec(
            select(InteractiveMessageRecipient)
            .where(
                InteractiveMessageRecipient.message_id == message_id,
                InteractiveMessageRecipient.viewed_at.is_not(None)
            )
        ).all())
        
        # Räkna svar
        response_count = len(self.session.exec(
            select(InteractiveMessageResponse)
            .where(InteractiveMessageResponse.message_id == message_id)
        ).all())
        
        # Räkna unika svarare
        unique_responders = len(self.session.exec(
            select(InteractiveMessageRecipient)
            .where(
                InteractiveMessageRecipient.message_id == message_id,
                InteractiveMessageRecipient.responded_at.is_not(None)
            )
        ).all())
        
        return {
            "total_recipients": total_recipients,
            "viewed_count": viewed_count,
            "view_rate": viewed_count / total_recipients if total_recipients > 0 else 0,
            "response_count": response_count,
            "unique_responders": unique_responders,
            "response_rate": unique_responders / total_recipients if total_recipients > 0 else 0
        }
    
    def cleanup_expired_messages(self) -> int:
        """Rensa upp utgångna meddelanden"""
        
        expired_messages = self.session.exec(
            select(InteractiveMessage).where(
                InteractiveMessage.expires_at < datetime.now(),
                InteractiveMessage.is_active == True
            )
        ).all()
        
        count = 0
        for message in expired_messages:
            message.is_active = False
            count += 1
        
        if count > 0:
            self.session.commit()
        
        return count
