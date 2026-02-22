import os
import asyncio
import logging
from aiohttp import web  # Додано для Render
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from utils.downloader import search_music, download_audio

# Налаштування логування
logging.basicConfig(level=logging.INFO)

# Твій токен
API_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Словник для зберігання результатів пошуку
search_cache = {}
# Глобальний лічильник для надкоротких ID пошуку
search_counter = 0

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
        # Обмежуємо текст назви
        button_text = f"{res['title'][:35]} ({res['duration']})"
        # d:VIDEO_ID - найкоротший формат
        builder.row(types.InlineKeyboardButton(
            text=button_text, 
            callback_data=f"d:{res['id']}")
        )
    
    nav_buttons = []
    # p:Q_ID:PAGE
    if page > 0:
        nav_buttons.append(types.InlineKeyboardButton(text="⬅️", callback_data=f"p:{query_id}:{page-1}"))
    if end_index < len(results):
        nav_buttons.append(types.InlineKeyboardButton(text="➡️", callback_data=f"p:{query_id}:{page+1}"))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    return builder.as_markup()

# --- Хендлери ---
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "Привіт! Я твій музичний бот. Напиши назву пісні і я допоможу з пошуком! 🎵",
        reply_markup=get_main_menu()
    )

@dp.message(F.text == "🔍 Знайти музику")
async def btn_search_handler(message: types.Message):
    await message.answer("Введіть назву пісні або виконавця: ⌨️")

@dp.message(F.text)
async def handle_search(message: types.Message):
    global search_counter
    query = message.text
    status_msg = await message.answer(f"Шукаю «{query}»... 🔍")
    
    results = search_music(query)
    if not results:
        await status_msg.edit_text("Нічого не знайдено. 😔")
        return

    # Створюємо максимально короткий числовий ID (1, 2, 3...)
    search_counter += 1
    query_id = str(search_counter)
    search_cache[query_id] = results
    
    await status_msg.edit_text(
        f"Ось що я знайшов за запитом «{query}»:", 
        reply_markup=get_music_keyboard(query_id, 0)
    )

@dp.callback_query(F.data.startswith("p:"))
async def process_page(callback: types.CallbackQuery):
    # Розбираємо p:query_id:page
    data = callback.data.split(":")
    query_id = data[1]
    page = int(data[2])
    await callback.message.edit_reply_markup(reply_markup=get_music_keyboard(query_id, page))
    await callback.answer()

@dp.callback_query(F.data.startswith("d:"))
async def process_download(callback: types.CallbackQuery):
    video_id = callback.data.split(":")[1]
    
    song_title = "пісню"
    for q_id in search_cache:
        for item in search_cache[q_id]:
            if item['id'] == video_id:
                song_title = item['title']
                break

    wait_msg = await callback.message.answer(f"Завантажую «{song_title[:30]}...» ⏳")
    
    try:
        file_path = download_audio(video_id)
        audio = types.FSInputFile(file_path)
        await callback.message.answer_audio(audio)
        await wait_msg.delete()
        await callback.answer("Готово! ✅")
    except Exception as e:
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
