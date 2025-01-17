from aiogram import BaseMiddleware
from aiogram.types import Message
import datetime


class LoggerMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        user_id = event.from_user.id
        username = event.from_user.username or "Unknown"
        action = event.text
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open("db/logs.csv", "a") as log_file:
            log_file.write(f'{timestamp},{user_id},{username},"{action}"\n')

        return await handler(event, data)