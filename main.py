import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from utils.downloader import search_music, download_audio

# Твій токен
API_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Словник для зберігання результатів пошуку
search_cache = {}

# Функція для постійної кнопки знизу
def get_main_menu():
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="🔍 Знайти музику"))
    return builder.as_markup(resize_keyboard=True)

# Функція для клавіатури зі сторінками
def get_music_keyboard(query_id, page=0):
    results = search_cache.get(query_id, [])
    items_per_page = 5
    start_index = page * items_per_page
    end_index = start_index + items_per_page
    current_items = results[start_index:end_index]

    builder = InlineKeyboardBuilder()
    for res in current_items:
        button_text = f"{res['title'][:40]} ({res['duration']})"
        builder.row(types.InlineKeyboardButton(
            text=button_text, 
            callback_data=f"dl_{res['id']}")
        )
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"page_{query_id}_{page-1}"))
    if end_index < len(results):
        nav_buttons.append(types.InlineKeyboardButton(text="Вперед ➡️", callback_data=f"page_{query_id}_{page+1}"))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    return builder.as_markup()

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "Привіт! Я твій музичний бот. 🎵\nПривіт! Я твій музичний бот. Напиши назву пісні, автора або ключові слова і я допоможу тобі з пошуком! 🎵.",
        reply_markup=get_main_menu()
    )

@dp.message(F.text == "🔍 Знайти музику")
async def btn_search_handler(message: types.Message):
    await message.answer("Введіть назву пісні або виконавця, якого хочете знайти: ⌨️")

@dp.message(F.text)
async def handle_search(message: types.Message):
    # Якщо користувач написав щось інше (назву пісні)
    query = message.text
    status_msg = await message.answer(f"Шукаю «{query}»... 🔍")
    
    results = search_music(query)
    if not results:
        await status_msg.edit_text("Нічого не знайдено. 😔")
        return

    query_id = str(abs(hash(query)))
    search_cache[query_id] = results
    
    await status_msg.edit_text(
        f"Ось що я знайшов за запитом «{query}»:", 
        reply_markup=get_music_keyboard(query_id, 0)
    )

@dp.callback_query(F.data.startswith("page_"))
async def process_page(callback: types.CallbackQuery):
    _, query_id, page = callback.data.split("_")
    await callback.message.edit_reply_markup(reply_markup=get_music_keyboard(query_id, int(page)))
    await callback.answer()

@dp.callback_query(F.data.startswith("dl_"))
async def process_download(callback: types.CallbackQuery):
    video_id = callback.data.split("_")[1]
    
    # Знаходимо назву пісні в кеші за ID
    song_title = "пісню"
    for q_id in search_cache:
        for item in search_cache[q_id]:
            if item['id'] == video_id:
                song_title = item['title']
                break

    # 1. Надсилаємо повідомлення про початок завантаження
    wait_msg = await callback.message.answer(f"Завантажую «{song_title[:30]}...» ⏳\nЦе займе кілька секунд...")
    
    try:
        # 2. Завантаження
        file_path = download_audio(video_id)
        audio = types.FSInputFile(file_path)
        
        # 3. Надсилаємо музику
        await callback.message.answer_audio(audio)
        
        # 4. Видаляємо повідомлення "Зачекайте", коли все готово
        await wait_msg.delete()
        await callback.answer("Готово! ✅")
        
    except Exception as e:
        await wait_msg.edit_text(f"Помилка завантаження: {e}")

async def main():
    print("Бот запущений!")
    await dp.start_polling(bot)

if __name__ == "__main__":

    asyncio.run(main())

