from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from apscheduler.schedulers.asyncio import AsyncIOScheduler
import csv
from datetime import datetime, timedelta

from bot.utils.scheduler import send_reminder, send_deadline_notification

router = Router()

class TaskCreation(StatesGroup):
    description = State()
    due_date = State()

@router.message(F.text == "Создать задачу")
async def create_task(message: Message, state: FSMContext):
    await state.set_state(TaskCreation.description)
    await message.answer("Введите описание задачи:")

@router.message(TaskCreation.description)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(TaskCreation.due_date)
    await message.answer("Введите срок выполнения задачи (в формате ГГГГ-ММ-ДД ЧЧ:ММ:СС):")

@router.message(TaskCreation.due_date)
async def process_due_date(message: Message, state: FSMContext, scheduler: AsyncIOScheduler):
    due_date = message.text

    try:
        due_date_obj = datetime.strptime(due_date, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        await message.answer("Неверный формат даты. Введите дату в формате ГГГГ-ММ-ДД ЧЧ:ММ:СС.")
        return

    data = await state.get_data()
    description = data["description"]

    with open("db/tasks.csv", "a", newline="") as file:
        writer = csv.writer(file)
        task_id = sum(1 for _ in open("db/tasks.csv"))
        writer.writerow([task_id, description, "", "В процессе", due_date, str(message.from_user.id)])

    reminder_time = due_date_obj - timedelta(hours=1)

    if reminder_time > datetime.now():
        scheduler.add_job(
            send_reminder,
            "date",
            run_date=reminder_time,
            args=[message.bot, message.from_user.id, description],
        )

    if due_date_obj > datetime.now():
        scheduler.add_job(
            send_deadline_notification,
            "date",
            run_date=due_date_obj,
            args=[message.bot, message.from_user.id, description],
            id=f"deadline_{task_id}",
        )

    await state.clear()
    await message.answer(f"Задача создана! ID задачи: {task_id}")

@router.message(F.text == "Удалить задачу")
async def delete_task_prompt(message: Message):
    user_id = str(message.from_user.id)

    with open("db/tasks.csv", "r") as file:
        reader = csv.reader(file)
        tasks = list(reader)

    user_tasks = [task for task in tasks if task[5] == user_id]

    if not user_tasks:
        await message.answer("У вас пока нет задач.")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=task[1], callback_data=f"delete_{task[0]}")] for task in user_tasks
    ])

    await message.answer("Выберите задачу для удаления:", reply_markup=keyboard)

@router.callback_query(F.data.startswith("delete_"))
async def delete_task(callback: CallbackQuery):
    task_id = int(callback.data.split("_")[1])

    tasks = []
    with open("db/tasks.csv", "r") as file:
        reader = csv.reader(file)
        tasks = list(reader)

    if task_id < 0 or task_id >= len(tasks):
        await callback.answer("Неверный номер задачи.")
        return

    deleted_task = tasks.pop(task_id)

    for i, task in enumerate(tasks):
        task[0] = str(i)

    with open("db/tasks.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(tasks)

    await callback.message.answer(f'Задача "{deleted_task[1]}" удалена.')
    await callback.answer()

@router.message(F.text == "Назначить задачу")
async def assign_task_prompt(message: Message):
    user_id = str(message.from_user.id)

    with open("db/tasks.csv", "r") as file:
        reader = csv.reader(file)
        tasks = list(reader)

    user_tasks = [task for task in tasks if task[5] == user_id]

    if not user_tasks:
        await message.answer("У вас пока нет задач.")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=task[1], callback_data=f"task_{task[0]}")]
        for task in user_tasks
    ])

    await message.answer("Выберите задачу:", reply_markup=keyboard)

@router.callback_query(F.data.startswith("task_"))
async def choose_task(callback: CallbackQuery):
    task_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    with open("db/users_data.csv", "r") as file:
        reader = csv.reader(file)
        users = list(reader)

    current_user = None
    for user in users:
        if str(user_id) == user[0]:
            current_user = user
            break

    if not current_user:
        await callback.answer("Вы не зарегистрированы. Используйте /start для регистрации.")
        return

    subordinates = current_user[2].strip('"').split(",") if len(current_user) > 2 else []
    if not subordinates:
        await callback.answer("У вас нет подчиненных.")
        return

    tasks = []
    with open("db/tasks.csv", "r") as file:
        reader = csv.reader(file)
        tasks = list(reader)

    if task_id < 0 or task_id >= len(tasks):
        await callback.answer("Неверный номер задачи.")
        return

    assigned_to = tasks[task_id][2].strip()
    assigned_to_list = assigned_to.split(",") if assigned_to else []

    available_subordinates = [s.strip() for s in subordinates if s.strip() not in assigned_to_list]

    if not available_subordinates:
        await callback.answer("Все подчиненные уже назначены на эту задачу.")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=s, callback_data=f"subordinate_{task_id}_{s}")] for s in available_subordinates
    ]
    +
    [[InlineKeyboardButton(text="Всё", callback_data=f"done_{task_id}")]])

    await callback.message.edit_text("Выберите подчиненного:", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("subordinate_"))
