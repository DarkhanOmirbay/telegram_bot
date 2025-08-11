import asyncio
import logging
from typing import Dict, Any
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter,CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import re

from config import BOT_TOKEN,ADMIN_IDS
from texts import (WELCOME_TEXT, HELP_TEXT,SEGMENT_MESSAGES, CASE_STUDIES, 
                   FAQ_ANSWERS,HOW_IT_WORKS_TEXT,CASE_STUDIES_HANDLER_TEXT,FAQ_HANDLER_TEXT,
                   GET_TEMPLATE_TEXT,ORDER_DEMO_TEXT,ACTION_TEMPLATE_TEXT,ACTION_DEMO_TEXT,EXIT_TEXT)
from keyboards import (
    get_segment_keyboard, get_main_menu_keyboard, get_case_studies_keyboard,
    get_faq_keyboard, get_back_keyboard
)
from google_sheets import init_google_sheets, save_lead_to_sheets, get_leads_statistics


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UserStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()


bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()

# db :) нужно поменять на psql
user_data: Dict[int, Dict[str, Any]] = {}


@router.message(CommandStart())
async def start_handler(message: Message):
    user_id = message.from_user.id
    user_data[user_id] = {
        'user_id': user_id,
        'username': message.from_user.username,
        'first_name': message.from_user.first_name,
        'started_at': message.date.isoformat()
    }
    
    await message.answer(
        WELCOME_TEXT,
        reply_markup=get_segment_keyboard(),
        parse_mode='HTML'
    )

@router.message(Command("help"))
async def help_handler(message: Message):
    """ команда /help """
    await message.answer(HELP_TEXT, parse_mode='HTML')
    

@router.message(Command("stats"))
async def stats_handler(message: Message):
    """Показать статистику лидов, только для админов"""
    admin_ids = ADMIN_IDS
    
    if message.from_user.id not in admin_ids:
        await message.answer("❌ У вас нет доступа к статистике.")
        return
    
    try:
        # Dict[str,dict[str,int]]
        stats = await get_leads_statistics()
        if stats:
            text = f"""📊 <b>Статистика лидов SignContract</b>

📈 <b>Общее количество лидов:</b> {stats['total_leads']}

👥 <b>По сегментам:</b>
"""
            for segment, count in stats['by_segment'].items():
                # dict[str,emoji:)]
                # for each segment we get emoji
                emoji = {'ip': '👨‍💼', 'lawyer': '⚖️', 'hr': '👥', 'other': '🔄'}.get(segment, '❓')
                
                segment_name = {'ip': 'Индивидуальный Предприниматель', 'lawyer': 'Юристы', 'hr': 'HR', 'other': 'Другие'}.get(segment, segment)

                text += f"{emoji} {segment_name}: {count}\n"
            
            text += f"\n🎯 <b>По действиям:</b>\n"
            for action, count in stats['by_action'].items():
                emoji = {'template': '📄', 'demo': '🎯'}.get(action, '❓')
                action_name = {'template': 'Шаблоны', 'demo': 'Демо'}.get(action, action)
                text += f"{emoji} {action_name}: {count}\n"
            
            await message.answer(text, parse_mode='HTML')
        else:
            await message.answer("❌ Не удалось получить статистику.")
            
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        await message.answer("❌ Ошибка при получении статистики.")

@router.message(Command("menu"))
async def menu_handler(message: Message):
    """ команда /menu """
    user_id = message.from_user.id
    segment = user_data.get(user_id, {}).get('segment', 'other')
    
    await message.answer(
        SEGMENT_MESSAGES[segment],
        reply_markup=get_main_menu_keyboard(),
        parse_mode='HTML'
    )

@router.callback_query(F.data.startswith("segment_"))
async def segment_handler(callback: CallbackQuery):
    segment = callback.data.split("_")[1]
    user_id = callback.from_user.id
    
    if user_id in user_data:
        user_data[user_id]['segment'] = segment
    
    await callback.message.edit_text(
        SEGMENT_MESSAGES[segment],
        reply_markup=get_main_menu_keyboard(),
        parse_mode='HTML'
    )
    await callback.answer()

@router.callback_query(F.data == "how_it_works")
async def how_it_works_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        HOW_IT_WORKS_TEXT,
        reply_markup=get_back_keyboard(),
        parse_mode='HTML'
    )
    await callback.answer()

@router.callback_query(F.data == "case_studies")
async def case_studies_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        CASE_STUDIES_HANDLER_TEXT,
        reply_markup=get_case_studies_keyboard(),
        parse_mode='HTML'
    )
    await callback.answer()

@router.callback_query(F.data.startswith("case_"))
async def case_detail_handler(callback: CallbackQuery):
    case_type = callback.data.split("_")[1]
    
    await callback.message.edit_text(
        CASE_STUDIES[case_type],
        reply_markup=get_back_keyboard(),
        parse_mode='HTML'
    )
    await callback.answer()

