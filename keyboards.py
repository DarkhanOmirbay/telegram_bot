from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Клавиатура для выбора сегмента пользователя
def get_segment_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨‍💼 Я Индивидуальный Предприниматель", callback_data="segment_ip")],
        [InlineKeyboardButton(text="⚖️ Я юрист", callback_data="segment_lawyer")],
        [InlineKeyboardButton(text="👥 Я HR-специалист", callback_data="segment_hr")],
        [InlineKeyboardButton(text="🔄 Другое", callback_data="segment_other")]
    ])

# Главное меню бота
def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❓ Как это работает?", callback_data="how_it_works")],
        [InlineKeyboardButton(text="💼 Примеры клиентов", callback_data="case_studies")],
        [InlineKeyboardButton(text="🤔 Ответы на вопросы", callback_data="faq")],
        [InlineKeyboardButton(text="📄 Получить шаблон договора", callback_data="get_template")],
        [InlineKeyboardButton(text="🎯 Заказать демонстрацию", callback_data="order_demo")],
        [InlineKeyboardButton(text="❌ Выйти",callback_data="exit")]
    ])

# Клавиатура для выбора кейсов
def get_case_studies_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎓 Образование", callback_data="case_education")],
        [InlineKeyboardButton(text="🏠 Недвижимость", callback_data="case_realestate")],
        [InlineKeyboardButton(text="💼 Услуги", callback_data="case_services")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu")]
    ])

# Клавиатура для FAQ
def get_faq_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚖️ Законно ли это?", callback_data="faq_legal")],
        [InlineKeyboardButton(text="🔐 Нужна ли ЭЦП?", callback_data="faq_ecp")],
        [InlineKeyboardButton(text="🛡 Безопасно ли?", callback_data="faq_security")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu")]
    ])

# Кнопка "Назад в меню"
def get_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_menu")]
    ])