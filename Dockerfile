FROM python:3.10-slim

# Встановлюємо FFmpeg та інструменти для мережі
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копіюємо файли
COPY . .

# Оновлюємо pip та встановлюємо бібліотеки з форсованою версією yt-dlp
RUN pip install --upgrade pip
RUN pip install --no-cache-dir aiogram yt-dlp

# Вказуємо шлях до FFmpeg явно (це вирішить помилку "does not exist")
ENV FFMPEG_BINARY=/usr/bin/ffmpeg

# Запуск бота
CMD ["python", "main.py"]
