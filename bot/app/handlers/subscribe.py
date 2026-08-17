import logging

import httpx
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.core.config import settings
from app.services.backend_client import backend_client

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("buy"))
async def buy(message: Message) -> None:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Оплатить (заглушка)", callback_data="pay_stub")]]
    )
    await message.answer(
        "Оплата пока не подключена — это заглушка, эмулирующая успешную оплату для тестирования.",
        reply_markup=keyboard,
    )


@router.callback_query(F.data == "pay_stub")
async def pay_stub(callback: CallbackQuery) -> None:
    try:
        subscription = await backend_client.create_subscription(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
        )
    except httpx.HTTPError:
        logger.exception("failed to create subscription for telegram_id=%s", callback.from_user.id)
        await callback.message.answer("Не получилось выдать доступ, попробуй позже.")
        await callback.answer()
        return

    link = f"{settings.public_base_url}/sub/{subscription['token']}"
    await callback.message.answer(f"Готово! Твоя ссылка подписки:\n{link}")
    await callback.answer()
