import uuid
from datetime import datetime

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: uuid.UUID
    kind: str
    message: str
    sent_at: datetime

    class Config:
        from_attributes = True
