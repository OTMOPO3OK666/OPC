FROM python:3.14-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости и ставим пакеты
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . .

CMD ["python", "-m", "app.main_async"]
