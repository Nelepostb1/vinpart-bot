import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

class RequestForm(StatesGroup):
    vin = State()
    phone = State()
    part = State()
    photo = State()

builder = ReplyKeyboardBuilder()
builder.button(text="ℹ️ О нас")
builder.button(text="📝 Оставить заявку")
keyboard = builder.as_markup(resize_keyboard=True)

active_chats = {}

@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer("🌞 Привет! Я бот VINPART — подбор автозапчастей по VIN.", reply_markup=keyboard)

@dp.message(F.text == "ℹ️ О нас")
async def about(message: Message):
    await message.answer("🛠 VINPART — подбор запчастей по VIN.\n📞 +7 999 123-45-67")

@dp.message(F.text == "📝 Оставить заявку")
async def start_form(message: Message, state: FSMContext):
    await message.answer("Введите VIN номер:")
    await state.set_state(RequestForm.vin)

@dp.message(RequestForm.vin)
async def process_vin(message: Message, state: FSMContext):
    await state.update_data(vin=message.text)
    await message.answer("Введите номер телефона:")
    await state.set_state(RequestForm.phone)

@dp.message(RequestForm.phone)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("Введите название или описание детали:")
    await state.set_state(RequestForm.part)

@dp.message(RequestForm.part)
async def process_part(message: Message, state: FSMContext):
    await state.update_data(part=message.text)
    await message.answer("Если у вас есть фото детали — отправьте его сейчас.\nИли напишите слово 'нет', если фото нет.")
    await state.set_state(RequestForm.photo)

@dp.message(RequestForm.photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photo_id = message.photo[-1].file_id
    text = (
        f"<b>📥 Новая заявка</b>\n\n"
        f"VIN: {data['vin']}\n"
        f"Телефон: {data['phone']}\n"
        f"Деталь: {data['part']}"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="📩 Ответить", callback_data=f"reply:{message.chat.id}")
    await bot.send_photo(chat_id=ADMIN_ID, photo=photo_id, caption=text, reply_markup=builder.as_markup())
    await message.answer("✅ Заявка отправлена!")
    await state.clear()

@dp.message(RequestForm.photo)
async def no_photo(message: Message, state: FSMContext):
    if message.text.lower() == "нет":
        data = await state.get_data()
        text = (
            f"<b>📥 Новая заявка</b>\n\n"
            f"VIN: {data['vin']}\n"
            f"Телефон: {data['phone']}\n"
            f"Деталь: {data['part']}"
        )
        builder = InlineKeyboardBuilder()
        builder.button(text="📩 Ответить", callback_data=f"reply:{message.chat.id}")
        await bot.send_message(chat_id=ADMIN_ID, text=text, reply_markup=builder.as_markup())
        await message.answer("✅ Заявка отправлена!")
        await state.clear()

@dp.callback_query(F.data.startswith("reply:"))
async def handle_reply_button(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Только администратор может отвечать!", show_alert=True)
        return
    user_id = int(callback.data.split(":")[1])
    active_chats[ADMIN_ID] = user_id
    await callback.message.answer("✍️ Введите сообщение клиенту.\nДля завершения — /stopchat")

@dp.message(F.text == "/stopchat")
async def stop_chat(message: Message):
    if ADMIN_ID in active_chats:
        del active_chats[ADMIN_ID]
        await message.answer("✅ Чат с клиентом завершён.")

@dp.message(F.photo)
async def relay_photo_to_admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        if ADMIN_ID in active_chats and active_chats[ADMIN_ID] == message.from_user.id:
            photo_id = message.photo[-1].file_id
            await bot.send_photo(chat_id=ADMIN_ID, photo=photo_id, caption=f"🖼 Фото от клиента {message.from_user.id}")
        else:
            photo_id = message.photo[-1].file_id
            builder = InlineKeyboardBuilder()
            builder.button(text="📩 Ответить", callback_data=f"reply:{message.from_user.id}")
            await bot.send_photo(chat_id=ADMIN_ID, photo=photo_id, caption=f"🗨 Новое фото от клиента {message.from_user.id}", reply_markup=builder.as_markup())

@dp.message()
async def relay_messages(message: Message):
    if message.from_user.id == ADMIN_ID and ADMIN_ID in active_chats:
        client_id = active_chats[ADMIN_ID]
        await bot.send_message(chat_id=client_id, text=message.text)
        await message.answer("✅ Ответ отправлен.")
    elif message.from_user.id != ADMIN_ID:
        builder = InlineKeyboardBuilder()
        builder.button(text="📩 Ответить", callback_data=f"reply:{message.from_user.id}")
        await bot.send_message(chat_id=ADMIN_ID, text=f"💬 Новое сообщение от клиента {message.from_user.id}:\n{message.text}", reply_markup=builder.as_markup())

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
