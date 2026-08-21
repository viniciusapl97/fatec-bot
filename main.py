# main.py

import logging
from telegram import BotCommand
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    Defaults,
)
from datetime import time, timedelta

from bot.core.settings import TELEGRAM_TOKEN, TIMEZONE
from bot.db.base import Base, engine, SessionLocal
from bot.db import models
from bot.services import reminder_service

# Importa todas as funções e setups de handlers
from bot.handlers.common import start, help_command, privacy_policy, button_handler, today_command, week_command
from bot.handlers.reminder_handler import setup_reminder_handler, setup_reminder_list_handler, schedule_reminder
from bot.handlers.subject_handler import list_subjects, setup_subject_handler, setup_management_handler, setup_report_handler
from bot.handlers.activity_handler import list_activities, setup_activity_handler, setup_activity_management_handler
from bot.handlers.absence_handler import setup_absence_handler, setup_absence_management_handler, report_absences
from bot.handlers.grade_handler import setup_grade_handler, setup_grade_management_handler
from bot.handlers.import_handler import setup_import_handler
from bot.handlers.export_handler import export_data, export_calendar
from bot.handlers.bug_report_handler import setup_bug_report_handler
from bot.handlers.fatec_handler import setup_fatec_handler
from bot.handlers.user_settings_handler import setup_delete_user_handler, setup_notifications_handler, setup_notification_hour_handler
from bot.handlers.admin_handler import setup_admin_handlers
from bot.jobs import check_deadlines_job, send_weekly_summary_job


# Configura o logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def post_init_configuration(application: Application) -> None:
    """
    Configuração pós-inicialização para definir os comandos do bot.
    """
    commands = [
        BotCommand("start", "Inicia o bot e mostra o menu principal"),
        BotCommand("help", "Mostra a lista de todos os comandos"),
        BotCommand("hoje", "Resumo do dia (aulas e atividades)"),
        BotCommand("semana", "Lista as atividades dos próximos 7 dias"),
        BotCommand("grade", "Exibe sua grade horária completa"),
        BotCommand("calendario", "Lista seus trabalhos e provas"),
        BotCommand("relatorio", "Gera um relatório detalhado de uma matéria"),
        BotCommand("addmateria", "Adiciona uma nova matéria"),
        BotCommand("addtrabalho", "Adiciona um novo trabalho"),
        BotCommand("addprova", "Adiciona uma nova prova"),
        BotCommand("faltei", "Registra uma ou mais faltas"),
        BotCommand("faltas", "Exibe o total de faltas por matéria"),
        BotCommand("addnota", "Lança uma nova nota para uma matéria"),
        BotCommand("gerenciarmaterias", "Edita ou exclui suas matérias"),
        BotCommand("gerenciarfaltas", "Edita ou exclui registros de faltas"),
        BotCommand("gerenciartrabalhos", "Edita ou exclui trabalhos"),
        BotCommand("gerenciarprovas", "Edita ou exclui provas"),
        BotCommand("bug", "Reportar um problema ou bug para o desenvolvedor"),
        BotCommand("fatec", "Configura a grade horária de um curso da Fatec S.B."),
        BotCommand("deletardados", "Apaga permanentemente todos os seus dados do bot"),
        BotCommand("broadcast", "(Admin) Envia uma mensagem para todos os usuários"),
        BotCommand("enviar", "(Admin) Envia mensagem para um usuário"),
        BotCommand("stats", "(Admin) Mostra estatísticas gerais de uso do bot"),
        BotCommand("lembrar", "Cria um lembrete personalizado"),
        BotCommand("meuslembretes", "Lista e permite cancelar seus lembretes pendentes"),
        BotCommand("exportar", "Baixa uma cópia de todos os seus dados em JSON"),
        BotCommand("exportarcalendario", "Baixa seus trabalhos e provas em formato .ics"),
        BotCommand("privacidade", "Mostra a política de privacidade"),
        BotCommand("notificacoes", "Ativa ou desativa os avisos automáticos de prazo"),
        BotCommand("horarionotificacao", "Escolhe o horário dos avisos automáticos de prazo"),
    ]
    await application.bot.set_my_commands(commands)


def reschedule_pending_reminders(application: Application) -> None:
    """
    Reagenda no job_queue os lembretes personalizados (/lembrar) que ainda não
    foram entregues. Necessário porque os jobs agendados vivem só em memória
    e são perdidos toda vez que o bot reinicia.
    """
    with SessionLocal() as db:
        pending_reminders = reminder_service.get_pending_reminders(db)
        for reminder in pending_reminders:
            schedule_reminder(
                application.job_queue,
                reminder.id,
                reminder.user_id,
                reminder.message,
                reminder.remind_at,
            )
    if pending_reminders:
        logger.info("Reagendados %d lembrete(s) pendente(s).", len(pending_reminders))


def main() -> None:
    """Inicia o bot e o mantém rodando."""

    logger.info("Criando/Verificando tabelas no banco de dados...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tabelas verificadas/criadas com sucesso.")

    defaults = Defaults(tzinfo=TIMEZONE)
    application = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .defaults(defaults)
        .post_init(post_init_configuration)
        .build()
    )



     # --- Agendamento de Tarefas Recorrentes ---
    job_queue = application.job_queue
    # Roda de hora em hora: check_deadlines_job filtra por dentro quem tem
    # /horarionotificacao igual à hora atual (o horário não é mais único e fixo)
    job_queue.run_repeating(check_deadlines_job, interval=timedelta(hours=1), first=0, name="check_deadlines_hourly")
    # Agenda o resumo semanal para toda segunda às 08:00 da manhã
    # (days: 0-6 = domingo-sábado na convenção do python-telegram-bot v20+, então segunda = 1)
    job_queue.run_daily(send_weekly_summary_job, time=time(hour=8, minute=0), days=(1,), name="weekly_summary")
    # Reagenda lembretes personalizados que ficaram pendentes de um restart anterior
    reschedule_pending_reminders(application)


    # --- Registra os Handlers de Comando ---
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("hoje", today_command))
    application.add_handler(CommandHandler("semana", week_command))
    application.add_handler(CommandHandler("grade", list_subjects))
    application.add_handler(CommandHandler("calendario", list_activities))
    application.add_handler(CommandHandler("faltas", report_absences))
    application.add_handler(CommandHandler("exportar", export_data))
    application.add_handler(CommandHandler("exportarcalendario", export_calendar))
    application.add_handler(CommandHandler("privacidade", privacy_policy))

    # --- Registra os Handlers de Conversa ---
    application.add_handler(setup_subject_handler())
    application.add_handler(setup_management_handler())
    application.add_handler(setup_report_handler())
    application.add_handler(setup_activity_handler())
    application.add_handler(setup_activity_management_handler()) # NOVO
    application.add_handler(setup_absence_handler())
    application.add_handler(setup_absence_management_handler())
    application.add_handler(setup_grade_handler())
    application.add_handler(setup_grade_management_handler())
    application.add_handler(setup_import_handler())
    application.add_handler(setup_bug_report_handler())
    application.add_handler(setup_fatec_handler())
    application.add_handler(setup_delete_user_handler())
    application.add_handlers(setup_notifications_handler())
    application.add_handlers(setup_notification_hour_handler())
    application.add_handlers(setup_admin_handlers())
    application.add_handler(setup_reminder_handler())
    application.add_handlers(setup_reminder_list_handler())

    # --- Handlers de Callback (Botões Genéricos) ---
    application.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Iniciando o bot e o agendador de tarefas...")
    application.run_polling()


if __name__ == "__main__":
    main()