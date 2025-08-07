# bot/handlers/bug_report_handler.py

import logging
from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, filters
)

from bot.services import email_service
from bot.core import dialogs

logger = logging.getLogger(__name__)

AWAITING_SCREENSHOT, AWAITING_DESCRIPTION = range(2)

async def bug_report_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia o fluxo de relatório de bug."""
    await update.message.reply_text(
        "Você encontrou um bug? Obrigado por ajudar! 🙏\n\n"
        "Por favor, me envie um **print da tela (screenshot)** mostrando o problema.\n\n"
        "Envie /cancelar para sair."
    )
    return AWAITING_SCREENSHOT

async def received_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe o screenshot e pede a descrição."""
    photo = update.message.photo[-1] # Pega a foto na maior resolução
    file = await photo.get_file()
    
    photo_bytes = await file.download_as_bytearray()
    context.user_data['bug_screenshot'] = photo_bytes
    
    await update.message.reply_text(
        "Ótimo, recebi a imagem. Agora, por favor, **descreva o que aconteceu** ou o que você esperava que acontecesse."
    )
    return AWAITING_DESCRIPTION

async def received_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe a descrição, envia o email e finaliza."""
    description = update.message.text
    screenshot_data = context.user_data['bug_screenshot']
    user = update.effective_user
    
    subject = f"Relatório de Bug do Jovis Bot - Usuário: {user.first_name} ({user.id})"
    body = (
        f"Relatório de Bug enviado por:\n"
        f"Nome: {user.first_name}\n"
        f"Username: @{user.username}\n"
        f"ID: {user.id}\n"
        f"-----------------------------------\n\n"
        f"DESCRIÇÃO DO PROBLEMA:\n{description}"
    )
    
    await update.message.reply_text("Enviando seu relatório para a equipe de desenvolvimento... 👨‍💻")
    
    success = email_service.send_bug_report_email(subject, body, screenshot_data)
    
    if success:
        await update.message.reply_text("Obrigado! Seu relatório foi enviado com sucesso. Vamos analisar o mais rápido possível.")
    else:
        await update.message.reply_text("Desculpe, ocorreu um erro ao tentar enviar seu relatório. Por favor, tente novamente mais tarde.")
        
    context.user_data.clear()
    return ConversationHandler.END

def setup_bug_report_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("bug", bug_report_start)],
        states={
            AWAITING_SCREENSHOT: [MessageHandler(filters.PHOTO, received_screenshot)],
            AWAITING_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_description)],
        },
        fallbacks=[CommandHandler("cancelar", dialogs.OPERATION_CANCELED)],
    )