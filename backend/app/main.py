from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv

from app.database import engine, Base
from app.routers import auth, users, sessions, chats, yandexgpt, export

load_dotenv()

# Создание таблиц БД
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="YandexGPT Office Laboratory",
    description="Виртуальный кабинет-лаборатория для совместной работы с YandexGPT",
    version="1.0.0"
)

# CORS настройки
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(chats.router, prefix="/api/chats", tags=["chats"])
app.include_router(yandexgpt.router, prefix="/api/yandexgpt", tags=["yandexgpt"])
app.include_router(export.router, prefix="/api/export", tags=["export"])

# Статические файлы для экспортированных документов
os.makedirs("exports", exist_ok=True)
app.mount("/exports", StaticFiles(directory="exports"), name="exports")

@app.get("/")
async def root():
    return {"message": "YandexGPT Office Laboratory API", "version": "1.0.0"}

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

