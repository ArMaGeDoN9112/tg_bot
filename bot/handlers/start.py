from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


router = Router()

class Registration(StatesGroup):
    name = State()
    subordinates = State()

@router.message(F.text == "/start")
async def start_command(message: Message, state: FSMContext):
    user_id = message.from_user.id

    with open("db/users_data.csv", "r") as file:
        users = file.readlines()

    user_found = False
    for i, user in enumerate(users):
        if str(user_id) == user.split(",")[0]:
            user_found = True
            break

    if user_found:
        await state.set_state(Registration.name)
        await message.answer("Вы уже зарегистрированы. Пожалуйста, введите ваше имя для обновления данных:")
    else:
        await state.set_state(Registration.name)
        await message.answer("Добро пожаловать! Пожалуйста, введите ваше имя:")

@router.message(Registration.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Registration.subordinates)
    await message.answer("Теперь введите ФИО ваших подчиненных (через запятую):")

@router.message(Registration.subordinates)
async def process_subordinates(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_data = await state.get_data()
    name = user_data["name"]
    subordinates = message.text

    with open("db/users_data.csv", "r") as file:
        users = file.readlines()

    user_found = False
    updated_users = []
    for user in users:
        if str(user_id) == user.split(",")[0]:
            updated_users.append(f'{user_id},{name},"{subordinates}"\n')
            user_found = True
        else:
            updated_users.append(user)

    if not user_found:
        updated_users.append(f'{user_id},{name},"{subordinates}"\n')

    with open("db/users_data.csv", "w") as file:
        file.writelines(updated_users)

    await state.clear()
    await message.answer("Спасибо! Ваши данные обновлены. Чтобы полностью воспользоваться функционалом бота, используйте команду /menu.")