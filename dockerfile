FROM python:3.14-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости и ставим пакеты
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . .

# Команда запуска: можно указать конкретный скрипт или точку входа
# Здесь предполагаем, что есть главный скрипт, который стартует оба сервера
CMD ["python", "-m", "app.main_async"]