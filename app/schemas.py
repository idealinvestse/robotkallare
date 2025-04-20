from datetime import datetime
from pydantic import BaseModel

class Stats(BaseModel):
    total_calls: int
    completed: int
    no_answer: int
    manual: int
    error: int
    last_call: datetime | None = None
