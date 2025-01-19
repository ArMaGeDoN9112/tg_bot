from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from datetime import datetime, timedelta
import csv
import random

MOTIVATIONAL_PHRASES = [
    "Делай хорошо, плохо не делай",
    "Думай на два шага вперед, но делай на шаг лучше",
    "Трудности решай, отговорки не придумывай",
    "Сначала сделай правильно, потом красиво",
    "Не знаешь, как сделать – спроси, а не угадай",
    "Если начал – доделай, если не уверен – уточни",
    "Мелочи решают многое",
    "Учись на ошибках, но избегай их повторения",
    "Не оставляй на завтра то, что можно сделать сегодня",
    "Улыбнись!",
    "Решение есть всегда – важно его найти",
    "Сделай лучше, чем вчера, и меньше, чем завтра",
    "Не усложняй, но и не упрощай лишнего",
    "Слушай других, но думай своей головой",
    "Каждый шаг – это прогресс, двигайся вперёд",
    ]

async def send_reminder(bot: Bot, chat_id: str, task_description: str):
    await bot.send_message(chat_id=chat_id, text=f"Напоминание: задача '{task_description}' скоро истекает (остался 1 час).")

async def send_deadline_notification(bot: Bot, chat_id: int, task_description: str):
    await bot.send_message(chat_id=chat_id, text=f"Срок выполнения задачи '{task_description}' истёк.")

async def send_daily_motivation(bot: Bot):
    with open("db/users_data.csv", "r") as file:
        reader = csv.reader(file)
        users = list(reader)

    for user in users[1:]:
        user_id = user[0]
        random_phrase = random.choice(MOTIVATIONAL_PHRASES)
        await bot.send_message(chat_id=user_id, text=random_phrase)

def setup_scheduler(scheduler: AsyncIOScheduler, bot: Bot):
    with open("db/tasks.csv", "r") as file:
        reader = csv.reader(file)
        tasks = list(reader)

    for task in tasks:
        task_id, description, assigned_to, status, due_date_str, user_id = task
        due_date = datetime.strptime(due_date_str, "%m-%d %H:%M")

        reminder_time = due_date - timedelta(hours=1)

        if reminder_time > datetime.now():
            scheduler.add_job(
                send_reminder,
                "date",
                run_date=reminder_time,
                args=[bot, user_id, description],
            )

    scheduler.add_job(
        send_daily_motivation,
        "cron",
        hour=9,
        minute=0,
        args=[bot],
    )

    print(scheduler.print_jobs())