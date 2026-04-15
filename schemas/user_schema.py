from pydantic import BaseModel
from typing import Optional

class CreateUserRequest(BaseModel):
    email: str
    name: str
    password: str
    
class LoginRequest(BaseModel):
    email: str
    password: str
    
class UpdateUserRequest(BaseModel):
    name: Optional[str] = None