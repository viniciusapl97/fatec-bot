# bot/handlers/import_handler.py

import logging
import json
from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, filters
)

from bot.db.base import SessionLocal
from bot.services import user_service, subject_service
from bot.core import dialogs

logger = logging.getLogger(__name__)

# Estado da conversa
AWAITING_FILE = 0

# O formato JSON que será mostrado ao usuário como exemplo
JSON_EXAMPLE = """
<code>[
    {
        "nome": "Inteligência Artificial",
        "professor": "Profa. Morgana",
        "dia_semana": "Quarta",
        "sala": "L301",
        "horario_inicio": "21:00",
        "horario_fim": "22:40",
        "semestre": 5
    },
    {
        "nome": "Banco de Dados",
        "professor": "Prof. Jovelino",
        "dia_semana": "Sexta",
        "sala": "B102",
        "horario_inicio": "19:00",
        "horario_fim": "22:40",
        "semestre": 5
    }
]</code>
"""

# =============================================================================
# Lógica da Conversa de Importação
# =============================================================================

async def import_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia a conversa de importação."""
    text = dialogs.IMPORT_START_PROMPT.format(json_example=JSON_EXAMPLE)
    await update.message.reply_html(text)
    return AWAITING_FILE

async def received_json_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe, processa o arquivo JSON e cadastra as matérias."""
    document = update.message.document
    if not document or not document.file_name.endswith('.json'):
        await update.message.reply_text(dialogs.IMPORT_INVALID_FILE_EXTENSION)
        return AWAITING_FILE

    await update.message.reply_text(dialogs.IMPORT_PROCESSING_FILE)

    file = await document.get_file()
    file_content = await file.download_as_bytearray()

    try:
        subjects_data = json.loads(file_content.decode('utf-8'))
        if not isinstance(subjects_data, list):
            raise ValueError(dialogs.IMPORT_JSON_NOT_A_LIST)
            
    except (json.JSONDecodeError, ValueError) as e:
        await update.message.reply_text(dialogs.IMPORT_JSON_ERROR.format(error=e))
        return AWAITING_FILE

    telegram_user = update.effective_user
    with SessionLocal() as db:
        user, _ = user_service.get_or_create_user(db, telegram_user.id, telegram_user.first_name, telegram_user.username)
        report = subject_service.bulk_create_subjects(db, user, subjects_data)

    # Monta o relatório final
    if report["errors"]:
        error_list = "\n".join(f"- {error}" for error in report["errors"])
        message = dialogs.IMPORT_FAILURE.format(error_list=error_list)
    else:
        message = dialogs.IMPORT_SUCCESS.format(count=report['success'])

    await update.message.reply_html(message)
    return ConversationHandler.END

async def import_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela a operação de importação."""
    await update.message.reply_text(dialogs.OPERATION_CANCELED)
    return ConversationHandler.END

# =============================================================================
# Setup do Handler
# =============================================================================

def setup_import_handler() -> ConversationHandler:
    """Cria e configura o ConversationHandler para /import."""
    return ConversationHandler(
        entry_points=[CommandHandler("import", import_start)],
        states={
            AWAITING_FILE: [MessageHandler(filters.Document.FileExtension("json"), received_json_file)]
        },
        fallbacks=[CommandHandler("cancelar", import_cancel)],
    )