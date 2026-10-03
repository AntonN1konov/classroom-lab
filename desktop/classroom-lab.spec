# -*- mode: python ; coding: utf-8 -*-
# Сборка: из корня репозитория, после `npm run build` во frontend/
#   pyinstaller desktop/classroom-lab.spec
import os
from PyInstaller.utils.hooks import collect_submodules

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
BACKEND = os.path.join(ROOT, "backend")

# Модули backend перечисляем по файлам: uvicorn и роутеры импортируются динамически
app_modules = []
for dirpath, _, files in os.walk(os.path.join(BACKEND, "app")):
    for f in files:
        if f.endswith(".py"):
            rel = os.path.relpath(os.path.join(dirpath, f), BACKEND)[:-3]
            mod = rel.replace(os.sep, ".")
            app_modules.append(mod[: -len(".__init__")] if mod.endswith(".__init__") else mod)

hiddenimports = app_modules + collect_submodules("uvicorn") + ["email_validator", "multipart"]

a = Analysis(
    [os.path.join(ROOT, "desktop", "launcher.py")],
    pathex=[BACKEND],
    datas=[
        (os.path.join(ROOT, "frontend", "dist"), "frontend_dist"),
        (os.path.join(BACKEND, "app", "assets"), os.path.join("app", "assets")),
    ],
    hiddenimports=hiddenimports,
    excludes=["tkinter", "psycopg2", "alembic"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ClassroomLab",
    console=True,
    icon=os.path.join(ROOT, "desktop", "icon.ico") if os.path.exists(os.path.join(ROOT, "desktop", "icon.ico")) else None,
)
coll = COLLECT(exe, a.binaries, a.datas, name="ClassroomLab")
