from aiogram import BaseMiddleware
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
import os


class AuthMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        user_id = event.from_user.id

        if not os.path.exists("db/users_data.csv"):
            with open("db/users_data.csv", "w") as file:
                file.write("user_id,name,skills\n")

        with open("db/users_data.csv", "r") as file:
            user_data = file.read()

        state: FSMContext = data.get("state")
        if state:
            current_state = await state.get_state()
        else:
            current_state = None

        if str(user_id) not in user_data:
            if event.text == "/start" or current_state in ["Registration:name", "Registration:subordinates"]:
                return await handler(event, data)
            else:
                await event.answer("Вы ещё не зарегистрированы. Используйте команду /start для регистрации.")
                return

        return await handler(event, data)