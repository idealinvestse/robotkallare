import pytest
from app.importer import validate_e164, import_csv
from app.models import Contact, PhoneNumber
from sqlmodel import Session
from pathlib import Path
import tempfile

def test_validate_e164():
    assert validate_e164("+46701234567") is True
    assert validate_e164("46701234567") is False
    assert validate_e164("+123") is True
    assert validate_e164("abc") is False

def test_import_csv(session: Session):
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        f.write("name,phone1,phone2\n")
        f.write("John Doe,+46701234567,+46709876543\n")
        f.flush()
        import_csv(Path(f.name))
    contacts = session.exec(Contact.select()).all()
    assert len(contacts) == 1
    assert contacts[0].name == "John Doe"
    numbers = session.exec(PhoneNumber.select()).all()
    assert len(numbers) == 2
    assert numbers[0].number == "+46701234567"
    assert numbers[0].priority == 1
    assert numbers[1].number == "+46709876543"
    assert numbers[1].priority == 2
