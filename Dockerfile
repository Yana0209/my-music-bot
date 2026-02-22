FROM python:3.10-slim

# Встановлюємо FFmpeg та інструменти для мережі
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копіюємо всі файли (включаючи cookies.txt, якщо він уже є в папці)
COPY . .

# Оновлюємо pip та встановлюємо бібліотеки
# Додаємо --upgrade для yt-dlp, щоб він завжди був найсвіжішої версії
RUN pip install --upgrade pip
RUN pip install --no-cache-dir aiogram yt-dlp --upgrade

# Вказуємо шлях до FFmpeg явно
# У коді ми шукаємо саме FFMPEG_LOCATION, тому додаємо цей рядок
ENV FFMPEG_LOCATION=/usr/bin/ffmpeg
ENV FFMPEG_BINARY=/usr/bin/ffmpeg

# Запуск бота
CMD ["python", "main.py"]
