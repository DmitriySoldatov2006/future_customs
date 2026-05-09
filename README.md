
Краткая инструкция — запуск одной командой

Требования
- Python 3.11+ (рекомендуется `python3` и виртуальное окружение)

Быстрый запуск

1) Перейдите в корень репозитория и выполните одну команду:

```bash
cd future_customs
npm run dev:all
```

Эта команда создаст/использует `venv`, установит зависимости (если есть `requirements.txt` — установит их, иначе установит Django), применит миграции и запустит dev-сервер на порту 8000.

Если вы предпочитаете выполнять шаги вручную:

```bash
cd future_customs
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # или: pip install Django
cd app5
python manage.py migrate
python manage.py runserver 8000
```

Примечания
- `manage.py` находится в папке `app5`.
- Если порт 8000 занят, остановите процесс или используйте другой порт: `python manage.py runserver 8001`.
- Остановить сервер: Ctrl+C в терминале, где он запущен.

Файлы
- Скрипт запуска находится в `package.json` (`dev:all`).

Готов помочь: могу добавить `requirements.txt` или пример `.env` по запросу.

