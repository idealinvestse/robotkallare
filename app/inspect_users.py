import os
import dotenv
dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from sqlmodel import Session, select
from app.models import User, SQLModel
from app.database import engine

with Session(engine) as session:
    users = session.exec(select(User)).all()
    print(f"Found {len(users)} user(s):")
    for user in users:
        print(f"- username: {user.username}, email: {user.email}, disabled: {user.disabled}")
