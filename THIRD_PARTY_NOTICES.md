# Сторонние материалы и лицензии

В проекте Classroom Lab используются сторонние библиотеки, инструменты и шрифты.
Права на них принадлежат их авторам. Они распространяются на условиях
собственных лицензий, указанных ниже, и не входят в состав прав на сам проект.

Версии указаны так, как они заданы в `backend/requirements.txt` и `frontend/package.json`.

## Происхождение проекта

Проект создан на основе учебного репозитория
[Diyaryulchub/YandexGPT-office-laboratory](https://github.com/Diyaryulchub/YandexGPT-office-laboratory)
(авторы коммитов: Diyaryulchub, d.yulchubaev). История его изменений сохранена в этом репозитории.
Лицензия в исходном репозитории не указана.

## Backend (Python)

| Компонент | Версия | Лицензия |
|---|---|---|
| [FastAPI](https://github.com/fastapi/fastapi) | >=0.115.0 | MIT |
| [Starlette](https://github.com/encode/starlette) (зависимость FastAPI) | — | BSD-3-Clause |
| [Uvicorn](https://github.com/encode/uvicorn) | >=0.32.0 | BSD-3-Clause |
| [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy) | >=2.0.36 | MIT |
| [psycopg2-binary](https://github.com/psycopg/psycopg2) | >=2.9.10 | LGPL-3.0-or-later (с исключением для OpenSSL) |
| [Alembic](https://github.com/sqlalchemy/alembic) | >=1.13.0 | MIT |
| [Pydantic](https://github.com/pydantic/pydantic) | >=2.10.0 | MIT |
| [pydantic-settings](https://github.com/pydantic/pydantic-settings) | >=2.6.0 | MIT |
| [email-validator](https://github.com/JoshData/python-email-validator) | >=2.0.0 | Unlicense |
| [python-jose](https://github.com/mpdavis/python-jose) | >=3.3.0 | MIT |
| [bcrypt](https://github.com/pyca/bcrypt) | >=4.0.0 | Apache-2.0 |
| [python-multipart](https://github.com/Kludex/python-multipart) | >=0.0.12 | Apache-2.0 |
| [aiofiles](https://github.com/Tinche/aiofiles) | >=24.1.0 | Apache-2.0 |
| [Requests](https://github.com/psf/requests) | >=2.32.0 | Apache-2.0 |
| [python-docx](https://github.com/python-openxml/python-docx) | >=1.1.2 | MIT |
| [ReportLab](https://www.reportlab.com/opensource/) | >=4.2.0 | BSD-3-Clause |
| [websockets](https://github.com/python-websockets/websockets) | >=14.0 | BSD-3-Clause |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | >=1.0.1 | BSD-3-Clause |

## Frontend (JavaScript)

| Компонент | Версия | Лицензия |
|---|---|---|
| [React](https://github.com/facebook/react), React DOM | ^18.2.0 | MIT |
| [React Router](https://github.com/remix-run/react-router) | ^6.20.0 | MIT |
| [TanStack Query](https://github.com/TanStack/query) | ^5.12.2 | MIT |
| [Zustand](https://github.com/pmndrs/zustand) | ^4.4.7 | MIT |
| [Axios](https://github.com/axios/axios) | ^1.6.2 | MIT |
| [date-fns](https://github.com/date-fns/date-fns) | ^2.30.0 | MIT |
| [Vite](https://github.com/vitejs/vite) (сборка) | ^5.0.8 | MIT |
| [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react) (сборка) | ^4.2.1 | MIT |

## Шрифты

| Компонент | Где используется | Лицензия |
|---|---|---|
| [DejaVu Sans](https://dejavu-fonts.github.io/) (`DejaVuSans.ttf`, `DejaVuSans-Bold.ttf`) | Экспорт в PDF, `backend/app/assets/fonts/` | Bitstream Vera Fonts License; изменения DejaVu переданы в общественное достояние. Полный текст: [`backend/app/assets/fonts/LICENSE-DejaVu.txt`](backend/app/assets/fonts/LICENSE-DejaVu.txt) |

## Компоненты установщика

Эти компоненты не хранятся в репозитории. Они скачиваются или используются при сборке в GitHub Actions
и входят в готовый установщик.

| Компонент | Назначение | Лицензия |
|---|---|---|
| [Python](https://www.python.org/) (среда выполнения) | Встроен в исполняемый файл | PSF-2.0 |
| [cloudflared](https://github.com/cloudflare/cloudflared) | Доступ из интернета (Cloudflare Tunnel) | Apache-2.0 |
| [PyInstaller](https://github.com/pyinstaller/pyinstaller) (сборка) | Упаковка в исполняемый файл | GPL-2.0-or-later с исключением для загрузчика: допускает распространение собранных программ на любых условиях |
| [Inno Setup](https://jrsoftware.org/isinfo.php) (сборка) | Создание установщика Windows | Inno Setup License (бесплатное использование, в том числе коммерческое) |

## Внешние сервисы

Сервисы, к которым программа может подключаться по выбору пользователя. Их код в проект не входит.

- **YandexGPT** (Yandex Cloud) — по условиям использования Yandex Cloud.
- **Ollama**, **LM Studio** — устанавливаются пользователем отдельно, на условиях своих лицензий.
- **Cloudflare Tunnel** (trycloudflare.com) — по условиям использования Cloudflare.

## Транзитивные зависимости

В таблицах перечислены прямые зависимости. Их собственные зависимости (например, anyio,
cryptography, scheduler) распространяются под собственными лицензиями, в основном MIT, BSD
и Apache-2.0. Полный список можно получить командами:

```bash
pip install pip-licenses && pip-licenses --from=mixed --format=markdown   # backend
npx license-checker --summary                                            # frontend
```
