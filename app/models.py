import uuid
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, Relationship

class PhoneNumber(SQLModel, table=True):
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    contact_id: uuid.UUID = Field(foreign_key="contact.id")
    number: str
    priority: int
    contact: "Contact" = Relationship(back_populates="phone_numbers")

class Contact(SQLModel, table=True):
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    phone_numbers: list[PhoneNumber] = Relationship(back_populates="contact")

class CallLog(SQLModel, table=True):
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    contact_id: uuid.UUID = Field(foreign_key="contact.id")
    phone_number_id: uuid.UUID = Field(foreign_key="phonenumber.id")
    call_sid: str
    started_at: datetime
    answered: bool = False
    digits: Optional[str] = Field(default=None, max_length=1)
    status: str  # initiated | completed | no-answer | manual | error
