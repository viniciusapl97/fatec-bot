import logging
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import Forbidden
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)

from bot.db.base import SessionLocal
from bot.services import user_service
from bot.core import dialogs
from bot.decorators import admin_only # Importamos nosso decorador de segurança

logger = logging.getLogger(__name__)

# Estados da conversa
AWAITING_MESSAGE, AWAITING_CONFIRMATION = range(2)

@admin_only
async def send_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """(Admin) Envia uma mensagem para um usuário específico."""
    admin = update.effective_user
    
    # Validação dos argumentos
    if not context.args or len(context.args) < 2:
        await update.message.reply_html(dialogs.ADMIN_SEND_USAGE)
        return
        
    try:
        target_user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_html(dialogs.ADMIN_SEND_USAGE)
        return
    
    message_text = " ".join(context.args[1:])
    
    # Verifica se o usuário existe no nosso DB
    with SessionLocal() as db:
        target_user = user_service.get_user_by_telegram_id(db, target_user_id)
        
    if not target_user:
        await update.message.reply_html(dialogs.ADMIN_SEND_FAILURE_NOT_FOUND.format(user_id=target_user_id))
        return
        
    # Tenta enviar a mensagem
    try:
        await context.bot.send_message(chat_id=target_user_id, text=message_text)
        await update.message.reply_html(
            dialogs.ADMIN_SEND_SUCCESS.format(user_name=target_user.first_name, user_id=target_user_id)
        )
    except Forbidden:
        await update.message.reply_html(
            dialogs.ADMIN_SEND_FAILURE_BLOCKED.format(user_name=target_user.first_name, user_id=target_user_id)
        )
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem para {target_user_id}: {e}")
        await update.message.reply_html(dialogs.ADMIN_SEND_FAILURE_GENERAL.format(user_id=target_user_id))


@admin_only
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia o fluxo de transmissão."""
    await update.message.reply_html(dialogs.ADMIN_BROADCAST_START)
    return AWAITING_MESSAGE

async def received_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe a mensagem, armazena e pede confirmação."""
    context.user_data['broadcast_message'] = update.message
    
    with SessionLocal() as db:
        users = user_service.get_all_active_users(db)
        user_count = len(users)

    context.user_data['user_list'] = [user.user_id for user in users]

    await update.message.reply_html(
        text=dialogs.ADMIN_BROADCAST_CONFIRM.format(
            message=update.message.text_html,
            user_count=user_count
        ),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Enviar para Todos", callback_data="confirm_broadcast")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancel_broadcast")]
        ])
    )
    return AWAITING_CONFIRMATION

async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Envia a mensagem em massa para todos os usuários."""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel_broadcast":
        await query.edit_message_text(dialogs.ADMIN_BROADCAST_CANCELED)
        context.user_data.clear()
        return ConversationHandler.END
    
    await query.edit_message_text(dialogs.ADMIN_BROADCAST_SENDING)

    message_to_send = context.user_data['broadcast_message']
    user_ids = context.user_data['user_list']
    
    success_count = 0
    failure_count = 0

    for user_id in user_ids:
        try:
            await context.bot.copy_message(
                chat_id=user_id,
                from_chat_id=message_to_send.chat_id,
                message_id=message_to_send.message_id
            )
            success_count += 1
        except Forbidden:
            logger.warning(f"Não foi possível enviar mensagem para o usuário {user_id}. Ele bloqueou o bot.")
            failure_count += 1
        except Exception as e:
            logger.error(f"Erro inesperado ao enviar mensagem para {user_id}: {e}")
            failure_count += 1
        
        await asyncio.sleep(0.1) # Pequena pausa para não sobrecarregar a API do Telegram

    # Envia o relatório final para o admin
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=dialogs.ADMIN_BROADCAST_REPORT.format(
            success_count=success_count,
            failure_count=failure_count
        )
    )
    
    context.user_data.clear()
    return ConversationHandler.END


def setup_admin_handlers() -> list:
    """Cria e configura todos os handlers de admin."""
    
    broadcast_handler = ConversationHandler(
        entry_points=[CommandHandler("broadcast", broadcast_start)],
        states={
            AWAITING_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_message)],
            AWAITING_CONFIRMATION: [CallbackQueryHandler(send_broadcast)],
        },
        fallbacks=[CommandHandler("cancelar", dialogs.OPERATION_CANCELED)],
    )

    send_to_user_handler = CommandHandler("enviar", send_to_user)
    
    return [broadcast_handler, send_to_user_handler]

