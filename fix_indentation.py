"""Fix indentation issues in models.py"""

def fix_indentation():
    # Read the entire file
    with open('app/models.py', 'r') as file:
        content = file.read()
    
    # Fix the Contact relationship
    if "    outreach_campaigns: List[\"OutreachCampaign\"] = Relationship(" in content:
        corrected_content = content.replace(
            "    outreach_campaigns: List[\"OutreachCampaign\"] = Relationship(\n        back_populates=\"contacts\",", 
            "    outreach_campaigns: List[\"OutreachCampaign\"] = Relationship(back_populates=\"contacts\","
        )
        corrected_content = corrected_content.replace(
            "        link_model=OutreachCampaignContactLink,\n        sa_relationship_kwargs={\"lazy\": \"selectin\"}\n    )", 
            "link_model=OutreachCampaignContactLink, sa_relationship_kwargs={\"lazy\": \"selectin\"})"
        )
        
        # Fix the Message relationship
        corrected_content = corrected_content.replace(
            "    outreach_campaigns: List[\"OutreachCampaign\"] = Relationship(\n        back_populates=\"message\",",
            "    outreach_campaigns: List[\"OutreachCampaign\"] = Relationship(back_populates=\"message\","
        )
        corrected_content = corrected_content.replace(
            "        sa_relationship_kwargs={\n            \"lazy\": \"selectin\",\n            \"primaryjoin\": \"Message.id == OutreachCampaign.message_id\"\n        }\n    )",
            "sa_relationship_kwargs={\"lazy\": \"selectin\", \"primaryjoin\": \"Message.id == OutreachCampaign.message_id\"})"
        )
        
        # Write corrected content
        with open('app/models.py', 'w') as file:
            file.write(corrected_content)
        
        print("Fixed indentation issues in models.py")
    else:
        print("Could not find the expected content pattern to fix.")

if __name__ == "__main__":
    fix_indentation()
