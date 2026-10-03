from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv

from app.database import engine, Base
from app.routers import auth, users, sessions, chats, yandexgpt, export, setup

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
app.include_router(setup.router, prefix="/api/setup", tags=["setup"])

# Статические файлы для экспортированных документов
exports_dir = os.getenv("EXPORTS_DIR", "exports")
os.makedirs(exports_dir, exist_ok=True)
app.mount("/exports", StaticFiles(directory=exports_dir), name="exports")


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


# В автономной сборке backend сам раздаёт собранный фронтенд (frontend/dist)
frontend_dist = os.getenv("FRONTEND_DIST")

if frontend_dist and os.path.isdir(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa(full_path: str):
        if full_path.startswith(("api/", "exports/")):
            raise HTTPException(status_code=404)
        candidate = os.path.normpath(os.path.join(frontend_dist, full_path))
        if full_path and candidate.startswith(os.path.normpath(frontend_dist)) and os.path.isfile(candidate):
            return FileResponse(candidate)
        # Маршруты React Router (/login, /teacher, ...) отдают index.html
        return FileResponse(os.path.join(frontend_dist, "index.html"))
else:
    @app.get("/")
    async def root():
        return {"message": "YandexGPT Office Laboratory API", "version": "1.0.0"}

