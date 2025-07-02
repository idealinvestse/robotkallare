"""Fix the relationship definition between Message and OutreachCampaign in models.py"""

def fix_relationship():
    with open('app/models.py', 'r') as file:
        content = file.read()
    
    # The outreach_campaigns in Message class should be a simple 1-to-many relationship
    # not using the outreachcampaigncontactlink secondary table (which is for Contact-OutreachCampaign)
    fixed_content = content.replace(
        'outreach_campaigns: List["OutreachCampaign"] = Relationship(back_populates="message")',
        'outreach_campaigns: List["OutreachCampaign"] = Relationship(back_populates="message", sa_relationship_kwargs={"lazy": "selectin"})'
    )
    
    with open('app/models.py', 'w') as file:
        file.write(fixed_content)
    
    print("Message-OutreachCampaign relationship fixed!")

if __name__ == "__main__":
    fix_relationship()
