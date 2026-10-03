from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Message, Session, User, StudentSession, ChatType, MessageStatus, TokenUsage
from app.schemas import YandexGPTRequest, YandexGPTResponse, MessageResponse
from app.auth import get_current_active_user, get_current_teacher
from app.services import llm

router = APIRouter()

@router.post("/send", response_model=YandexGPTResponse)
def send_to_yandexgpt(
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
    
    # Напрямую (уровень 1) пишет только преподаватель этой сессии.
    # Студенты отправляют промты через уровень 2 — на одобрение.
    if current_user.role.value != "teacher" or session.teacher_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Напрямую в модель пишет только преподаватель сессии. Отправьте промт на одобрение.",
        )
    
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
        result = llm.send(prompt=request.prompt, context=context)
        
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
        
    except llm.LLMError as e:
        db.rollback()
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка при обращении к модели: {e}")

@router.post("/approve/{message_id}")
def approve_student_message(
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
        result = llm.send(prompt=message.content, context=context)
        
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
            "message": "Сообщение одобрено и отправлено модели",
            "response": result["response"],
            "tokens_used": result.get("tokens_used")
        }
        
    except llm.LLMError as e:
        db.rollback()
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка при обращении к модели: {e}")

