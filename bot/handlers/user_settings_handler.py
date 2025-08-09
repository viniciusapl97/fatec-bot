import logging
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from bot.db.base import SessionLocal
from bot.services import user_service
from bot.core import dialogs

logger = logging.getLogger(__name__)

# Estado da conversa
AWAITING_CONFIRMATION = 0
CONFIRMATION_PHRASE = "excluir todos os meus dados"

async def delete_data_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia o fluxo de exclusão de dados, enviando um aviso."""
    await update.message.reply_html(dialogs.DELETE_DATA_WARNING)
    return AWAITING_CONFIRMATION

async def confirm_data_deletion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Verifica a frase de confirmação e apaga os dados do usuário."""
    user_input = update.message.text
    
    if user_input.strip().lower() == CONFIRMATION_PHRASE:
        user_id = update.effective_user.id
        with SessionLocal() as db:
            deleted = user_service.delete_user_by_id(db, user_id)
        
        if deleted:
            await update.message.reply_html(dialogs.DELETE_DATA_SUCCESS)
        else:
            # Caso raro em que o usuário não foi encontrado no DB, mas tentou apagar
            await update.message.reply_text("Não encontrei seus dados para apagar.")
            
    else:
        await update.message.reply_text(dialogs.DELETE_DATA_CONFIRMATION_INVALID)
    
    context.user_data.clear()
    return ConversationHandler.END

async def delete_data_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela a operação de exclusão."""
    await update.message.reply_text(dialogs.OPERATION_CANCELED)
    context.user_data.clear()
    return ConversationHandler.END


def setup_delete_user_handler() -> ConversationHandler:
    """Cria e configura o ConversationHandler para /deletardados."""
    return ConversationHandler(
        entry_points=[CommandHandler("deletardados", delete_data_start)],
        states={
            AWAITING_CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_data_deletion)]
        },
        fallbacks=[CommandHandler("cancelar", delete_data_cancel)],
    )