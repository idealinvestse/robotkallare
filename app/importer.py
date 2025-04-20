import csv
import sys
import re
from pathlib import Path
import uuid
from sqlmodel import Session
from .database import get_session
from .models import Contact, PhoneNumber

def validate_e164(number: str) -> bool:
    pattern = re.compile(r"^\+[1-9]\d{1,14}$")
    return bool(pattern.match(number))

def import_csv(path: Path) -> None:
    session: Session = next(get_session())
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            contact = Contact(id=uuid.uuid4(), name=row["name"])
            session.add(contact)
            prio = 1
            for key, val in row.items():
                if key.startswith("phone") and val:
                    if validate_e164(val):
                        pn = PhoneNumber(
                            contact_id=contact.id,
                            number=val,
                            priority=prio,
                        )
                        session.add(pn)
                        prio += 1
                    else:
                        print(f"Invalid phone number {val} for {row['name']}")
            session.commit()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: importer.py contacts.csv")
        sys.exit(1)
    import_csv(Path(sys.argv[1]))
