from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()

class FeedbackForm(StatesGroup):
    satisfaction = State()
    suggestions = State()

def get_rating_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1", callback_data="rating_1"),
                InlineKeyboardButton(text="2", callback_data="rating_2"),
                InlineKeyboardButton(text="3", callback_data="rating_3"),
                InlineKeyboardButton(text="4", callback_data="rating_4"),
                InlineKeyboardButton(text="5", callback_data="rating_5"),
            ]
        ]
    )

    return keyboard

@router.message(F.text == "/feedback")
async def start_feedback(message: Message, state: FSMContext):

    await state.set_state(FeedbackForm.satisfaction)
    await message.answer("Оцените работу бота по шкале от 1 до 5:", reply_markup=get_rating_keyboard())

@router.callback_query(F.data.startswith("rating_"))
async def process_rating(callback: CallbackQuery, state: FSMContext):
    rating = callback.data.split("_")[1]

    await state.update_data(satisfaction=rating)
    await state.set_state(FeedbackForm.suggestions)

    await callback.message.answer("Есть ли у вас предложения по улучшению? Напишите их ниже:")
    await callback.answer()

@router.message(FeedbackForm.satisfaction)
async def process_satisfaction(message: Message, state: FSMContext):
    rating = message.text

    if rating not in ["1", "2", "3", "4", "5"]:
        await message.answer("Введите число от 1 до 5.")
        return

    await state.update_data(satisfaction=rating)
    await state.set_state(FeedbackForm.suggestions)
    await message.answer("Есть ли у вас предложения по улучшению? Напишите их ниже:")

@router.message(FeedbackForm.suggestions)
async def process_suggestions(message: Message, state: FSMContext):
    suggestions = message.text
    user_data = await state.get_data()

    with open("db/feedback.csv", "a") as file:
        file.write(f"{message.from_user.id},{user_data['satisfaction']},{suggestions}\n")

    await state.clear()
    await message.answer("Спасибо за ваш отзыв!")