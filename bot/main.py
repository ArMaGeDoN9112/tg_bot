import asyncio

from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, Message

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.config import settings
from bot.handlers import start
from bot.middleware.logger import LoggerMiddleware
from bot.middleware.auth_check import AuthMiddleware

from handlers.feedback import router as fsm_router
from handlers.menu import router as menu_router
from handlers.tasks import router as tasks_router
from handlers.ai_handler import router as ai_router
from bot.utils.scheduler import setup_scheduler


bot = Bot(token=settings.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
scheduler = AsyncIOScheduler()

dp.message.middleware(AuthMiddleware())
dp.message.middleware(LoggerMiddleware())

router = Router()

dp.include_routers(start.router, menu_router, fsm_router, tasks_router, ai_router, router)

@router.message()
async def handle_unknown_message(message: Message):
    await message.answer(
        "Я не понимаю вашего сообщения. Пожалуйста, используйте команды из меню или введите /menu для выбора действия."
    )

async def on_startup():
    await bot.set_my_commands([
        BotCommand(command="start", description="Начало работы"),
        BotCommand(command="menu", description="Открыть меню"),
        BotCommand(command="view_tasks", description="Просмотр задач"),
        BotCommand(command="feedback", description="Оставить отзыв"),
    ])

    setup_scheduler(scheduler, bot)
    scheduler.start()


async def main():
    await on_startup()
    await dp.start_polling(bot, scheduler=scheduler)

if __name__ == "__main__":
    asyncio.run(main())