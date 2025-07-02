"""Fix the relationship definition in models.py"""

def fix_relationship():
    with open('app/models.py', 'r') as file:
        content = file.read()
    
    # Replace the problematic relationship
    fixed_content = content.replace(
        'outreach_campaigns: List["OutreachCampaign"] = Relationship(back_populates="message")',
        'outreach_campaigns: List["OutreachCampaign"] = Relationship(\n        back_populates="contacts",\n        link_model=OutreachCampaignContactLink,\n        sa_relationship_kwargs={"lazy": "selectin"}\n    )'
    )
    
    with open('app/models.py', 'w') as file:
        file.write(fixed_content)
    
    print("Relationship fixed!")

if __name__ == "__main__":
    fix_relationship()
