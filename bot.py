import asyncio
import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, ContentType
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from database import Database
from config import BOT_TOKEN

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
db = Database()

class Registration(StatesGroup):
    full_name = State()
    birth_date = State()
    phone = State()

def main_menu():
    buttons = [
        [KeyboardButton(text="📋 Оставить заявку")],
        [KeyboardButton(text="📞 Контакты")],
        [KeyboardButton(text="ℹ️ Информация о компании")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def contacts_keyboard():
    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Перейти на сайт", url="https://example.com")]
    ])
    return buttons

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await message.answer("Привет! Давай зарегистрируемся.\n\nВведите ФИО:")
    await state.set_state(Registration.full_name)

@dp.message(Registration.full_name)
async def process_full_name(message: Message, state: FSMContext):
    full_name = message.text.strip()
    if len(full_name.split()) < 2:
        await message.answer("Пожалуйста, введите ФИО полностью (минимум имя и фамилия).")
        return
    await state.update_data(full_name=full_name)
    await message.answer("Введите дату рождения в формате ДД.ММ.ГГГГ (например, 31.12.1990):")
    await state.set_state(Registration.birth_date)

@dp.message(Registration.birth_date)
async def process_birth_date(message: Message, state: FSMContext):
    date_str = message.text.strip()
    try:
        birth_date = datetime.datetime.strptime(date_str, "%d.%m.%Y").date()
    except ValueError:
        await message.answer("❌ Ошибка! Дата должна быть в формате ДД.ММ.ГГГГ. Попробуйте ещё раз:")
        return
    await state.update_data(birth_date=birth_date)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отправить номер телефона", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("Пожалуйста, отправьте ваш номер телефона, нажав кнопку ниже ⬇️", reply_markup=keyboard)
    await state.set_state(Registration.phone)

@dp.message(Registration.phone, F.content_type == ContentType.CONTACT)
async def process_phone(message: Message, state: FSMContext):
    contact = message.contact
    if contact is None or contact.user_id != message.from_user.id:
        await message.answer("Пожалуйста, отправьте именно ваш контакт через кнопку.")
        return
    phone = contact.phone_number
    data = await state.get_data()
    full_name = data.get('full_name')
    birth_date = data.get('birth_date')  # Объект datetime.date

    try:
        # Передаём объект datetime.date напрямую
        await db.add_user(full_name, birth_date, phone)
        await message.answer("✅ Регистрация завершена! Добро пожаловать!", reply_markup=main_menu())
        await state.clear()
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка при регистрации: {e}")

@dp.message(F.text == "ℹ️ Информация о компании")
async def info_company(message: Message):
    text = (
        "🏢 *Наша компания*\n\n"
        "Мы — лидеры рынка с 2010 года, предоставляем качественные услуги по созданию тг ботов\n"
        "🌟 Надежность, профессионализм и индивидуальный подход — наши главные ценности."
    )
    photo_url = "https://cdn-icons-png.flaticon.com/512/190/190411.png"
    await message.answer_photo(photo=photo_url, caption=text, parse_mode="Markdown")

@dp.message(F.text == "📞 Контакты")
async def contacts(message: Message):
    text = (
        "📞 Контактный телефон: +7 (999) 123-45-67\n"
        "📧 Email: info@marsdev.com\n"
        "📍 Адрес: г. Москва, ул. Сайкина, д. 1"
    )
    await message.answer(text, reply_markup=contacts_keyboard())

@dp.message(F.text == "📋 Оставить заявку")
async def leave_request(message: Message):
    await message.answer("⚙️ Блок в разработке 🔧")

async def main():
    await db.connect()
    await db.create_tables()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
