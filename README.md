
Краткая инструкция — запуск одной командой

Требования
- Node.js и npm
- Python 3.11+

Быстрый запуск

1. Перейдите в корень репозитория и выполните:

```bash
npm run dev:all
```

Команда работает и на Windows, и на macOS. Она:
- находит подходящий Python 3
- создаёт виртуальное окружение, если его ещё нет
- использует совместимое окружение для текущей платформы
- устанавливает зависимости из `requirements.txt`, если файл появится
- иначе проверяет наличие Django и при необходимости ставит его
- применяет миграции
- запускает Django dev-сервер на `127.0.0.1:8000`

Особенности по платформам
- Windows: сначала используется `venv`, затем `.venv`
- macOS: сначала используется `.venv`, затем `venv`
- если в проекте уже лежит окружение от другой ОС, скрипт не ломает его и создаёт отдельное совместимое окружение

Проверка без запуска сервера

```bash
node scripts/dev-all.mjs --check
```

Ручной запуск

Windows PowerShell:

```powershell
python -m venv venv
venv\Scripts\python app5\manage.py migrate
venv\Scripts\python app5\manage.py runserver 8000
```

macOS:

```bash
python3 -m venv .venv
.venv/bin/python app5/manage.py migrate
.venv/bin/python app5/manage.py runserver 8000
```

Примечания
- `manage.py` находится в папке `app5`
- остановить сервер можно через `Ctrl+C`
- если порт `8000` занят, сервер нужно остановить или запустить вручную на другом порту

