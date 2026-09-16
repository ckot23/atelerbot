import asyncio
import logging
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup,
    KeyboardButton, ReplyKeyboardRemove
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters, ContextTypes
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# =================== CONFIG ===================
TOKEN     = '8943280869:AAHFxKGh5R-jYh0OJot5xOoPp_nbt7E04pk'
ADMIN_ID  = 7114829971
SITE_URL  = 'https://ckot-23.github.io'   # замени на свой URL сайта
# ==============================================

# States
CHOOSE_TYPE, ENTER_TASK, ENTER_CONTACT, CONFIRM = range(4)

# Храним сообщения admin->client для ответов
# {admin_msg_id: client_chat_id}
reply_map: dict[int, int] = {}

SERVICES = {
    'channel': {
        'name': '📢 Бот для канала',
        'price': 'от 15 000 ₽',
        'time': '5–7 дней',
        'desc': 'Кнопки под постами, заявка и уведомление вам в Telegram.',
        'features': [
            'Сбор заявки и контакта из канала',
            'Уведомление о заявке в Telegram',
            'Тестирование и передача проекта',
        ]
    },
    'support': {
        'name': '🎧 Бот поддержки',
        'price': 'от 20 000 ₽',
        'time': '7–10 дней',
        'desc': 'Первая линия по FAQ. Сложные обращения уходят человеку.',
        'features': [
            'Статус заказа и возврат',
            'Онлайн-школа',
            'Тарифы и передача мастеру',
        ]
    },
    'booking': {
        'name': '📅 Бот записи',
        'price': 'от 20 000 ₽',
        'time': '7–10 дней',
        'desc': 'Клиент видит слоты, записывается сам и получает напоминание.',
        'features': [
            'Салон и барбершоп',
            'Стоматология или массаж',
            'Автосервис на час',
        ]
    },
    'shop': {
        'name': '🛍 Бот-магазин',
        'price': 'от 30 000 ₽',
        'time': '10–14 дней',
        'desc': 'Каталог, корзина и оплата ЮKassa/СБП в Telegram.',
        'features': [
            'Магазин одежды или мерча',
            'Доставка еды',
            'Цифровые товары после оплаты',
        ]
    },
}


def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('💻 Услуги и цены', callback_data='services')],
        [InlineKeyboardButton('✏️ Оставить заявку', callback_data='order')],
        [InlineKeyboardButton('❓ FAQ', callback_data='faq'),
         InlineKeyboardButton('🌐 Сайт', url=SITE_URL)],
        [InlineKeyboardButton('📨 Написать напрямую', url='https://t.me/ckot_23')],
    ])


def services_keyboard():
    buttons = []
    for key, s in SERVICES.items():
        buttons.append([InlineKeyboardButton(f"{s['name']} — {s['price']}", callback_data=f'svc_{key}')])
    buttons.append([InlineKeyboardButton('← Назад', callback_data='back_main')])
    return InlineKeyboardMarkup(buttons)


def order_type_keyboard():
    buttons = []
    for key, s in SERVICES.items():
        buttons.append([InlineKeyboardButton(s['name'], callback_data=f'type_{key}')])
    buttons.append([InlineKeyboardButton('❌ Отмена', callback_data='cancel')])
    return InlineKeyboardMarkup(buttons)


# =================== HANDLERS ===================

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    text = (
        f"Привет, {name}! У вас ATELIER — разработка Telegram-ботов под ключ ✨\n\n"
        "👉 Боты для заявок, продаж, записи и поддержки\n"
        "👉 Оценка до начала работ\n"
        "👉 Фиксируем объём и смету\n"
        "👉 14 дней правок после запуска"
    )
    await update.message.reply_text(text, reply_markup=main_keyboard())


async def button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    if data == 'services':
        await q.edit_message_text(
            "💼 *Наши услуги*\n\nВыберите тип бота, чтобы узнать подробнее:",
            parse_mode='Markdown',
            reply_markup=services_keyboard()
        )

    elif data.startswith('svc_'):
        key = data[4:]
        s = SERVICES[key]
        features = '\n'.join(f'  \u2022 {f}' for f in s['features'])
        text = (
            f"*{s['name']}*\n\n"
            f"💰 *Цена:* {s['price']}\n"
            f"⏱ *Срок:* {s['time']}\n\n"
            f"{s['desc']}\n\n"
            f"*Что входит:*\n{features}"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton('✏️ Заказать этот бот', callback_data=f'type_{key}')],
            [InlineKeyboardButton('← К услугам', callback_data='services')],
        ])
        await q.edit_message_text(text, parse_mode='Markdown', reply_markup=keyboard)

    elif data == 'faq':
        text = (
            "❓ *Частые вопросы*\n\n"
            "💰 *Сколько стоит?*\nКанал от 15 000 ₽, поддержка и запись от 20 000 ₽, магазин от 30 000 ₽\n\n"
            "⏱ *Сроки?*\nКанал 5–7 дней, поддержка и запись 7–10, магазин 10–14\n\n"
            "💳 *Оплата?*\n50/50: половина до старта, половина перед передачей кода\n\n"
            "📦 *После запуска?*\nКод ваш. 14 дней правок входят в стоимость"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton('✏️ Оставить заявку', callback_data='order')],
            [InlineKeyboardButton('← Назад', callback_data='back_main')],
        ])
        await q.edit_message_text(text, parse_mode='Markdown', reply_markup=keyboard)

    elif data == 'back_main':
        await q.edit_message_text(
            '🏠 *Главное меню*',
            parse_mode='Markdown',
            reply_markup=main_keyboard()
        )

    elif data == 'order' or data.startswith('type_'):
        # Если уже выбран тип через svc_ воронку
        if data.startswith('type_'):
            key = data[5:]
            ctx.user_data['bot_type'] = SERVICES[key]['name']
            await q.edit_message_text(
                f"Выбрано: *{SERVICES[key]['name']}*\n\n"
                "💬 Опишите коротко, что должен делать бот — сфера, аудитория, цель:",
                parse_mode='Markdown'
            )
            return ENTER_TASK
        else:
            await q.edit_message_text(
                "📝 *Новая заявка*\n\nШаг 1/3 — выберите тип бота:",
                parse_mode='Markdown',
                reply_markup=order_type_keyboard()
            )
            return CHOOSE_TYPE

    elif data == 'cancel':
        await q.edit_message_text(
            '❌ Заявка отменена.',
            reply_markup=main_keyboard()
        )
        ctx.user_data.clear()
        return ConversationHandler.END


