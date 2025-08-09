import logging
import dateparser
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)
from bot.core import dialogs

logger = logging.getLogger(__name__)

AWAITING_MESSAGE, AWAITING_TIME = range(2)

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
    
    reminder_datetime = dateparser.parse(time_text, languages=['pt'])
    
    if not reminder_datetime:
        await update.message.reply_text(dialogs.REMINDER_CUSTOM_ERROR_TIME)
        return AWAITING_TIME

    reminder_message = context.user_data['reminder_message']
    user_id = update.effective_user.id
    
    async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(
            chat_id=user_id, 
            text=dialogs.REMINDER_CUSTOM_NOTIFICATION.format(reminder_message=reminder_message)
        )

    context.job_queue.run_once(send_reminder, reminder_datetime)
    
    await update.message.reply_html(
        dialogs.REMINDER_CUSTOM_SUCCESS.format(
            reminder_message=reminder_message,
            reminder_datetime=reminder_datetime.strftime('%d/%m/%Y às %H:%M')
        )
    )
    
    context.user_data.clear()
    return ConversationHandler.END

def setup_reminder_handler() -> ConversationHandler:
    """Cria e configura o ConversationHandler para /lembrar."""
    return ConversationHandler(
        entry_points=[CommandHandler("lembrar", reminder_start)],
        states={
            AWAITING_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_reminder_message)],
            AWAITING_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_reminder_time)],
        },
        fallbacks=[CommandHandler("cancelar", dialogs.OPERATION_CANCELED)],
    )