# Быстрый старт

## Предварительные требования

1. Python 3.9+
2. Node.js 18+
3. PostgreSQL 12+
4. Yandex Cloud аккаунт с API ключами

## Установка

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Создайте файл `.env`:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/yandexgpt_lab
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
YANDEX_CLOUD_FOLDER_ID=your-folder-id
YANDEXGPT_API_KEY=your-api-key
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

Создайте базу данных:
```sql
CREATE DATABASE yandexgpt_lab;
```

Запустите сервер:
```bash
python run.py
# или
uvicorn app.main:app --reload
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

## Использование Docker

```bash
docker-compose up -d
```

Не забудьте создать файл `.env` в корне проекта с переменными окружения для Yandex Cloud.

## Первый вход

1. Откройте http://localhost:3000
2. Зарегистрируйтесь как преподаватель
3. Создайте сессию
4. Добавьте студентов в сессию
5. Начните работу с YandexGPT!

