import logging
from datetime import datetime

import dateparser
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    JobQueue,
    filters,
    TypeHandler,
)
from bot.db.base import SessionLocal
from bot.services import user_service, reminder_service
from bot.core import dialogs
from bot.core.settings import TIMEZONE_NAME
from bot.core.conversation_timeout import CONVERSATION_TIMEOUT_SECONDS, notify_conversation_timeout

logger = logging.getLogger(__name__)

AWAITING_MESSAGE, AWAITING_TIME = range(2)


async def _deliver_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback do job_queue: entrega o lembrete e remove seu registro do banco."""
    job_data = context.job.data
    reminder_id = job_data['reminder_id']
    user_id = job_data['user_id']
    reminder_message = job_data['reminder_message']

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=dialogs.REMINDER_CUSTOM_NOTIFICATION.format(reminder_message=reminder_message)
        )
    except Exception as e:
        logger.error(f"Não foi possível entregar o lembrete {reminder_id} para o usuário {user_id}: {e}")

    with SessionLocal() as db:
        reminder_service.delete_reminder_by_id(db, reminder_id)


def schedule_reminder(job_queue: JobQueue, reminder_id: int, user_id: int, message: str, when: datetime) -> None:
    """Agenda a entrega de um lembrete já persistido no banco."""
    job_queue.run_once(
        _deliver_reminder,
        when,
        data={'reminder_id': reminder_id, 'user_id': user_id, 'reminder_message': message},
        name=f"reminder_{reminder_id}",
    )

async def reminder_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia a conversa para criar um lembrete personalizado."""
    await update.message.reply_html(dialogs.REMINDER_CUSTOM_ASK_MESSAGE)
    return AWAITING_MESSAGE

async def received_reminder_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe a mensagem do lembrete e pede o horário."""
    context.user_data['reminder_message'] = update.message.text
    await update.message.reply_html(dialogs.REMINDER_CUSTOM_ASK_TIME)
    return AWAITING_TIME

async def received_reminder_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe o horário, agenda a tarefa e finaliza."""
    time_text = update.message.text
    
    reminder_datetime = dateparser.parse(
        time_text,
        languages=['pt'],
        settings={
            'TIMEZONE': TIMEZONE_NAME,
            'TO_TIMEZONE': TIMEZONE_NAME,
            'RETURN_AS_TIMEZONE_AWARE': True,
        },
    )
    
    if not reminder_datetime:
        await update.message.reply_text(dialogs.REMINDER_CUSTOM_ERROR_TIME)
        return AWAITING_TIME

    reminder_message = context.user_data['reminder_message']
    telegram_user = update.effective_user

    with SessionLocal() as db:
        user, _ = user_service.get_or_create_user(db, telegram_user.id, telegram_user.first_name, telegram_user.username)
        reminder = reminder_service.create_reminder(db, user, reminder_message, reminder_datetime)
        reminder_id = reminder.id

    schedule_reminder(context.job_queue, reminder_id, telegram_user.id, reminder_message, reminder_datetime)

    await update.message.reply_html(
        dialogs.REMINDER_CUSTOM_SUCCESS.format(
            reminder_message=reminder_message,
            reminder_datetime=reminder_datetime.strftime('%d/%m/%Y às %H:%M')
        )
    )
    
    context.user_data.clear()
    return ConversationHandler.END

async def reminder_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela a criação do lembrete personalizado."""
    await update.message.reply_html(dialogs.OPERATION_CANCELED)
    context.user_data.clear()
    return ConversationHandler.END


def setup_reminder_handler() -> ConversationHandler:
    """Cria e configura o ConversationHandler para /lembrar."""
    return ConversationHandler(
        entry_points=[CommandHandler("lembrar", reminder_start)],
        states={
            AWAITING_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_reminder_message)],
            AWAITING_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_reminder_time)],
            ConversationHandler.TIMEOUT: [TypeHandler(Update, notify_conversation_timeout)],
        },
        fallbacks=[CommandHandler("cancelar", reminder_cancel)],
        conversation_timeout=CONVERSATION_TIMEOUT_SECONDS,
    )


# =============================================================================
# Seção: Listagem e cancelamento de lembretes (/meuslembretes)
# =============================================================================

def _truncate(text: str, max_length: int = 30) -> str:
    """Encurta um texto para caber no botão inline, sem quebrar o layout."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 1].rstrip() + "…"


async def list_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lista os lembretes pendentes do usuário, cada um com um botão para cancelar."""
    telegram_user = update.effective_user

    with SessionLocal() as db:
        user, _ = user_service.get_or_create_user(db, telegram_user.id, telegram_user.first_name, telegram_user.username)
        reminders = reminder_service.get_pending_reminders_by_user(db, user)

    if not reminders:
        await update.message.reply_text(dialogs.REMINDER_LIST_EMPTY)
        return

    keyboard = [
        [InlineKeyboardButton(
            dialogs.REMINDER_LIST_BUTTON.format(
                message=_truncate(r.message),
                when=r.remind_at.strftime('%d/%m %H:%M'),
            ),
            callback_data=f"delete_reminder_{r.id}",
        )]
        for r in reminders
    ]
    await update.message.reply_html(dialogs.REMINDER_LIST_HEADER, reply_markup=InlineKeyboardMarkup(keyboard))


async def delete_reminder_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancela um lembrete pendente: remove do banco e do job_queue."""
    query = update.callback_query
    await query.answer()
    reminder_id = int(query.data.split('_')[-1])

    with SessionLocal() as db:
        deleted = reminder_service.delete_reminder_by_id(db, reminder_id)

    if not deleted:
        await query.edit_message_text(dialogs.ERROR_NOT_FOUND)
        return

    # O registro já saiu do banco; remove também o job em memória para o
    # lembrete não disparar mesmo assim caso o bot não reinicie antes da hora.
    for job in context.job_queue.get_jobs_by_name(f"reminder_{reminder_id}"):
        job.schedule_removal()

    await query.edit_message_text(dialogs.REMINDER_LIST_DELETE_SUCCESS)


def setup_reminder_list_handler() -> list:
    """Cria os handlers (comando + callback) para listar/cancelar lembretes pendentes."""
    return [
        CommandHandler("meuslembretes", list_reminders),
        CallbackQueryHandler(delete_reminder_callback, pattern="^delete_reminder_"),
    ]