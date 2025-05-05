import os
import dotenv
dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import uuid
from sqlmodel import Session
from passlib.context import CryptContext
from app.models import User, SQLModel
from app.database import engine

# Password hashing context (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

from sqlalchemy import select, or_

def seed_user():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        # Check if test user already exists
        stmt = select(User).where(
            or_(User.username == "test", User.email == "test@example.com")
        )
        user = session.exec(stmt).first()
        if user:
            print("Test user already exists.")
            return
        # Create new test user
        new_user = User(
            id=uuid.uuid4(),
            username="test",
            email="test@example.com",
            hashed_password=get_password_hash("pass"),
            disabled=False,
        )
        session.add(new_user)
        session.commit()
        print("Test user created: username='test', password='pass'")

if __name__ == "__main__":
    seed_user()
