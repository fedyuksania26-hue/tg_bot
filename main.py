import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from yadisk import YaDisk
from dotenv import load_dotenv

# Загрузка переменных из .env
load_dotenv()

# Инициализация бота
bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
dp = Dispatcher()

# Клиент Яндекс Диска
ydisk = YaDisk(token=os.getenv("YANDEX_DISK_TOKEN"))

# Хранилище для фото (user_id → список file_ids)
user_photos = {}



@dp.message(F.text)
async def handle_text(message: types.Message):
    """
    Реагирует на любое текстовое сообщение.
    Если текст — «Готово», сохраняем фото на Диск.
    Иначе — напоминаем про фото.
    """
    if message.text.strip().lower() == "готово":
        user_id = message.from_user.id
        photos = user_photos.get(user_id, [])

        if not photos:
            await message.answer("Вы не отправили ни одного фото. Отправьте фото, а затем напишите «Готово».")
            return

        # Создаём папку на Яндекс Диске (по user_id)
        folder_path = f"/telegram_photos/{user_id}"
        try:
            await ydisk.mkdir(folder_path)
        except Exception as e:
            # Папка уже может существовать
            pass

        # Скачиваем и загружаем фото
        for idx, file_id in enumerate(photos, 1):
            # Получаем информацию о файле
            file = await bot.get_file(file_id)
            file_path = file.file_path

            # Скачиваем фото в память
            photo_data = await bot.download_file(file_path)

            # Загружаем на Яндекс Диск
            upload_path = f"{folder_path}/photo_{idx}.jpg"
            await ydisk.upload(photo_data, upload_path)

        await message.answer(f"✅ Все фото сохранены на Яндекс Диск в папку: {folder_path}")
        # Очищаем хранилище для этого пользователя
        user_photos[user_id] = []
    else:
        await message.answer("Отправьте фото. Когда закончите, напишите «Готово».")



@dp.message(F.photo)
async def handle_photo(message: types.Message):
    """
    Сохраняет file_id каждого фото в хранилище.
    """
    user_id = message.from_user.id

    # Инициализируем список для пользователя
    if user_id not in user_photos:
        user_photos[user_id] = []

    # Добавляем file_id последнего фото
    user_photos[user_id].append(message.photo[-1].file_id)

    await message.answer(f"Фото принято (всего: {len(user_photos[user_id])}). Отправьте ещё или напишите «Готово».")




async def main():
    await dp.start_polling(bot)



if __name__ == "__main__":
    asyncio.run(main())
