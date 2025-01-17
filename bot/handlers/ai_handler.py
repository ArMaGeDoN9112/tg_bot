from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.config import settings
from bot.utils.ai import AIChatManager


router = Router()
ai_manager = AIChatManager(settings.GIGACHAT_KEY)

class AIChatStates(StatesGroup):
    initial_question = State()
    in_dialog = State()

def get_ai_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Завершить диалог с ИИ")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

    return keyboard

@router.message(F.text.in_({"Умный поиск (ИИ)", "Генерация идей (ИИ)"}))
async def start_dialog(message: Message, state: FSMContext):
    await state.update_data(mode=message.text)

    await state.set_state(AIChatStates.initial_question)
    await message.answer("Пожалуйста, введите ваш запрос для ИИ:", reply_markup=get_ai_keyboard())

@router.message(F.text == "Завершить диалог с ИИ")
async def end_dialog(message: Message, state: FSMContext):
    user_id = message.from_user.id

    ai_manager.end_dialog(user_id)

    await state.clear()
    await message.answer("Диалог завершен. Если нужно, начните новый с помощью /menu.", reply_markup=ReplyKeyboardRemove())

@router.message(AIChatStates.initial_question)
async def process_initial_question(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    mode = data.get("mode")

    if mode == "Умный поиск (ИИ)":
        ai_manager.start_new_dialog(user_id,
                                    "Ты являешься помощником, который специализируется на поиске, анализе и предоставлении "
                                    "информации пользователям. Твоя задача – интерпретировать запросы, формулировать ответы"
                                    "на основе полученной информации и помогать пользователю находить то, что ему нужно."
                                    " Необходимо проанализировать запрос пользователя, определить его цель, ключевые слова"
                                    " и контекст. Если запрос неполный или некорректный, уточни у пользователя недостающую"
                                    " информацию. Ответы должны быть понятными, лаконичными и строго по теме. Если запрос"
                                    " многосложный, давай развернутый ответ или структурируй его по пунктам. "
                                    "Если информация требует пояснений, добавь их. Отвечай честно, предоставляя только"
                                    " актуальную и проверенную информацию, избегай двусмысленных формулировок или"
                                    " неполных данных.")
    elif mode == "Генерация идей (ИИ)":
        ai_manager.start_new_dialog(user_id,
                                    "Ты являешься помощником в генерации идей для проектов. Твоя цель — предлагать "
                                    "уникальные, инновационные и релевантные идеи, которые можно адаптировать для "
                                    "различных сфер деятельности, таких как технологии, искусство, бизнес, "
                                    "образование и другие. Ты внимательно анализируешь ввод пользователя, чтобы "
                                    "понять тему, контекст и цель проекта, учитываешь ограничения и ресурсы, "
                                    "указанные пользователем, такие как бюджет, временные рамки, доступные "
                                    "технологии и целевая аудитория. Предлагай конкретные идеи для проектов, "
                                    "соответствующие запросу. Каждая идея должна быть оригинальной, полезной и "
                                    "иметь потенциал для реализации. Если пользователь просит, предлагай несколько "
                                    "вариантов идей с разными уровнями сложности или направленности. Генерируй идеи "
                                    "как для узких, так и для широких тем. От конкретной задачи до абстрактной "
                                    "концепции. Ты можешь адаптировать свои предложения под современные тренды, "
                                    "технологии и популярные темы.")
    else:
        await message.answer("Ошибка: режим не выбран.")
        return

    ai_response = ai_manager.get_ai_response(user_id, message.text)

    await message.answer(ai_response, reply_markup=get_ai_keyboard())
    await state.set_state(AIChatStates.in_dialog)

@router.message(AIChatStates.in_dialog)
async def handle_dialog_message(message: Message, state: FSMContext):
    user_id = message.from_user.id
    ai_response = ai_manager.get_ai_response(user_id, message.text)

    await message.answer(ai_response, reply_markup=get_ai_keyboard())

