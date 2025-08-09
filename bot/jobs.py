# bot/jobs.py

import logging
from collections import defaultdict
from telegram.ext import ContextTypes

from bot.db.base import SessionLocal
from bot.services import activity_service
from bot.core import dialogs

logger = logging.getLogger(__name__)

async def check_deadlines_job(context: ContextTypes.DEFAULT_TYPE):
    """
    A tarefa que roda diariamente para verificar e enviar lembretes de prazos.
    """
    logger.info("Executando a tarefa de verificação de prazos (check_deadlines_job)...")
    
    reminders_to_send = defaultdict(list)
    
    with SessionLocal() as db:
        # Busca atividades para amanhã (1 dia de antecedência)
        activities_tomorrow = activity_service.get_upcoming_activities(db, days_ahead=1)
        for activity in activities_tomorrow:
            reminders_to_send[activity.user_id].append(
                dialogs.REMINDER_AUTOMATIC_TOMORROW.format(
                    activity_type=activity.activity_type.capitalize(),
                    activity_name=activity.name,
                    subject_name=activity.subject.name
                )
            )
            
        # Busca atividades para daqui a 3 dias
        activities_in_3_days = activity_service.get_upcoming_activities(db, days_ahead=3)
        for activity in activities_in_3_days:
            reminders_to_send[activity.user_id].append(
                dialogs.REMINDER_AUTOMATIC_3_DAYS.format(
                    activity_type=activity.activity_type.capitalize(),
                    activity_name=activity.name,
                    subject_name=activity.subject.name
                )
            )

    # Envia os lembretes agrupados por usuário
    for user_id, messages in reminders_to_send.items():
        full_message = dialogs.REMINDER_AUTOMATIC_HEADER + "\n\n".join(messages)
        try:
            await context.bot.send_message(chat_id=user_id, text=full_message, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Não foi possível enviar lembrete para o usuário {user_id}: {e}")