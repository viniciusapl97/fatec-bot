# bot/handlers/export_handler.py

import json
import logging
from datetime import datetime
from io import BytesIO

from telegram import Update
from telegram.ext import ContextTypes

from bot.db.base import SessionLocal
from bot.services import user_service, activity_service, export_service
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


async def export_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gera e envia um arquivo .ics com os trabalhos e provas do usuário."""
    telegram_user = update.effective_user

    with SessionLocal() as db:
        user, _ = user_service.get_or_create_user(db, telegram_user.id, telegram_user.first_name, telegram_user.username)
        activities = activity_service.get_activities_by_user(db, user)

        if not activities:
            await update.message.reply_text(dialogs.EXPORT_CALENDAR_EMPTY)
            return

        # Monta o .ics ainda dentro da sessão: build_activities_ics acessa
        # activity.subject.name (lazy load), que quebraria depois que a sessão fechasse.
        ics_content = export_service.build_activities_ics(activities)

    await update.message.reply_text(dialogs.EXPORT_CALENDAR_GENERATING)

    file = BytesIO(ics_content.encode('utf-8'))
    file.name = f"jovis_calendario_{telegram_user.id}.ics"

    await update.message.reply_document(document=file, caption=dialogs.EXPORT_CALENDAR_SUCCESS)
