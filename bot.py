import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandObject
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from db import init_db, get_db

# ───────── НАСТРОЙКИ ─────────
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")  # токен візьметься з налаштувань Render, а не з коду
OWNER_ID = 7059576652
OWNER_TAG = "@kalev12"

FREE_TRIALS = 3

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

# ───────── DB HELPERS ─────────
def get_user(user_id: int):
    with get_db() as db:
        cur = db.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
            (user_id,)
        )
        db.commit()

        cur.execute(
            "SELECT used, sub, active FROM users WHERE user_id = ?",
            (user_id,)
        )
        return cur.fetchone()

def update_user(user_id: int, **kwargs):
    with get_db() as db:
        for key, value in kwargs.items():
            db.execute(
                f"UPDATE users SET {key} = ? WHERE user_id = ?",
                (value, user_id)
            )
        db.commit()

def add_pending(owner_msg_id: int, user_id: int):
    with get_db() as db:
        db.execute(
            "INSERT INTO pending (owner_msg_id, user_id) VALUES (?, ?)",
            (owner_msg_id, user_id)
        )
        db.commit()

def pop_pending(owner_msg_id: int):
    with get_db() as db:
        cur = db.cursor()
        cur.execute(
            "SELECT user_id FROM pending WHERE owner_msg_id = ?",
            (owner_msg_id,)
        )
        row = cur.fetchone()
        if row:
            db.execute(
                "DELETE FROM pending WHERE owner_msg_id = ?",
                (owner_msg_id,)
            )
            db.commit()
            return row[0]
        return None

# ───────── /start ─────────
@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    used, sub, active = get_user(user_id)

    await message.answer(
        "🍌 Нано Банана — ДЗ як в зошиті\n\n"
        f"Безкоштовні спроби: {FREE_TRIALS - used if not sub else '∞'}\n\n"
        "✏️ Напиши:\n"
        "/gen [завдання]"
    )

# ───────── /gen ─────────
@dp.message(Command("gen"))
async def gen(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    prompt = command.args

    if not prompt:
        await message.answer("Напиши завдання після /gen")
        return

    used, sub, active = get_user(user_id)

    if active:
        await message.answer("⏳ Твій запит уже в обробці")
        return

    if not sub and used >= FREE_TRIALS:
        await message.answer("❌ Ліміт безкоштовних спроб вичерпано")
        return

    owner_msg = await bot.send_message(
        OWNER_ID,
        f"🆕 ЗАПИТ\n\n"
        f"👤 ID: {user_id}\n"
        f"✏️ {prompt}\n\n"
        f"➡️ ВІДПОВІДАЙ ФОТО НА ЦЕ ПОВІДОМЛЕННЯ"
    )

    add_pending(owner_msg.message_id, user_id)
    update_user(user_id, active=1)

    if not sub:
        update_user(user_id, used=used + 1)

    await message.answer("⏳ Запит прийнято, чекай 🍌")

# ───────── OWNER ANSWER ─────────
@dp.message(lambda m: m.from_user.id == OWNER_ID and m.reply_to_message)
async def owner_reply(message: types.Message):
    owner_msg_id = message.reply_to_message.message_id
    user_id = pop_pending(owner_msg_id)

    if not user_id:
        return

    update_user(user_id, active=0)

    try:
        if message.photo:
            await bot.send_photo(
                user_id,
                message.photo[-1].file_id,
                caption="🍌 Готово!"
            )
        else:
            await bot.send_message(user_id, "🍌 Готово!")

        await message.answer("✅ Відправлено користувачу")
    except Exception as e:
        await message.answer(f"❌ Помилка: {e}")

# ───────── START ─────────
async def main():
    init_db()
    print("🍌 Бот готовий до роботи")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())