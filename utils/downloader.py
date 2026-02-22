import yt_dlp
import os

# Створюємо папку для завантажень, якщо її немає
if not os.path.exists('downloads'):
    os.makedirs('downloads')

# Визначаємо шлях до куків у головній папці проекту
# os.getcwd() завжди повертає кореневу папку на Render
COOKIES_PATH = os.path.join(os.getcwd(), 'cookies.txt')

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
        # Використовуємо куки за правильним шляхом
        'cookiefile': COOKIES_PATH if os.path.exists(COOKIES_PATH) else None,
        # Додаткові налаштування для стабільності
        'nocheckcertificate': True,
        'geo_bypass': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
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

    # Отримуємо шлях до FFmpeg з налаштувань Dockerfile
    ffmpeg_path = os.getenv('FFMPEG_LOCATION', '/usr/bin/ffmpeg')

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'downloads/{video_id}.%(ext)s',
        'ffmpeg_location': ffmpeg_path, 
        # Використовуємо куки за правильним шляхом
        'cookiefile': COOKIES_PATH if os.path.exists(COOKIES_PATH) else None,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': False,
        'nocheckcertificate': True,
        'geo_bypass': True,
        # Додаємо "людський" User-Agent
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
    
    return file_path
