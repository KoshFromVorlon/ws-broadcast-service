FROM python:3.12-slim

WORKDIR /app

# Запрещаем Python писать .pyc файлы и включаем немедленный вывод логов
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Запуск с 4 воркерами согласно ТЗ
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]