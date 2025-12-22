from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Message, Session, User, StudentSession, ChatType, MessageStatus, TokenUsage
from app.schemas import YandexGPTRequest, YandexGPTResponse, MessageResponse
from app.auth import get_current_active_user, get_current_teacher
from app.services.yandexgpt_service import YandexGPTService

router = APIRouter()
yandexgpt_service = YandexGPTService()

@router.post("/send", response_model=YandexGPTResponse)
async def send_to_yandexgpt(
    request: YandexGPTRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Отправка запроса в YandexGPT
    """
    # Проверка доступа к сессии
    session = db.query(Session).filter(Session.id == request.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    # Для студентов проверяем, что они имеют доступ
    if current_user.role.value == "student":
        student_session = db.query(StudentSession).filter(
            StudentSession.session_id == request.session_id,
            StudentSession.student_id == current_user.id
        ).first()
        if not student_session:
            raise HTTPException(status_code=403, detail="Нет доступа к этой сессии")
    
    # Получение контекста из предыдущих сообщений
    previous_messages = db.query(Message).filter(
        Message.session_id == request.session_id,
        Message.chat_type == ChatType.YANDEXGPT,
        Message.status == MessageStatus.APPROVED
    ).order_by(Message.created_at).all()
    
    context = None
    if previous_messages:
        context_messages = []
        for msg in previous_messages:
            context_messages.append({
                "role": "assistant" if msg.is_from_yandexgpt else "user",
                "text": msg.yandexgpt_response if msg.is_from_yandexgpt else msg.content
            })
        context = context_messages
    
    # Отправка запроса в YandexGPT
    try:
        result = yandexgpt_service.send_request(
            prompt=request.prompt,
            context=context
        )
        
        # Сохранение сообщения пользователя
        user_message = Message(
            session_id=request.session_id,
            author_id=current_user.id,
            chat_type=ChatType.YANDEXGPT,
            content=request.prompt,
            status=MessageStatus.APPROVED,
            is_from_yandexgpt=False
        )
        db.add(user_message)
        db.flush()
        
        # Сохранение ответа YandexGPT
        yandexgpt_message = Message(
            session_id=request.session_id,
            author_id=current_user.id,
            chat_type=ChatType.YANDEXGPT,
            content=request.prompt,
            yandexgpt_response=result["response"],
            status=MessageStatus.APPROVED,
            is_from_yandexgpt=True
        )
        db.add(yandexgpt_message)
        
        # Сохранение статистики использования токенов
        if result.get("tokens_used"):
            token_usage = TokenUsage(
                session_id=request.session_id,
                user_id=current_user.id,
                tokens_used=result["tokens_used"],
                request_type="yandexgpt_request"
            )
            db.add(token_usage)
        
        db.commit()
        
        return YandexGPTResponse(
            response=result["response"],
            tokens_used=result.get("tokens_used")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при обращении к YandexGPT: {str(e)}")

@router.post("/approve/{message_id}")
async def approve_student_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Одобрение сообщения студента и отправка в YandexGPT (только для преподавателей)
    """
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Сообщение не найдено")
    
    if message.status != MessageStatus.PENDING:
        raise HTTPException(status_code=400, detail="Сообщение уже обработано")
    
    # Проверка доступа к сессии
    session = db.query(Session).filter(Session.id == message.session_id).first()
    if not session or session.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому сообщению")
    
    # Получение контекста
    previous_messages = db.query(Message).filter(
        Message.session_id == message.session_id,
        Message.chat_type == ChatType.YANDEXGPT,
        Message.status == MessageStatus.APPROVED
    ).order_by(Message.created_at).all()
    
    context = None
    if previous_messages:
        context_messages = []
        for msg in previous_messages:
            context_messages.append({
                "role": "assistant" if msg.is_from_yandexgpt else "user",
                "text": msg.yandexgpt_response if msg.is_from_yandexgpt else msg.content
            })
        context = context_messages
    
    # Отправка в YandexGPT
    try:
        result = yandexgpt_service.send_request(
            prompt=message.content,
            context=context
        )
        
        # Обновление статуса сообщения
        message.status = MessageStatus.APPROVED
        
        # Сохранение ответа YandexGPT
        yandexgpt_message = Message(
            session_id=message.session_id,
            author_id=message.author_id,
            chat_type=ChatType.YANDEXGPT,
            content=message.content,
            yandexgpt_response=result["response"],
            status=MessageStatus.APPROVED,
            is_from_yandexgpt=True
        )
        db.add(yandexgpt_message)
        
        # Сохранение статистики
        if result.get("tokens_used"):
            token_usage = TokenUsage(
                session_id=message.session_id,
                user_id=message.author_id,
                tokens_used=result["tokens_used"],
                request_type="yandexgpt_request"
            )
            db.add(token_usage)
        
        db.commit()
        
        author = db.query(User).filter(User.id == message.author_id).first()
        return {
            "message": "Сообщение одобрено и отправлено в YandexGPT",
            "response": result["response"],
            "tokens_used": result.get("tokens_used")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при обращении к YandexGPT: {str(e)}")

