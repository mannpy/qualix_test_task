# Django JSON-RPC тестовый проект

## Настройка секретов (сертификат / ключ)

> Примечание: Для запуска проекта нужен .env файл в корневой директории с двумя переменными - сертификатом и приватным ключом, закодированным в base64:

```
JSONRPC_CLIENT_CERT_PEM=BASE64-содержимого.cert
JSONRPC_CLIENT_KEY_PEM=BASE64-содержимого.key
``` 

Сделал так для того, чтобы не публиковать содержимое сертификатов в репозиторий. Изначально просто в настройках указывал в виде многострочной строки.

Получить base64 можно из PEM-файлов следующими командами

```bash
base64 -w0 client2026test.crt
base64 -w0 client2026test.key
```

на macOS вместо '-w0' используйте '-b 0'

## Запуск и тестирование

Проект использует только Python-стандартную библиотеку + Django, поэтому зависимость всего одна.

### Вариант 1 — uv (рекомендуется)

> Как установить: [ссылка](https://docs.astral.sh/uv/getting-started/installation/)

```bash
uv sync
uv run manage.py test
uv run manage.py runserver
```

### Вариант 2 — pip + venv

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py test
python manage.py runserver
```

### Вариант 3 — Docker

```bash
docker build -t django-jsonrpc .
docker run --rm -p 8000:8000 django-jsonrpc
```

Прогнать тесты внутри контейнера:

```bash
docker run --rm django-jsonrpc uv run python manage.py test
```

Приложение будет доступно на `http://127.0.0.1:8000/`.