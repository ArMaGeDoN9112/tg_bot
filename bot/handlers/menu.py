from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

router = Router()

def get_menu_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Создать задачу"), KeyboardButton(text="Назначить задачу")],
            [KeyboardButton(text="Завершить задачу"), KeyboardButton(text="Удалить задачу")],
            [KeyboardButton(text="Мой профиль"), KeyboardButton(text="Помощь")],
            [KeyboardButton(text="Умный поиск (ИИ)"), KeyboardButton(text="Генерация идей (ИИ)")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    return keyboard

@router.message(F.text == "/menu")
async def menu_command(message: Message):
    await message.answer("Выберите действие:", reply_markup=get_menu_keyboard())

@router.message(F.text == "Мой профиль")
async def view_profile(message: Message):
    user_id = message.from_user.id

    with open("db/users_data.csv", "r") as users:
        for user in users:
            if str(user_id) in user:
                parts = user.strip().split(",")
                user_id_csv, name = parts[:2]
                subordinates_list = [i.replace("'", "").replace('"', "") for i in parts[2:]]

                if subordinates_list:
                    subordinates_str = "\n".join([f"  - {s.strip()}" for s in subordinates_list])
                else:
                    subordinates_str = "  Нет подчиненных"

                response = (
                    f"Ваш профиль:\n"
                    f"Имя: {name}\n"
                    f"Подчиненные:\n{subordinates_str}"
                )

                await message.answer(response)
                return

    await message.answer("Ваш профиль не найден. Зарегистрируйтесь через /start.")

@router.message(F.text == "Помощь")
async def help_command(message: Message):
    await message.answer("Список доступных команд:\n/menu — Открыть меню\n/start — Регистрация")