async def choose_type(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    key = q.data[5:]  # type_xxx
    ctx.user_data['bot_type'] = SERVICES[key]['name']
    await q.edit_message_text(
        f"Тип: *{SERVICES[key]['name']}*\n\n"
        "💬 Шаг 2/3 — опишите задачу:\n"
        "Коротко: сфера, что должен делать бот, аудитория:",
        parse_mode='Markdown'
    )
    return ENTER_TASK


async def enter_task(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['task'] = update.message.text
    await update.message.reply_text(
        "📱 Шаг 3/3 — ваш Telegram для связи:\n"
        "(например: @username)"
    )
    return ENTER_CONTACT


async def enter_contact(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['contact'] = update.message.text
    d = ctx.user_data
    text = (
        "✅ *Проверьте заявку:*\n\n"
        f"📌 Тип: {d['bot_type']}\n"
        f"💬 Задача: {d['task']}\n"
        f"📱 Telegram: {d['contact']}"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton('✅ Отправить', callback_data='confirm'),
         InlineKeyboardButton('❌ Отмена', callback_data='cancel')]
    ])
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=keyboard)
    return CONFIRM


async def confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    d = ctx.user_data
    user = update.effective_user

    # Сообщение админу
    admin_text = (
        "🔔 *Новая заявка через бота*\n\n"
        f"📌 *Тип:* {d['bot_type']}\n"
        f"💬 *Задача:* {d['task']}\n"
        f"📱 *Контакт:* {d['contact']}\n\n"
        f"👤 *Telegram ID:* `{user.id}`\n"
        f"👤 *Username:* @{user.username or 'не указан'}\n"
        f"👤 *Имя:* {user.full_name}\n\n"
        f"💡 Чтобы ответить клиенту, ответьте на это сообщение (функция Reply)"
    )
    sent = await ctx.bot.send_message(
        ADMIN_ID, admin_text, parse_mode='Markdown'
    )
    # Запоминаем связь admin_msg_id -> client_chat_id
    reply_map[sent.message_id] = user.id

    # Ответ клиенту
    await q.edit_message_text(
        "✅ *Заявка принята!*\n\n"
        "Напишу в Telegram в течение рабочего дня.\n"
        "Можете также написать напрямую: @ckot\_23",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton('🏠 Главное', callback_data='back_main')]
        ])
    )
    ctx.user_data.clear()
    return ConversationHandler.END


async def cancel_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('❌ Отменено.', reply_markup=main_keyboard())
    ctx.user_data.clear()
    return ConversationHandler.END


async def admin_reply(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Admin отвечает на заявку — пересылаем сообщение клиенту."""
    if update.effective_user.id != ADMIN_ID:
        return
    msg = update.message
    if not msg.reply_to_message:
        return
    replied_id = msg.reply_to_message.message_id
    client_id = reply_map.get(replied_id)
    if not client_id:
        await msg.reply_text('⚠️ Не найден клиент для этой заявки.')
        return
    await ctx.bot.send_message(
        client_id,
        f"📬 *Ответ от ATELIER:*\n\n{msg.text}",
        parse_mode='Markdown'
    )
    await msg.reply_text('✅ Сообщение отправлено клиенту.')


async def unknown(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'Не понял команду. Используйте /start',
        reply_markup=main_keyboard()
    )


def main():
    app = Application.builder().token(TOKEN).build()

    # ConversationHandler для оформления заявки
    conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(button, pattern='^order$'),
            CallbackQueryHandler(button, pattern='^type_'),
        ],
        states={
            CHOOSE_TYPE: [
                CallbackQueryHandler(choose_type, pattern='^type_'),
                CallbackQueryHandler(button, pattern='^cancel$'),
            ],
            ENTER_TASK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_task)
            ],
            ENTER_CONTACT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_contact)
            ],
            CONFIRM: [
                CallbackQueryHandler(confirm, pattern='^confirm$'),
                CallbackQueryHandler(button, pattern='^cancel$'),
            ],
        },
        fallbacks=[
            CommandHandler('cancel', cancel_cmd),
            CallbackQueryHandler(button, pattern='^cancel$'),
        ],
        allow_reentry=True,
    )

    app.add_handler(CommandHandler('start', start))
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(button))  # остальные кнопки

    # Ответы админа клиенту
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.User(ADMIN_ID) & filters.REPLY,
        admin_reply
    ))

    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    print('🤖 Бот ATELIER запущен...')
    app.run_polling(drop_pending_updates=True)


if __name__ == '__main__':
    main()
