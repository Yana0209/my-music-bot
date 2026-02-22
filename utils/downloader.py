import yt_dlp
import os

# Створюємо папку для завантажень, якщо її немає
if not os.path.exists('downloads'):
    os.makedirs('downloads')

# Допоміжна функція для перетворення секунд у формат 00:00
def format_duration(seconds):
    if not seconds:
        return "??:??"
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes}:{seconds:02d}"

def search_music(query):
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'extract_flat': True,
        # Додаємо використання куків для пошуку, щоб YouTube не блокував запити
        'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Шукаємо 20 варіантів
        info = ydl.extract_info(f"ytsearch20:{query}", download=False)
        
        results = []
        if 'entries' in info:
            for e in info['entries']:
                results.append({
                    "id": e['id'], 
                    "title": e['title'],
                    "duration": format_duration(e.get('duration'))
                })
        return results

def download_audio(video_id):
    file_path = f"downloads/{video_id}.mp3"
    
    if os.path.exists(file_path):
        return file_path

    # Отримуємо шлях до FFmpeg з налаштувань системи (для Render)
    ffmpeg_path = os.getenv('FFMPEG_LOCATION', 'ffmpeg')

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'downloads/{video_id}.%(ext)s',
        'ffmpeg_location': ffmpeg_path, 
        # Додаємо cookies.txt для завантаження
        'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': False, # Ставимо False, щоб бачити помилки в логах Render, якщо вони будуть
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
    
    return file_path
