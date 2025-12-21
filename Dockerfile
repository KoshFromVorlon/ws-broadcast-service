FROM python:3.12-slim

WORKDIR /app

# Запрещаем Python писать .pyc файлы и включаем немедленный вывод логов
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Запуск с 4 воркерами.
# --no-signal-handlers позволяет нашему коду в signals.py самому управлять
# процессом закрытия, не блокируя сокеты раньше времени.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--no-signal-handlers"]