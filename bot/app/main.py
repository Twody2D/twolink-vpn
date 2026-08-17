import asyncio
import logging

from aiogram import Bot, Dispatcher

from app.core.config import settings
from app.handlers import start, subscribe


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=settings.bot_token)
    dispatcher = Dispatcher()
    dispatcher.include_router(start.router)
    dispatcher.include_router(subscribe.router)

    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
