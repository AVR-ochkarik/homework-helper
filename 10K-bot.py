import asyncio
import datetime
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json
import os
from dotenv import load_dotenv

load_dotenv()

DB_FILE = "homework_data.json"
logging.basicConfig(level=logging.INFO)

def load_homework():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_homework(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


TOKEN = os.getenv("TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
TOPIC_ID = int(os.getenv("TOPIC_ID"))
MY_USER_ID = int(os.getenv("MY_USER_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher()

homework_storage = load_homework()

SUBJECTS = ["матан", "физика", "геома", "тервер", "алгебра"]
SCHEDULE = {
    2: ["матан", "тервер", "физика"],
    3: ["физика", "геома"],
    4: ["алгебра"]
}

DAYS_NAMES = {"Среда": 2, "Четверг": 3, "Пятница": 4}

@dp.message(F.chat.id == GROUP_ID, F.photo)
async def collect_homework(message: types.Message):
    if message.from_user.id == MY_USER_ID:
        if message.caption:
            caption_lower = message.caption.lower()
            for sub in SUBJECTS:
                if sub in caption_lower:
                    homework_storage[sub] = message.photo[-1].file_id
                    save_homework(homework_storage)
                    logging.info(f"Запомнил ДЗ по предмету: {sub}")



def get_main_kb():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="ДЗ на завтра", callback_data="hw_tomorrow"))
    builder.row(types.InlineKeyboardButton(text="ДЗ по предметам", callback_data="hw_subjects"))
    builder.row(types.InlineKeyboardButton(text="ДЗ по дням", callback_data="hw_days"))
    return builder.as_markup()


def get_subjects_kb():
    builder = InlineKeyboardBuilder()
    for sub in SUBJECTS:
        builder.button(text=sub.capitalize(), callback_data=f"find_{sub}")
    builder.button(text="⬅️ Назад", callback_data="main_menu")
    builder.adjust(2)
    return builder.as_markup()


def get_days_kb():
    builder = InlineKeyboardBuilder()
    for day_name in DAYS_NAMES.keys():
        builder.button(text=day_name, callback_data=f"day_{DAYS_NAMES[day_name]}")
    builder.button(text="⬅️ Назад", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Выберите режим просмотра ДЗ:", reply_markup=get_main_kb())


@dp.callback_query(F.data == "main_menu")
async def main_menu(callback: types.CallbackQuery):
    await callback.message.edit_text("Выберите режим просмотра ДЗ:", reply_markup=get_main_kb())


@dp.callback_query(F.data == "hw_subjects")
async def show_subjects(callback: types.CallbackQuery):
    await callback.message.edit_text("Выберите предмет:", reply_markup=get_subjects_kb())


@dp.callback_query(F.data.startswith("find_"))
async def search_hw_subject(callback: types.CallbackQuery):
    subject = callback.data.split("_")[1]
    photo_id = homework_storage.get(subject)

    if photo_id:
        await callback.message.answer_photo(photo=photo_id, caption=f"📚 Последнее ДЗ: {subject}")
    else:
        await callback.message.answer(f"Бот еще не видел фото по предмету {subject} с момента запуска.")
    await callback.answer()


@dp.callback_query(F.data == "hw_tomorrow")
async def search_hw_tomorrow(callback: types.CallbackQuery):
    tomorrow = (datetime.datetime.now().weekday() + 1) % 7
    subjects = SCHEDULE.get(tomorrow)

    if not subjects:
        await callback.answer("Завтра уроков нет!", show_alert=True)
        return

    found = False
    for sub in subjects:
        photo_id = homework_storage.get(sub)
        if photo_id:
            await callback.message.answer_photo(photo=photo_id, caption=f"📚 Завтра: {sub}")
            found = True

    if not found:
        await callback.message.answer("Ни одно ДЗ на завтра еще не было загружено в память бота.")
    await callback.answer()


@dp.callback_query(F.data == "hw_days")
async def show_days(callback: types.CallbackQuery):
    await callback.message.edit_text("Выберите день недели:", reply_markup=get_days_kb())


@dp.callback_query(F.data.startswith("day_"))
async def search_hw_day(callback: types.CallbackQuery):
    day_index = int(callback.data.split("_")[1])
    subjects = SCHEDULE.get(day_index)

    found = False
    for sub in subjects:
        photo_id = homework_storage.get(sub)
        if photo_id:
            await callback.message.answer_photo(photo=photo_id, caption=f"📚 {sub}")
            found = True

    if not found:
        await callback.message.answer("ДЗ на этот день не найдено в памяти.")
    await callback.answer()


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
