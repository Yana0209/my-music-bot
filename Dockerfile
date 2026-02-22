FROM python:3.10-slim

# Встановлюємо FFmpeg (без нього музика не завантажиться)
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

WORKDIR /app

# Копіюємо всі файли з GitHub
COPY . .

# Встановлюємо бібліотеки
RUN pip install --no-cache-dir aiogram yt-dlp

# Запуск бота
CMD ["python", "main.py"]
