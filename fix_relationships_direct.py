"""Directly fix SQLAlchemy relationships in models.py"""

def fix_relationships():
    # Read the entire file
    with open('app/models.py', 'r') as file:
        lines = file.readlines()
    
    # Find the Message class and modify its relationship
    message_class_index = -1
    message_relationship_index = -1
    contact_class_index = -1
    contact_relationship_index = -1
    
    for i, line in enumerate(lines):
        if "class Message(SQLModel, table=True):" in line:
            message_class_index = i
        elif message_class_index > 0 and "outreach_campaigns: List" in line and "Relationship" in line:
            message_relationship_index = i
        elif "class Contact(SQLModel, table=True):" in line:
            contact_class_index = i
        elif contact_class_index > 0 and "outreach_campaigns: List" in line and "Relationship" in line:
            contact_relationship_index = i
    
    if message_relationship_index > 0:
        # Replace the Message relationship with direct primaryjoin
        message_relationship_lines = [
            '    outreach_campaigns: List["OutreachCampaign"] = Relationship(\n',
            '        back_populates="message",\n',
            '        sa_relationship_kwargs={\n',
            '            "lazy": "selectin",\n',
            '            "primaryjoin": "Message.id == OutreachCampaign.message_id"\n',
            '        }\n',
            '    )\n'
        ]
        lines[message_relationship_index:message_relationship_index+1] = message_relationship_lines
    
    if contact_relationship_index > 0:
        # Replace the Contact relationship with direct link_model
        contact_relationship_lines = [
            '    outreach_campaigns: List["OutreachCampaign"] = Relationship(\n',
            '        back_populates="contacts",\n',
            '        link_model=OutreachCampaignContactLink,\n',
            '        sa_relationship_kwargs={"lazy": "selectin"}\n',
            '    )\n'
        ]
        lines[contact_relationship_index:contact_relationship_index+1] = contact_relationship_lines
    
    # Write the modified content back
    with open('app/models.py', 'w') as file:
        file.writelines(lines)
    
    print(f"Fixed relationships directly - Message relationship at line {message_relationship_index}, Contact relationship at line {contact_relationship_index}")

if __name__ == "__main__":
    fix_relationships()
