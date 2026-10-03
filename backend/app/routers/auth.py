from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database import get_db
from app.models import User, UserRole
from app.net import is_local_request
from app.schemas import UserCreate, UserResponse, Token
from app.auth import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    get_user_by_username,
    get_user_by_email,
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter()

def can_register_teacher(request: Request, db: Session) -> bool:
    """
    Преподавателя можно зарегистрировать, только если преподавателей ещё нет
    (первый запуск) или регистрация идёт с компьютера, где запущен сервер.
    Иначе любой, кто получил ссылку, мог бы стать преподавателем и тратить
    платные запросы к модели.
    """
    if is_local_request(request):
        return True
    return db.query(User).filter(User.role == UserRole.TEACHER).first() is None


@router.get("/registration-options")
async def registration_options(request: Request, db: Session = Depends(get_db)):
    return {"can_register_teacher": can_register_teacher(request, db)}


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, request: Request, db: Session = Depends(get_db)):
    """
    Регистрация нового пользователя
    """
    if user_data.role == UserRole.TEACHER and not can_register_teacher(request, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Аккаунт преподавателя можно создать только на компьютере, где запущен сервер",
        )
    # Проверка существования пользователя
    if get_user_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким именем уже существует"
        )
    
    if get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует"
        )
    
    # Создание нового пользователя
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        role=user_data.role
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Вход в систему
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Получение информации о текущем пользователе
    """
    return current_user

