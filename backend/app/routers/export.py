from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
from datetime import datetime

from app.database import get_db
from app.models import Message, Session, User, StudentSession, ChatType, MessageStatus
from app.schemas import ExportRequest
from app.auth import get_current_active_user, get_current_teacher
try:
    from app.services.export_service import ExportService
    export_service = ExportService()
except ImportError:
    export_service = None
    print("Warning: Export service not available. Install python-docx and reportlab for export functionality.")

router = APIRouter()

@router.post("/session")
async def export_session(
    request: ExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Экспорт сессии в документ
    """
    # Проверка доступа к сессии
    session = db.query(Session).filter(Session.id == request.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    if current_user.role.value == "student":
        student_session = db.query(StudentSession).filter(
            StudentSession.session_id == request.session_id,
            StudentSession.student_id == current_user.id
        ).first()
        if not student_session:
            raise HTTPException(status_code=403, detail="Нет доступа к этой сессии")
    
    # Получение сообщений
    messages = db.query(Message).filter(
        Message.session_id == request.session_id,
        Message.chat_type == ChatType.YANDEXGPT,
        Message.status == MessageStatus.APPROVED
    ).order_by(Message.created_at).all()
    
    if not messages:
        raise HTTPException(status_code=400, detail="Нет сообщений для экспорта")
    
    # Формирование данных для экспорта
    export_data = []
    for msg in messages:
        author = db.query(User).filter(User.id == msg.author_id).first()
        export_data.append({
            "author": author.full_name if author else "Неизвестный",
            "prompt": msg.content if not msg.is_from_yandexgpt else None,
            "response": msg.yandexgpt_response if msg.is_from_yandexgpt else None,
            "timestamp": msg.created_at.isoformat()
        })
    
    # Экспорт в выбранный формат
    if not export_service:
        raise HTTPException(status_code=500, detail="Сервис экспорта недоступен")
    
    try:
        file_path = export_service.export_session(
            session_name=session.name,
            messages=export_data,
            format=request.format,
            include_context=request.include_context
        )
        
        return FileResponse(
            path=file_path,
            filename=os.path.basename(file_path),
            media_type="application/octet-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при экспорте: {str(e)}")

