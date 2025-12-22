from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from app.models import UserRole, ChatType, MessageStatus

# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    role: UserRole

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Auth schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Session schemas
class SessionBase(BaseModel):
    name: str
    description: Optional[str] = None

class SessionCreate(SessionBase):
    pass

class SessionResponse(SessionBase):
    id: int
    teacher_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class SessionWithStudents(SessionResponse):
    students: List[UserResponse] = []

# Message schemas
class MessageBase(BaseModel):
    content: str
    chat_type: ChatType

class MessageCreate(MessageBase):
    session_id: int

class MessageResponse(MessageBase):
    id: int
    session_id: int
    author_id: int
    author_name: str
    status: MessageStatus
    is_from_yandexgpt: bool
    yandexgpt_response: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# YandexGPT schemas
class YandexGPTRequest(BaseModel):
    prompt: str
    session_id: int
    context: Optional[List[dict]] = None

class YandexGPTResponse(BaseModel):
    response: str
    tokens_used: Optional[int] = None

# Export schemas
class ExportRequest(BaseModel):
    session_id: int
    format: str  # pdf, docx
    include_context: bool = True

