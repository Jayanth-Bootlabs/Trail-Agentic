from pydantic import BaseModel
from typing import Optional

class CreateUserRequest(BaseModel):
    email: str
    name: str
    
class UpdateUserRequest(BaseModel):
    name: Optional[str] = None