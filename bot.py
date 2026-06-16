import asyncio
import logging
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

import asyncpg
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

db: asyncpg.Pool = None


async def init_db():
    global db
    db = await asyncpg.create_pool(os.getenv("DATABASE_URL"))
    await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          BIGINT PRIMARY KEY,
            username    TEXT,
            full_name   TEXT,
            joined_at   TIMESTAMP DEFAULT NOW()
        )
    """)
    logging.info("DB ulandi va jadval tayyor!")


async def save_user(user):
    await db.execute("""
        INSERT INTO users (id, username, full_name)
        VALUES ($1, $2, $3)
        ON CONFLICT (id) DO NOTHING
    """, user.id, user.username, user.full_name)


@dp.message(CommandStart())
async def start_handler(message: Message):
    await save_user(message.from_user)
    await message.answer(
        f"👋 Salom, {message.from_user.first_name}!\n\n"
        f"Men echo botman — yozgan xabaringizni qaytaraman.\n\n"
        f"📌 Commandlar:\n"
        f"/start — Botni ishga tushirish\n"
        f"/help — Yordam\n"
        f"/me — Mening ma'lumotlarim"
    )


@dp.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(
        "ℹ️ Yordam:\n\n"
        "Menga istalgan xabar yozing — aynan o'sha xabarni qaytaraman.\n\n"
        "/start — Boshlash\n"
        "/me — O'z ma'lumotlaringiz"
    )


@dp.message(Command("me"))
async def me_handler(message: Message):
    user = message.from_user
    await message.answer(
        f"👤 Sizning ma'lumotlaringiz:\n\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"👤 Ism: {user.full_name}\n"
        f"🔗 Username: @{user.username or 'yoq'}",
        parse_mode="HTML"
    )


@dp.message(F.text)
async def echo_handler(message: Message):
    await message.answer(message.text)


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *args):
        pass


def run_server():
    port = int(os.getenv("PORT", 8080))
    HTTPServer(("0.0.0.0", port), HealthHandler).serve_forever()


async def main():
    await init_db()
    threading.Thread(target=run_server, daemon=True).start()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())