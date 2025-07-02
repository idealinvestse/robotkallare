"""Fix all relationship definitions in models.py"""
import re

def fix_relationships():
    with open('app/models.py', 'r') as file:
        content = file.read()
    
    # 1. Fix the Contact-OutreachCampaign relationship
    content = content.replace(
        'outreach_campaigns: List["OutreachCampaign"] = Relationship(back_populates="message")',
        'outreach_campaigns: List["OutreachCampaign"] = Relationship(\n        back_populates="contacts",\n        link_model=OutreachCampaignContactLink,\n        sa_relationship_kwargs={"lazy": "selectin"}\n    )'
    )
    
    # 2. Fix the Message-OutreachCampaign relationship with explicit primaryjoin
    content = content.replace(
        'outreach_campaigns: List["OutreachCampaign"] = Relationship(back_populates="message", sa_relationship_kwargs={"lazy": "selectin"})',
        'outreach_campaigns: List["OutreachCampaign"] = Relationship(\n        back_populates="message",\n        sa_relationship_kwargs={\n            "lazy": "selectin",\n            "primaryjoin": "Message.id == OutreachCampaign.message_id"\n        }\n    )'
    )
    
    with open('app/models.py', 'w') as file:
        file.write(content)
    
    print("All relationships fixed!")

if __name__ == "__main__":
    fix_relationships()
