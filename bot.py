import os
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv

load_dotenv()

# Проверка переменных окружения при запуске
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("API_KEY")


bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Привет! Я AI-бот. Задай любой вопрос!")

@dp.message(Command("help"))
async def help_command(message: types.Message):
    await message.answer("Просто напиши вопрос, и я отвечу с помощью нейросети!")

@dp.message()
async def handle_message(message: types.Message):
    if not message.text:
        await message.answer("Пожалуйста, отправьте текстовое сообщение.")
        return
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/your-repo",
            "X-Title": "Telegram AI Bot"
        }
        payload = {
            "model": "mistralai/mistral-7b-instruct:free",
            "messages": [{"role": "user", "content": message.text}],
            "max_tokens": 1024
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    await message.answer("Ошибка при обращении к нейросети. Проверьте настройки API.")
                    return
                response_data = await response.json()
                answer = response_data['choices'][0]['message']['content']

                await message.answer(answer)

    except Exception:
        await message.answer("Произошла ошибка при обработке запроса.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
