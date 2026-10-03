from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Session, User, StudentSession, UserRole
from app.schemas import SessionCreate, SessionResponse, SessionWithStudents
from app.auth import get_current_active_user, get_current_teacher

router = APIRouter()

@router.post("/", response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Создание новой сессии (только для преподавателей)
    """
    db_session = Session(
        name=session_data.name,
        description=session_data.description,
        teacher_id=current_user.id
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

@router.get("/", response_model=List[SessionResponse])
async def get_sessions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Получение списка сессий
    """
    if current_user.role.value == "teacher":
        sessions = db.query(Session).filter(Session.teacher_id == current_user.id).offset(skip).limit(limit).all()
    else:
        # Для студентов показываем только сессии, в которых они участвуют
        sessions = db.query(Session).join(StudentSession).filter(
            StudentSession.student_id == current_user.id
        ).offset(skip).limit(limit).all()
    
    return sessions

@router.get("/{session_id}", response_model=SessionWithStudents)
async def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Получение информации о сессии
    """
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    # Проверка доступа
    if current_user.role.value == "student":
        student_session = db.query(StudentSession).filter(
            StudentSession.session_id == session_id,
            StudentSession.student_id == current_user.id
        ).first()
        if not student_session:
            raise HTTPException(status_code=403, detail="Нет доступа к этой сессии")
    
    # Получение списка студентов
    student_sessions = db.query(StudentSession).filter(
        StudentSession.session_id == session_id
    ).all()
    students = [ss.student for ss in student_sessions]
    
    session_dict = {
        **session.__dict__,
        "students": students
    }
    
    return SessionWithStudents(**session_dict)

@router.post("/{session_id}/students/{student_id}")
async def add_student_to_session(
    session_id: int,
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Добавление студента в сессию (только для преподавателей)
    """
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    if session.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этой сессии")
    
    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Студент не найден")

    if student.role != UserRole.STUDENT:
        raise HTTPException(status_code=400, detail="Пользователь не является студентом")
    
    # Проверка, не добавлен ли уже студент
    existing = db.query(StudentSession).filter(
        StudentSession.session_id == session_id,
        StudentSession.student_id == student_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Студент уже добавлен в сессию")
    
    student_session = StudentSession(
        session_id=session_id,
        student_id=student_id
    )
    db.add(student_session)
    db.commit()
    
    return {"message": "Студент успешно добавлен в сессию"}

@router.delete("/{session_id}/students/{student_id}")
async def remove_student_from_session(
    session_id: int,
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Удаление студента из сессии (только для преподавателей)
    """
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    if session.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этой сессии")
    
    student_session = db.query(StudentSession).filter(
        StudentSession.session_id == session_id,
        StudentSession.student_id == student_id
    ).first()
    
    if not student_session:
        raise HTTPException(status_code=404, detail="Студент не найден в сессии")
    
    db.delete(student_session)
    db.commit()
    
    return {"message": "Студент успешно удален из сессии"}

@router.patch("/{session_id}/status")
async def update_session_status(
    session_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Обновление статуса сессии (только для преподавателей)
    """
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    if session.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этой сессии")
    
    session.is_active = is_active
    db.commit()
    db.refresh(session)
    
    return session

