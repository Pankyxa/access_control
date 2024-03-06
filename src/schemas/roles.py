from pydantic import BaseModel
from uuid import UUID


class AssignRole(BaseModel):
    user_id: UUID
    role_id: int
