# bot/jobs.py

import logging
from collections import defaultdict
from telegram.ext import ContextTypes

from bot.db.base import SessionLocal
from bot.services import user_service
from bot.core import dialogs
from bot.handlers.common import build_week_summary_message

logger = logging.getLogger(__name__)

async def check_deadlines_job(context: ContextTypes.DEFAULT_TYPE):
    """
    A tarefa que roda diariamente para verificar e enviar lembretes de prazos.
    """
    logger.info("Executando a tarefa de verificação de prazos (check_deadlines_job)...")
    
    reminders_to_send = defaultdict(list)

    with SessionLocal() as db:
        # Busca atividades para amanhã (1 dia de antecedência)
        activities_tomorrow = user_service.get_upcoming_activities(db, days_ahead=1)
        for activity in activities_tomorrow:
            reminders_to_send[activity.user_id].append(
                dialogs.REMINDER_AUTOMATIC_TOMORROW.format(
                    activity_type=activity.activity_type.capitalize(),
                    activity_name=activity.name,
                    subject_name=activity.subject.name
                )
            )

        # Busca atividades para daqui a 3 dias
        activities_in_3_days = user_service.get_upcoming_activities(db, days_ahead=3)
        for activity in activities_in_3_days:
            reminders_to_send[activity.user_id].append(
                dialogs.REMINDER_AUTOMATIC_3_DAYS.format(
                    activity_type=activity.activity_type.capitalize(),
                    activity_name=activity.name,
                    subject_name=activity.subject.name
                )
            )

        disabled_user_ids = user_service.get_user_ids_with_notifications_disabled(db)

    # Envia os lembretes agrupados por usuário (pulando quem desativou em /notificacoes)
    for user_id, messages in reminders_to_send.items():
        if user_id in disabled_user_ids:
            continue
        full_message = dialogs.REMINDER_AUTOMATIC_HEADER + "\n\n".join(messages)
        try:
            await context.bot.send_message(chat_id=user_id, text=full_message, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Não foi possível enviar lembrete para o usuário {user_id}: {e}")


async def send_weekly_summary_job(context: ContextTypes.DEFAULT_TYPE):
    """
    Tarefa que roda toda segunda de manhã e manda o resumo da semana
    (equivalente ao /semana) para todos os usuários cadastrados.
    """
    logger.info("Executando a tarefa de resumo semanal (send_weekly_summary_job)...")

    with SessionLocal() as db:
        summaries = {
            user.user_id: dialogs.WEEKLY_SUMMARY_INTRO + build_week_summary_message(db, user)
            for user in user_service.get_all_active_users(db)
        }

    for user_id, message in summaries.items():
        try:
            await context.bot.send_message(chat_id=user_id, text=message, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Não foi possível enviar o resumo semanal para o usuário {user_id}: {e}")