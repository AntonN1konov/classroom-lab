from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Message, Session, User, StudentSession, ChatType, MessageStatus
from app.schemas import MessageCreate, MessageResponse
from app.auth import get_current_active_user, get_current_teacher

router = APIRouter()

@router.post("/messages", response_model=MessageResponse)
async def create_message(
    message_data: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Создание нового сообщения
    """
    # Проверка доступа к сессии
    session = db.query(Session).filter(Session.id == message_data.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    if current_user.role.value == "student":
        student_session = db.query(StudentSession).filter(
            StudentSession.session_id == message_data.session_id,
            StudentSession.student_id == current_user.id
        ).first()
        if not student_session:
            raise HTTPException(status_code=403, detail="Нет доступа к этой сессии")
        
        # Для студентов сообщения в YandexGPT требуют одобрения
        if message_data.chat_type == ChatType.YANDEXGPT:
            status = MessageStatus.PENDING
        else:
            status = MessageStatus.APPROVED
    else:
        # Для преподавателей сообщения одобрены автоматически
        status = MessageStatus.APPROVED
    
    db_message = Message(
        session_id=message_data.session_id,
        author_id=current_user.id,
        chat_type=message_data.chat_type,
        content=message_data.content,
        status=status
    )
    
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    # Формирование ответа с именем автора
    response_dict = {
        **db_message.__dict__,
        "author_name": current_user.full_name
    }
    
    return MessageResponse(**response_dict)

@router.get("/messages/{session_id}", response_model=List[MessageResponse])
async def get_messages(
    session_id: int,
    chat_type: ChatType,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Получение сообщений сессии по типу чата
    """
    # Проверка доступа к сессии
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    if current_user.role.value == "student":
        student_session = db.query(StudentSession).filter(
            StudentSession.session_id == session_id,
            StudentSession.student_id == current_user.id
        ).first()
        if not student_session:
            raise HTTPException(status_code=403, detail="Нет доступа к этой сессии")
    
    messages = db.query(Message).filter(
        Message.session_id == session_id,
        Message.chat_type == chat_type
    ).order_by(Message.created_at).all()
    
    result = []
    for msg in messages:
        author = db.query(User).filter(User.id == msg.author_id).first()
        result.append(MessageResponse(
            id=msg.id,
            session_id=msg.session_id,
            author_id=msg.author_id,
            author_name=author.full_name if author else "Неизвестный",
            chat_type=msg.chat_type,
            content=msg.content,
            status=msg.status,
            is_from_yandexgpt=msg.is_from_yandexgpt,
            yandexgpt_response=msg.yandexgpt_response,
            created_at=msg.created_at
        ))
    
    return result

@router.patch("/messages/{message_id}/status")
async def update_message_status(
    message_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Обновление статуса сообщения (только для преподавателей)
    """
    try:
        message_status = MessageStatus(status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Неверный статус: {status}")
    
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Сообщение не найдено")
    
    # Проверка доступа к сессии
    session = db.query(Session).filter(Session.id == message.session_id).first()
    if not session or session.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому сообщению")
    
    message.status = message_status
    db.commit()
    db.refresh(message)
    
    author = db.query(User).filter(User.id == message.author_id).first()
    return MessageResponse(
        id=message.id,
        session_id=message.session_id,
        author_id=message.author_id,
        author_name=author.full_name if author else "Неизвестный",
        chat_type=message.chat_type,
        content=message.content,
        status=message.status,
        is_from_yandexgpt=message.is_from_yandexgpt,
        yandexgpt_response=message.yandexgpt_response,
        created_at=message.created_at
    )

