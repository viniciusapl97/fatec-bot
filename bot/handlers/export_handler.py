# bot/handlers/export_handler.py

import json
import logging
from datetime import datetime
from io import BytesIO

from telegram import Update
from telegram.ext import ContextTypes

from bot.db.base import SessionLocal
from bot.services import user_service, export_service
from bot.core import dialogs
from bot.core.settings import TIMEZONE

logger = logging.getLogger(__name__)


async def export_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gera e envia um arquivo JSON com todos os dados do usuário."""
    telegram_user = update.effective_user
    await update.message.reply_text(dialogs.EXPORT_GENERATING)

    with SessionLocal() as db:
        user, _ = user_service.get_or_create_user(db, telegram_user.id, telegram_user.first_name, telegram_user.username)
        export_payload = export_service.build_user_export(db, user)

    export_payload["exportado_em"] = datetime.now(TIMEZONE).strftime('%d/%m/%Y %H:%M')

    json_bytes = json.dumps(export_payload, ensure_ascii=False, indent=2).encode('utf-8')
    file = BytesIO(json_bytes)
    file.name = f"jovis_dados_{telegram_user.id}.json"

    await update.message.reply_document(document=file, caption=dialogs.EXPORT_SUCCESS)
