import os
import logging
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Инициализация бота
bot = Bot(
    token=os.getenv("TELEGRAM_BOT_TOKEN"),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# Словарь для хранения истории диалогов
user_context = {}


# Функция для разбивки длинных сообщений
def split_text(text: str, max_length: int = 4096) -> list[str]:
    """Разбивает текст на части по max_length символов"""
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]


# Обработчики команд
@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    user_context[user_id] = []  # Сбрасываем контекст
    await message.answer("🚀 Привет! Я AI-бот. Задай любой вопрос!")


@dp.message(Command("help"))
async def help_command(message: types.Message):
    help_text = (
        "📚 <b>Доступные команды:</b>\n"
        "/start - Начать диалог\n"
        "/help - Помощь\n\n"
        "Просто напиши вопрос, и я отвечу с помощью нейросети!"
    )
    await message.answer(help_text)


@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id

    # Пропускаем не-текстовые сообщения
    if not message.text:
        await message.answer("Пожалуйста, отправьте текстовое сообщение.")
        return

    # Логируем полученное сообщение
    logger.info(f"Получено сообщение от {user_id}: {message.text}")

    # Инициализируем историю для нового пользователя
    if user_id not in user_context:
        user_context[user_id] = []

    # Добавляем новое сообщение в историю
    user_context[user_id].append({"role": "user", "content": message.text})

    try:
        # Индикатор "печатает"
        await bot.send_chat_action(message.chat.id, "typing")

        # Параметры запроса к OpenRouter API
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "mistralai/mistral-7b-instruct",
            "messages": user_context[user_id],
            "max_tokens": 1024,
            "temperature": 0.7
        }

        # Отправляем запрос напрямую через aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"OpenRouter API error: {response.status} - {error_text}")
                    await message.answer("⚠️ Ошибка при обращении к нейросети. Попробуйте позже.")
                    return

                response_data = await response.json()
                answer = response_data['choices'][0]['message']['content']

        # Логируем ответ
        logger.info(f"Ответ от LLM: {answer[:100]}...")

        # Добавляем ответ в историю
        user_context[user_id].append({"role": "assistant", "content": answer})

        # Проверка на пустой ответ
        if not answer.strip():
            logger.warning("Получен пустой ответ от модели")
            await message.answer("🤔 Не получилось сгенерировать ответ. Попробуйте задать вопрос иначе.")
            return

        # Разбиваем ответ на части
        parts = split_text(answer)
        logger.info(f"Разбивка ответа на {len(parts)} частей")

        # Отправка частей с задержкой
        for i, part in enumerate(parts, 1):
            logger.info(f"Отправка части {i}/{len(parts)}: {part[:50]}...")
            await message.answer(part)
            await asyncio.sleep(0.5)  # Задержка

        logger.info("Ответ успешно отправлен")

    except Exception as e:
        logger.error(f"Ошибка: {e}", exc_info=True)
        await message.answer("⚠️ Произошла ошибка при обработке запроса. Попробуйте позже.")


# Запуск бота
async def main():
    logger.info("Starting bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())