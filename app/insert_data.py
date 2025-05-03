import uuid
import logging
from datetime import datetime
from sqlmodel import select
from .models import Message, Contact, PhoneNumber, ContactGroup, GroupContactLink, DtmfResponse

def insert_initial_data():
    """Insert initial data into the database"""
    # Import here to avoid circular dependencies
    from .database import get_session
    
    db = next(get_session())
    
    # Check if we already have data
    existing_contacts = db.exec(select(Contact)).all()
    existing_messages = db.exec(select(Message)).all()
    existing_groups = db.exec(select(ContactGroup)).all()
    existing_dtmf_responses = db.exec(select(DtmfResponse)).all()
    
    if existing_contacts and existing_messages and existing_groups:
        logging.info("Database already contains data, skipping initialization.")
        
        # Only add DTMF responses if they don't exist
        if not existing_dtmf_responses:
            logging.info("Adding default DTMF responses")
            add_default_dtmf_responses(db)
        return
        
    # Add default DTMF responses
    add_default_dtmf_responses(db)
    
    # Add default emergency message
    default_message = Message(
        name="Standard Emergency Alert",
        content="This is an emergency notification. The building must be evacuated immediately. Please follow the emergency procedures and proceed to the assembly point. Press 1 to confirm you have received this message. Press 2 if you need assistance. Press 3 for emergency services.",
        is_template=True,
        message_type="voice",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(default_message)
    
    # Add a fire evacuation message
    fire_message = Message(
        name="Fire Evacuation Alert",
        content="IMPORTANT: A fire has been reported in the building. Please evacuate immediately using the nearest fire exit. Do not use elevators. Proceed to your designated assembly point. Press 1 to confirm receipt of this message. Press 2 if you need assistance.",
        is_template=True,
        message_type="voice",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(fire_message)
    
    # Add a severe weather message
    weather_message = Message(
        name="Severe Weather Alert",
        content="A severe weather warning has been issued for our area. Please remain indoors and away from windows. Secure loose objects and be prepared for possible power outages. Press 1 to confirm receipt of this message. Press 2 if you need assistance.",
        is_template=True,
        message_type="voice",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(weather_message)
    
    # Add test message
    test_message = Message(
        name="Test Message - DO NOT RESPOND",
        content="This is a test of the emergency notification system. No action is required. Please press 1 to confirm you have received this test message.",
        is_template=True,
        message_type="voice",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(test_message)
    
    # Add SMS messages
    sms_alert = Message(
        name="Emergency SMS Alert",
        content="EMERGENCY ALERT: This is an important notification. Please check your email or voicemail for more details.",
        is_template=True,
        message_type="sms",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(sms_alert)
    
    sms_test = Message(
        name="SMS Test Message",
        content="This is a test of the emergency SMS notification system. No action is required.",
        is_template=True,
        message_type="sms",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(sms_test)
    
    both_alert = Message(
        name="Combined Alert (Voice + SMS)",
        content="EMERGENCY: Please evacuate the building immediately and proceed to the designated assembly area. This message is being sent via multiple channels.",
        is_template=True,
        message_type="both",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(both_alert)
    
    # Add sample contact groups
    emergency_group = ContactGroup(
        name="Emergency Response Team",
        description="Personnel trained to respond to emergency situations"
    )
    db.add(emergency_group)
    
    management_group = ContactGroup(
        name="Management Team",
        description="Senior management personnel to be notified in emergencies"
    )
    db.add(management_group)
    
    all_staff_group = ContactGroup(
        name="All Staff",
        description="All staff members"
    )
    db.add(all_staff_group)
    
    # Commit to get IDs
    db.commit()
    
    # Add sample contacts (with fake phone numbers)
    contacts = [
        {
            "name": "John Smith",
            "email": "john.smith@example.com",
            "notes": "First aid trained",
            "phones": [
                {"number": "+46701234567", "priority": 1},
                {"number": "+46701234568", "priority": 2}
            ],
            "groups": [emergency_group.id, all_staff_group.id]
        },
        {
            "name": "Maria Garcia",
            "email": "maria.garcia@example.com",
            "notes": "Fire warden",
            "phones": [
                {"number": "+46701234569", "priority": 1}
            ],
            "groups": [emergency_group.id, all_staff_group.id]
        },
        {
            "name": "Alex Johnson",
            "email": "alex.johnson@example.com",
            "notes": "CEO",
            "phones": [
                {"number": "+46701234570", "priority": 1},
                {"number": "+46701234571", "priority": 2}
            ],
            "groups": [management_group.id, all_staff_group.id]
        },
        {
            "name": "Oscar Delerud",
            "email": "oscar@example.com",
            "notes": "Test user",
            "phones": [
                {"number": "+46105597506", "priority": 1}
            ],
            "groups": [all_staff_group.id]
        }
    ]
    
    for contact_data in contacts:
        contact = Contact(
            name=contact_data["name"],
            email=contact_data["email"],
            notes=contact_data["notes"]
        )
        db.add(contact)
        db.commit()
        
        # Add phone numbers
        for phone_data in contact_data["phones"]:
            phone = PhoneNumber(
                contact_id=contact.id,
                number=phone_data["number"],
                priority=phone_data["priority"]
            )
            db.add(phone)
        
        # Add to groups
        for group_id in contact_data["groups"]:
            link = GroupContactLink(
                group_id=group_id,
                contact_id=contact.id
            )
            db.add(link)
    
    db.commit()
    
    logging.info("Initial data inserted successfully!")

def add_default_dtmf_responses(db):
    """Add default DTMF response messages"""
    default_responses = [
        {
            "digit": "1",
            "description": "Confirm receipt",
            "response_message": "Thank you for confirming receipt of this message. You pressed 1. Goodbye."
        },
        {
            "digit": "2",
            "description": "Need assistance",
            "response_message": "Thank you. Your request for assistance has been recorded. You pressed 2. Someone will contact you shortly."
        },
        {
            "digit": "3",
            "description": "Emergency services",
            "response_message": "Emergency services have been notified. You pressed 3. Please remain on the line if possible."
        }
    ]
    
    for response_data in default_responses:
        response = DtmfResponse(
            digit=response_data["digit"],
            description=response_data["description"],
            response_message=response_data["response_message"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.add(response)
    
    db.commit()
    logging.info("Default DTMF responses added successfully")

if __name__ == "__main__":
    from .database import create_db_and_tables
    create_db_and_tables()
    insert_initial_data()
