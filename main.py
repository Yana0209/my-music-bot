import os
import asyncio
import logging
from aiohttp import web  # Додано для Render
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from utils.downloader import search_music, download_audio

# Налаштування логування, щоб бачити помилки в панелі Render
logging.basicConfig(level=logging.INFO)

# Твій токен
API_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Словник для зберігання результатів пошуку
search_cache = {}

# --- Секція для Render (Web Server) ---
async def handle(request):
    return web.Response(text="Bot is running")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Web server started on port {port}")

# --- Функції клавіатури ---
def get_main_menu():
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="🔍 Знайти музику"))
    return builder.as_markup(resize_keyboard=True)

def get_music_keyboard(query_id, page=0):
    results = search_cache.get(query_id, [])
    items_per_page = 5
    start_index = page * items_per_page
    end_index = start_index + items_per_page
    current_items = results[start_index:end_index]

    builder = InlineKeyboardBuilder()
    for res in current_items:
        # Обмежуємо текст назви, щоб кнопка була акуратною
        button_text = f"{res['title'][:35]} ({res['duration']})"
        # Використовуємо короткий префікс 'd:', щоб не перевищити ліміт 64 байти
        builder.row(types.InlineKeyboardButton(
            text=button_text, 
            callback_data=f"d:{res['id']}")
        )
    
    nav_buttons = []
    # Короткі callback_data для навігації 'p:query_id:page'
    if page > 0:
        nav_buttons.append(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"p:{query_id}:{page-1}"))
    if end_index < len(results):
        nav_buttons.append(types.InlineKeyboardButton(text="Вперед ➡️", callback_data=f"p:{query_id}:{page+1}"))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    return builder.as_markup()

# --- Хендлери ---
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "Привіт! Я твій музичний бот. Напиши назву пісні, автора або ключові слова і я допоможу тобі з пошуком! 🎵",
        reply_markup=get_main_menu()
    )

@dp.message(F.text == "🔍 Знайти музику")
async def btn_search_handler(message: types.Message):
    await message.answer("Введіть назву пісні або виконавця, якого хочете знайти: ⌨️")

@dp.message(F.text)
async def handle_search(message: types.Message):
    query = message.text
    status_msg = await message.answer(f"Шукаю «{query}»... 🔍")
    
    results = search_music(query)
    if not results:
        await status_msg.edit_text("Нічого не знайдено. 😔")
        return

    # Робимо query_id максимально коротким для економії місця в callback_data
    query_id = str(abs(hash(query)) % 1000000)
    search_cache[query_id] = results
    
    await status_msg.edit_text(
        f"Ось що я знайшов за запитом «{query}»:", 
        reply_markup=get_music_keyboard(query_id, 0)
    )

@dp.callback_query(F.data.startswith("p:"))
async def process_page(callback: types.CallbackQuery):
    # Розбираємо коротку команду p:query_id:page
    _, query_id, page = callback.data.split(":")
    await callback.message.edit_reply_markup(reply_markup=get_music_keyboard(query_id, int(page)))
    await callback.answer()

@dp.callback_query(F.data.startswith("d:"))
async def process_download(callback: types.CallbackQuery):
    # Отримуємо чистий video_id після d:
    video_id = callback.data.split(":")[1]
    
    song_title = "пісню"
    # Шукаємо назву в кеші
    for q_id in search_cache:
        for item in search_cache[q_id]:
            if item['id'] == video_id:
                song_title = item['title']
                break

    wait_msg = await callback.message.answer(f"Завантажую «{song_title[:30]}...» ⏳\nЦе займе кілька секунд...")
    
    try:
        file_path = download_audio(video_id)
        audio = types.FSInputFile(file_path)
        await callback.message.answer_audio(audio)
        await wait_msg.delete()
        await callback.answer("Готово! ✅")
    except Exception as e:
        # Виводимо помилку в чат для діагностики
        await wait_msg.edit_text(f"Помилка завантаження: {e}")

# --- Запуск ---
async def main():
    asyncio.create_task(start_web_server())
    print("Бот запущений!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот зупинений")
