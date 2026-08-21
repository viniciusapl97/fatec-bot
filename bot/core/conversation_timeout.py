# bot/core/conversation_timeout.py

from telegram import Update
from telegram.ext import ContextTypes

from bot.core import dialogs

# Tempo de inatividade (em segundos) até uma conversa ser cancelada automaticamente.
CONVERSATION_TIMEOUT_SECONDS = 600


async def notify_conversation_timeout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler genérico para o estado ConversationHandler.TIMEOUT de todas as conversas."""
    context.user_data.clear()
    chat = update.effective_chat
    if chat:
        await context.bot.send_message(chat_id=chat.id, text=dialogs.CONVERSATION_TIMEOUT)
