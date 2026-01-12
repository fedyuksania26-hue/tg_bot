import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from yadisk import YaDisk
from dotenv import load_dotenv

# Загрузка переменных из .env
load_dotenv()

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и Яндекс Диска
bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
dp = Dispatcher()
ydisk = YaDisk(token=os.getenv("YANDEX_DISK_TOKEN"))

# Состояние пользователя
user_state = {}  # {user_id: {"order_id": None, "photos": []}}

@dp.message(Command("start"))
async def start(message: types.Message):
    user_state[message.from_user.id] = {"order_id": None, "photos": []}
    await message.answer("Введите номер заказа:")

@dp.message(F.text & ~F.command())
async def get_order_id(message: types.Message):
    user_id = message.from_user.id
    if user_state[user_id]["order_id"] is None:
        user_state[user_id]["order_id"] = message.text
        await message.answer("Загрузите фотографии (до 200 штук):")
    else:
        await message.answer("Отправьте фото, а не текст.")

@dp.message(F.photo)
async def handle_photos(message: types.Message):
    user_id = message.from_user.id
    order_id = user_state[user_id]["order_id"]
    
    if order_id is None:
        await message.answer("Сначала введите номер заказа.")
        return

    # Сохраняем фото (ID файла Telegram)
    user_state[user_id]["photos"].append(message.photo[-1].file_id)

    if len(user_state[user_id]["photos"]) >= 200:
        await process_photos(user_id, order_id)
        await message.answer("Ваши фото приняты.")
    else:
        await message.answer(f"Фото сохранено. Осталось загрузить {200 - len(user_state[user_id]['photos'])} фото.")

async def process_photos(user_id: int, order_id: str):
    # Создаем папку на Яндекс Диске
    folder_path = f"/{order_id}"
    try:
        ydisk.mkdir(folder_path)
    except Exception as e:
        logger.error(f"Ошибка создания папки: {e}")

    # Загружаем фото
    for photo_id in user_state[user_id]["photos"]:
        file_info = await bot.get_file(photo_id)
        file_url = f"https://api.telegram.org/file/bot{os.getenv('TELEGRAM_TOKEN')}/{file_info.file_path}"
        
        # Скачиваем фото и загружаем на Диск
        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as resp:
                photo_data = await resp.read()
                ydisk.upload(photo_data, f"{folder_path}/{photo_id}.jpg")

    # Очищаем состояние
    user_state[user_id] = {"order_id": None, "photos": []}

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
