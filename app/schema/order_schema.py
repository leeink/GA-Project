from pydantic import BaseModel

from typing import Dict
import uuid


class OrderSchema(BaseModel):
    item: Dict[uuid.UUID, int]
<<<<<<< Updated upstream
    user_id: uuid.UUID
    address: str
=======
    address: str
>>>>>>> Stashed changes
