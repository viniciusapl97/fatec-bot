import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    TypeHandler,
)

from bot.db.base import SessionLocal
from bot.services import user_service
from bot.core import dialogs
from bot.core.conversation_timeout import CONVERSATION_TIMEOUT_SECONDS, notify_conversation_timeout

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


# =============================================================================
# Notificações automáticas de prazo (/notificacoes)
# =============================================================================

def _build_notifications_view(enabled: bool):
    """Monta o texto e o botão de alternância pro status das notificações."""
    status = dialogs.NOTIFICATIONS_ON if enabled else dialogs.NOTIFICATIONS_OFF
    text = dialogs.NOTIFICATIONS_STATUS.format(status=status)
    button_text = dialogs.NOTIFICATIONS_BUTTON_DISABLE if enabled else dialogs.NOTIFICATIONS_BUTTON_ENABLE
    keyboard = [[InlineKeyboardButton(button_text, callback_data="toggle_notifications")]]
    return text, InlineKeyboardMarkup(keyboard)


async def notifications_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mostra se as notificações automáticas de prazo estão ativadas, com botão pra alternar."""
    telegram_user = update.effective_user

    with SessionLocal() as db:
        user, _ = user_service.get_or_create_user(db, telegram_user.id, telegram_user.first_name, telegram_user.username)
        text, reply_markup = _build_notifications_view(user.notifications_enabled)

    await update.message.reply_html(text, reply_markup=reply_markup)


async def toggle_notifications_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Alterna o status das notificações automáticas de prazo."""
    query = update.callback_query
    await query.answer()
    telegram_user = query.from_user

    with SessionLocal() as db:
        user, _ = user_service.get_or_create_user(db, telegram_user.id, telegram_user.first_name, telegram_user.username)
        user_service.set_notifications_enabled(db, user, not user.notifications_enabled)
        text, reply_markup = _build_notifications_view(user.notifications_enabled)

    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')


def setup_notifications_handler() -> list:
    """Cria os handlers (comando + callback) para /notificacoes."""
    return [
        CommandHandler("notificacoes", notifications_status),
        CallbackQueryHandler(toggle_notifications_callback, pattern="^toggle_notifications$"),
    ]


# =============================================================================
# Horário dos avisos automáticos de prazo (/horarionotificacao)
# =============================================================================

def _build_notification_hour_view(current_hour: int):
    """Monta o texto e a grade de botões (0h-23h) pra escolher o horário dos avisos."""
    text = dialogs.NOTIFICATION_HOUR_STATUS.format(hour=current_hour)
    keyboard = []
    for row_start in range(0, 24, 6):
        row = []
        for hour in range(row_start, row_start + 6):
            label = f"✅ {hour}h" if hour == current_hour else f"{hour}h"
            row.append(InlineKeyboardButton(label, callback_data=f"set_notif_hour_{hour}"))
        keyboard.append(row)
    return text, InlineKeyboardMarkup(keyboard)


async def notification_hour_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mostra o horário atual dos avisos de prazo, com botões pra trocar."""
    telegram_user = update.effective_user

    with SessionLocal() as db:
        user, _ = user_service.get_or_create_user(db, telegram_user.id, telegram_user.first_name, telegram_user.username)
        text, reply_markup = _build_notification_hour_view(user.notification_hour)

    await update.message.reply_html(text, reply_markup=reply_markup)


async def set_notification_hour_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Define a nova hora escolhida para os avisos automáticos de prazo."""
    query = update.callback_query
    await query.answer()
    hour = int(query.data.split('_')[-1])
    telegram_user = query.from_user

    with SessionLocal() as db:
        user, _ = user_service.get_or_create_user(db, telegram_user.id, telegram_user.first_name, telegram_user.username)
        user_service.set_notification_hour(db, user, hour)
        text, reply_markup = _build_notification_hour_view(user.notification_hour)

    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')


def setup_notification_hour_handler() -> list:
    """Cria os handlers (comando + callback) para /horarionotificacao."""
    return [
        CommandHandler("horarionotificacao", notification_hour_status),
        CallbackQueryHandler(set_notification_hour_callback, pattern="^set_notif_hour_"),
    ]


def setup_delete_user_handler() -> ConversationHandler:
    """Cria e configura o ConversationHandler para /deletardados."""
    return ConversationHandler(
        entry_points=[CommandHandler("deletardados", delete_data_start)],
        states={
            AWAITING_CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_data_deletion)],
            ConversationHandler.TIMEOUT: [TypeHandler(Update, notify_conversation_timeout)],
        },
        fallbacks=[CommandHandler("cancelar", delete_data_cancel)],
        conversation_timeout=CONVERSATION_TIMEOUT_SECONDS,
    )