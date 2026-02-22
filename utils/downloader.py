import yt_dlp
import os

if not os.path.exists('downloads'):
    os.makedirs('downloads')

COOKIES_PATH = os.path.join(os.getcwd(), 'cookies.txt')

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
        'cookiefile': COOKIES_PATH if os.path.exists(COOKIES_PATH) else None,
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

    ffmpeg_path = os.getenv('FFMPEG_LOCATION', '/usr/bin/ffmpeg')

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'downloads/{video_id}.%(ext)s',
        'ffmpeg_location': ffmpeg_path, 
        'cookiefile': COOKIES_PATH if os.path.exists(COOKIES_PATH) else None,
        
        # Використовуємо інший метод обходу (iOS)
        'youtube_include_dash_manifest': False,
        'client_name': 'ios',
        'client_version': '19.29.1',
        
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': False,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'user_agent': 'com.google.ios.youtube/19.29.1 (iPhone16,2; U; CPU iOS 17_5_1 like Mac OS X; en_US)'
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
    
    return file_path
