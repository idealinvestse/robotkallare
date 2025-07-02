"""Direct fix for relationships in models.py by looking for and replacing the entire line patterns"""

def direct_fix():
    with open('app/models.py', 'r') as file:
        lines = file.readlines()
    
    # Find the problematic lines
    for i in range(len(lines)):
        # Fix Contact.outreach_campaigns relationship
        if "    outreach_campaigns: List[\"OutreachCampaign\"] = Relationship(" in lines[i]:
            # Check if this is in the Contact class (has to be before Message class)
            if any("class Message" in lines[j] for j in range(i+1, min(i+20, len(lines)))):
                # This is in the Contact class
                lines[i] = "    outreach_campaigns: List[\"OutreachCampaign\"] = Relationship(back_populates=\"contacts\", link_model=OutreachCampaignContactLink, sa_relationship_kwargs={\"lazy\": \"selectin\"})\n"
            # The one in Message class
            else:
                lines[i] = "    outreach_campaigns: List[\"OutreachCampaign\"] = Relationship(back_populates=\"message\", sa_relationship_kwargs={\"lazy\": \"selectin\", \"primaryjoin\": \"Message.id == OutreachCampaign.message_id\"})\n"

    # Remove any indentation-causing lines that were not properly handled
    new_lines = []
    i = 0
    skip = False
    while i < len(lines):
        line = lines[i]
        # Skip any remaining problematic back_populates lines that weren't properly replaced
        if "back_populates=" in line and "=" not in line.split("back_populates=")[0]:
            skip = True
        elif skip and ")" in line:
            skip = False
            i += 1
            continue
        elif not skip:
            new_lines.append(line)
        i += 1

    # Write the fixed content
    with open('app/models.py', 'w') as file:
        file.writelines(new_lines)
    
    print("Direct replacement of relationship definitions completed")

if __name__ == "__main__":
    direct_fix()
