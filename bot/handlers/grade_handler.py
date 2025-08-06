# bot/handlers/grade_handler.py

import logging
from decimal import Decimal, InvalidOperation
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)

from bot.db.base import SessionLocal
from bot.services import user_service, subject_service, grade_service

# Configura o logger
logger = logging.getLogger(__name__)

# Define os estados da conversa de notas
SELECT_GRADE_SUBJECT, SELECT_GRADE_NAME, SELECT_GRADE_VALUE = range(50, 53)

# --- Funções da Conversa de Nova Nota ---

async def new_grade_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia a conversa para lançar uma nota (via comando ou botão)."""
    telegram_user = update.effective_user
    if update.callback_query:
        telegram_user = update.callback_query.from_user
        await update.callback_query.answer()

    with SessionLocal() as db:
        user, _ = user_service.get_or_create_user(db, telegram_user.id, telegram_user.first_name, telegram_user.username)
        subjects = subject_service.get_subjects_by_user(db, user)

    if not subjects:
        text = "Você precisa ter matérias cadastradas para lançar uma nota. Use /novamateria."
        if update.callback_query:
            await update.callback_query.message.reply_text(text)
        else:
            await update.message.reply_text(text)
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(s.name, callback_data=f"grade_subject_{s.id}")] for s in subjects]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "Para qual matéria você quer lançar uma nota?\n\n"
        "Envie /cancelar para interromper."
    )
    if update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)
        
    return SELECT_GRADE_SUBJECT

async def received_grade_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe a matéria e pede o nome da avaliação."""
    query = update.callback_query
    await query.answer()

    subject_id = int(query.data.split('_')[-1])
    context.user_data['grade_subject_id'] = subject_id
    
    await query.edit_message_text(text="Matéria selecionada. Qual o nome desta avaliação? (Ex: P1, Trabalho 1, Prova Substitutiva)")
    return SELECT_GRADE_NAME

async def received_grade_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe o nome da avaliação e pede a nota."""
    context.user_data['grade_name'] = update.message.text
    await update.message.reply_text("Nome da avaliação definido. Agora, qual foi a nota que você tirou?\n\n(Use *ponto* para decimais, ex: 8.5 ou 10.0)")
    return SELECT_GRADE_VALUE

async def received_grade_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe a nota, valida, salva no banco e finaliza."""
    try:
        # Substitui vírgula por ponto e converte para Decimal
        grade_value_str = update.message.text.replace(',', '.')
        grade_value = Decimal(grade_value_str)

        if grade_value < 0:
            raise ValueError("Nota não pode ser negativa.")
            
    except (InvalidOperation, ValueError):
        await update.message.reply_text("Valor inválido. 😓 Por favor, envie um número (ex: 7.5 ou 10).")
        return SELECT_GRADE_VALUE # Permanece no mesmo estado

    # Coleta todos os dados
    subject_id = context.user_data['grade_subject_id']
    grade_name = context.user_data['grade_name']
    telegram_user = update.effective_user
    
    with SessionLocal() as db:
        user, _ = user_service.get_or_create_user(db, telegram_user.id, telegram_user.first_name, telegram_user.username)
        subject = subject_service.get_subject_by_id(db, subject_id)
        
        # Usa o serviço para adicionar a nota
        grade_service.add_grade(db, user, subject, grade_name, grade_value)
        
        await update.message.reply_text(f"✅ Nota *{grade_value}* para '{grade_name}' lançada com sucesso na matéria *{subject.name}*!", parse_mode='Markdown')

    context.user_data.clear()
    return ConversationHandler.END

async def grade_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela a operação."""
    if update.callback_query:
        await update.callback_query.edit_message_text("Operação cancelada.")
    else:
        await update.message.reply_text("Operação cancelada.")
    context.user_data.clear()
    return ConversationHandler.END

# --- Montagem do ConversationHandler ---

def setup_grade_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("addnota", new_grade_start),
            CallbackQueryHandler(new_grade_start, pattern="^start_new_grade$")
            ],
        states={
            SELECT_GRADE_SUBJECT: [CallbackQueryHandler(received_grade_subject, pattern="^grade_subject_")],
            SELECT_GRADE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_grade_name)],
            SELECT_GRADE_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_grade_value)],
        },
        fallbacks=[CommandHandler("cancelar", grade_cancel)],
    )