async def choose_subordinate(callback: CallbackQuery):
    task_id = int(callback.data.split("_")[1])
    subordinate_name = callback.data.split("_", 2)[2]

    tasks = []
    with open("db/tasks.csv", "r") as file:
        reader = csv.reader(file)
        tasks = list(reader)

    if task_id < 0 or task_id >= len(tasks):
        await callback.answer("Неверный номер задачи.")
        return

    assigned_to = tasks[task_id][2].strip()
    assigned_to_list = assigned_to.split(",") if assigned_to else []

    if subordinate_name not in assigned_to_list:
        assigned_to_list.append(subordinate_name)
        tasks[task_id][2] = ",".join(assigned_to_list)

        with open("db/tasks.csv", "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerows(tasks)

        await callback.answer(f"Подчиненный {subordinate_name} добавлен к задаче {task_id}.")
    else:
        await callback.answer(f"Подчиненный {subordinate_name} уже назначен на задачу {task_id}.")

    await choose_task(callback)

@router.callback_query(F.data.startswith("done_"))
async def done_assigning(callback: CallbackQuery):
    task_id = int(callback.data.split("_")[1])

    tasks = []
    with open("db/tasks.csv", "r") as file:
        reader = csv.reader(file)
        tasks = list(reader)

    if task_id < 0 or task_id >= len(tasks):
        await callback.answer("Неверный номер задачи.")
        return

    assigned_to = tasks[task_id][2].strip()
    assigned_to_list = assigned_to.split(",") if assigned_to else []

    if not assigned_to_list:
        await callback.message.answer("На задачу не назначено ни одного подчиненного.")
    else:
        await callback.message.answer(f"Назначение подчиненных на задачу завершено.\n"
                                     f"Назначенные подчиненные: {', '.join(assigned_to_list)}")

    await callback.answer()

@router.message(F.text == "/view_tasks")
async def view_tasks(message: Message):
    user_id = str(message.from_user.id)

    with open("db/tasks.csv", "r") as file:
        reader = csv.reader(file)
        tasks = list(reader)

    if not tasks:
        await message.answer("Задач пока нет.")
        return

    user_tasks = [task for task in tasks if task[5] == user_id]

    if not user_tasks:
        await message.answer("У вас пока нет задач.")
        return

    response = "Список ваших задач:\n"
    for task in user_tasks:
        task_id, description, assigned_to, status, due_date, _ = task
        response += (
            f"ID: {task_id}\n"
            f"Описание: {description}\n"
            f"Назначена: {assigned_to if assigned_to else 'Никому'}\n"
            f"Статус: {status}\n"
            f"Срок: {due_date}\n\n"
        )

    await message.answer(response)

@router.message(F.text == "Завершить задачу")
async def complete_task_prompt(message: Message):
    user_id = str(message.from_user.id)

    with open("db/tasks.csv", "r") as file:
        reader = csv.reader(file)
        tasks = list(reader)

    user_tasks = [task for task in tasks if task[5] == user_id]

    if not user_tasks:
        await message.answer("У вас пока нет задач.")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=task[1], callback_data=f"complete_{task[0]}")] for task in user_tasks
    ])

    await message.answer("Выберите задачу для завершения:", reply_markup=keyboard)

@router.callback_query(F.data.startswith("complete_"))
async def complete_task(callback: CallbackQuery):
    task_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    tasks = []
    with open("db/tasks.csv", "r") as file:
        reader = csv.reader(file)
        tasks = list(reader)

    if task_id < 0 or task_id >= len(tasks):
        await callback.answer("Неверный номер задачи.")
        return

    if tasks[task_id][5] != str(user_id):
        await callback.answer("Вы не можете завершить чужую задачу.")
        return

    tasks[task_id][3] = "Выполнено"

    with open("db/tasks.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(tasks)

    await callback.message.answer(f'Задача "{tasks[task_id][1]}" отмечена как выполненная.')
    await callback.answer()