@router.callback_query(F.data == "faq")
async def faq_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        FAQ_HANDLER_TEXT,
        reply_markup=get_faq_keyboard(),
        parse_mode='HTML'
    )
    await callback.answer()

@router.callback_query(F.data.startswith("faq_"))
async def faq_detail_handler(callback: CallbackQuery):
    faq_type = callback.data.split("_")[1]
    
    await callback.message.edit_text(
        FAQ_ANSWERS[faq_type],
        reply_markup=get_back_keyboard(),
        parse_mode='HTML'
    )
    await callback.answer()

@router.callback_query(F.data == "get_template")
async def get_template_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.waiting_for_name)
    await state.update_data(action="template")
    await callback.message.edit_text(GET_TEMPLATE_TEXT, reply_markup=get_back_keyboard(),parse_mode='HTML')
    # testing
    logger.info(f"get back from get template ,checking user_data {user_data}")
    await callback.answer()

@router.callback_query(F.data == "order_demo")
async def order_demo_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.waiting_for_name)
    await state.update_data(action="demo")
    await callback.message.edit_text(ORDER_DEMO_TEXT,reply_markup=get_back_keyboard(), parse_mode='HTML')
    # testing
    logger.info(f"get back from order demo,checking user_data {user_data}")
    
    await callback.answer()

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    segment = user_data.get(user_id, {}).get('segment', 'other')
    
    await callback.message.edit_text(
        SEGMENT_MESSAGES[segment],
        reply_markup=get_main_menu_keyboard(),
        parse_mode='HTML'
    )
    await callback.answer()


@router.message(StateFilter(UserStates.waiting_for_name))
async def process_name(message: Message, state: FSMContext):
    user_data_state = await state.get_data()
    action = user_data_state.get('action')
    
    name = message.text.strip()
    if not re.match(r"^[A-Za-zA-Яа-яЁё]{2,}$",name):
        await message.answer("❌ Пожалуйста, введите корректное имя (только буквы, не менее 2 символов).")
        return
    
    user_id = message.from_user.id
    if user_id in user_data:
        user_data[user_id]['name'] = name
    
    await state.update_data(name=message.text)
    await state.set_state(UserStates.waiting_for_phone)
    
    action_text = "получения шаблона" if action == "template" else "заказа демонстрации"
    
    
    await message.answer(
        f"👍 Приятно познакомиться, {message.text}!\n\n"
        f"<b>Теперь введите ваш номер телефона для {action_text}:</b>\n\n"
        f"Например: +7 999 123-45-67",reply_markup=get_back_keyboard(),
        parse_mode="HTML"
    )
    


@router.message(StateFilter(UserStates.waiting_for_phone))
async def process_phone(message: Message, state: FSMContext):
    user_data_state = await state.get_data()
    action = user_data_state.get('action')
    name = user_data_state.get('name')
    
    phone = message.text.strip()
    if not re.match(r"^\+7\d{10}$",phone.replace(" ","").replace("-","")):
        await message.answer("❌ Введите корректный номер телефона в формате +7XXXXXXXXXX.")
        return
    
    user_id = message.from_user.id
    if user_id in user_data:
        user_data[user_id]['phone'] = phone
        user_data[user_id]['name'] = name
    
    user_data[user_id] = {
        'user_id': user_id,
        'username': message.from_user.username,
        'first_name': message.from_user.first_name,
    }
   
   
    try:
        success = await save_lead_to_sheets(user_data.get(user_id, {}), name, message.text, action)
        if success:
            logger.info(f"Lead saved to Google Sheets: {name}, {message.text}, {action}")
            logger.info(f"before deleting user_data: {user_data}" )
            if user_id in user_data:
                del user_data[user_id]
            logger.info(f"after deleting user data {user_data}")
        else:
            logger.warning("Failed to save lead to Google Sheets")
    except Exception as e:
        logger.error(f"Error saving to Google Sheets: {e}")
    
    
    logger.info(f"New lead: {name}, {message.text}, {action}")
    
    if action == "template":
        text = ACTION_TEMPLATE_TEXT
    else:
        text = ACTION_DEMO_TEXT
    
    await message.answer(
        text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode='HTML'
    )
    await state.clear()

# ЗДЕСЬ МОЖНО ДОБАВИТЬ ЛОГИКУ ИИ ЛЛМ И ТД.
@router.message()
async def unknown_message_handler(message: Message):
    await message.answer(
        "🤔 Не совсем понял вас. Воспользуйтесь меню ниже или напишите /start для начала.",
        reply_markup=get_main_menu_keyboard()
    )

@router.callback_query(F.data=="exit")
async def exit(callback:CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id in user_data:
        del user_data[user_id]
    
    await callback.message.answer(
        text = EXIT_TEXT,
        parse_mode='HTML'
    )
async def main():
    await init_google_sheets()
    
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    
    logger.info("Bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped")