"""Приглашения в сессию по ссылке."""
import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.auth import get_current_active_user, get_current_teacher
from app.database import get_db
from app.models import Session, SessionInvite, StudentSession, User, UserRole

router = APIRouter()


def _own_session(db: DBSession, session_id: int, teacher: User) -> Session:
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    if session.teacher_id != teacher.id:
        raise HTTPException(status_code=403, detail="Это не ваша сессия")
    return session


def _active_invite(db: DBSession, token: str) -> SessionInvite:
    invite = db.query(SessionInvite).filter(SessionInvite.token == token, SessionInvite.is_active.is_(True)).first()
    if not invite or not invite.session or not invite.session.is_active:
        raise HTTPException(status_code=404, detail="Приглашение недействительно. Попросите у преподавателя новую ссылку.")
    return invite


def _new_invite(db: DBSession, session_id: int, teacher: User) -> SessionInvite:
    invite = SessionInvite(session_id=session_id, token=secrets.token_urlsafe(16), created_by=teacher.id)
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite


@router.post("/sessions/{session_id}/invite")
def get_or_create_invite(session_id: int, db: DBSession = Depends(get_db),
                         teacher: User = Depends(get_current_teacher)):
    """Текущая ссылка-приглашение сессии (создаётся при первом запросе)."""
    _own_session(db, session_id, teacher)
    invite = db.query(SessionInvite).filter(
        SessionInvite.session_id == session_id, SessionInvite.is_active.is_(True)
    ).first() or _new_invite(db, session_id, teacher)
    return {"token": invite.token}


@router.post("/sessions/{session_id}/invite/reset")
def reset_invite(session_id: int, db: DBSession = Depends(get_db),
                 teacher: User = Depends(get_current_teacher)):
    """Отозвать старую ссылку и выпустить новую."""
    _own_session(db, session_id, teacher)
    db.query(SessionInvite).filter(SessionInvite.session_id == session_id).update({"is_active": False})
    db.commit()
    return {"token": _new_invite(db, session_id, teacher).token}


@router.get("/invites/{token}")
def invite_info(token: str, db: DBSession = Depends(get_db)):
    """Публичная информация о приглашении (для страницы /join)."""
    invite = _active_invite(db, token)
    return {
        "session_name": invite.session.name,
        "session_description": invite.session.description,
        "teacher_name": invite.session.teacher.full_name if invite.session.teacher else None,
    }


@router.post("/invites/{token}/join")
def join_by_invite(token: str, db: DBSession = Depends(get_db),
                   user: User = Depends(get_current_active_user)):
    invite = _active_invite(db, token)
    if user.role != UserRole.STUDENT:
        raise HTTPException(status_code=400, detail="По приглашению присоединяются студенты. Войдите под аккаунтом студента.")
    exists = db.query(StudentSession).filter(
        StudentSession.session_id == invite.session_id, StudentSession.student_id == user.id
    ).first()
    if not exists:
        db.add(StudentSession(session_id=invite.session_id, student_id=user.id))
        db.commit()
    return {"session_id": invite.session_id, "already_member": bool(exists)}
