from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from app.database import Base

class UserRole(str, enum.Enum):
    TEACHER = "teacher"
    STUDENT = "student"

class ChatType(str, enum.Enum):
    YANDEXGPT = "yandexgpt"
    GROUP = "group"

class MessageStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.STUDENT, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    sessions = relationship("Session", back_populates="teacher")
    student_sessions = relationship("StudentSession", back_populates="student")
    messages = relationship("Message", back_populates="author")

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    teacher = relationship("User", back_populates="sessions")
    students = relationship("StudentSession", back_populates="session", cascade="all, delete-orphan")
    yandexgpt_messages = relationship("Message", back_populates="session", 
                                     primaryjoin="and_(Session.id==Message.session_id, Message.chat_type=='yandexgpt')",
                                     foreign_keys="Message.session_id")
    group_messages = relationship("Message", back_populates="session",
                                 primaryjoin="and_(Session.id==Message.session_id, Message.chat_type=='group')",
                                 foreign_keys="Message.session_id",
                                 overlaps="yandexgpt_messages")

class StudentSession(Base):
    __tablename__ = "student_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    
    session = relationship("Session", back_populates="students")
    student = relationship("User", back_populates="student_sessions")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    chat_type = Column(SQLEnum(ChatType), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(SQLEnum(MessageStatus), default=MessageStatus.PENDING)
    is_from_yandexgpt = Column(Boolean, default=False)
    yandexgpt_response = Column(Text)
    message_metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    session = relationship("Session")
    author = relationship("User", back_populates="messages")

class Archive(Base):
    __tablename__ = "archives"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    session = relationship("Session")

class TokenUsage(Base):
    __tablename__ = "token_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    tokens_used = Column(Integer, default=0)
    request_type = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    session = relationship("Session")



class SessionInvite(Base):
    """Ссылка-приглашение в сессию: студент переходит по ней и попадает в сессию."""
    __tablename__ = "session_invites"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("Session")
