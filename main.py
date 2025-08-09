# main.py

import logging
from telegram import BotCommand
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
)
from datetime import time

from bot.core.settings import TELEGRAM_TOKEN
from bot.db.base import Base, engine
from bot.db import models

# Importa todas as funções e setups de handlers
from bot.handlers.common import start, help_command, button_handler, today_command, week_command
from bot.handlers.reminder_handler import setup_reminder_handler
from bot.handlers.subject_handler import list_subjects, setup_subject_handler, setup_management_handler, setup_report_handler
from bot.handlers.activity_handler import list_activities, setup_activity_handler, setup_activity_management_handler
from bot.handlers.absence_handler import setup_absence_handler, setup_absence_management_handler, report_absences
from bot.handlers.grade_handler import setup_grade_handler, setup_grade_management_handler
from bot.handlers.import_handler import setup_import_handler
from bot.handlers.bug_report_handler import setup_bug_report_handler
from bot.handlers.fatec_handler import setup_fatec_handler
from bot.handlers.user_settings_handler import setup_delete_user_handler
from bot.handlers.admin_handler import setup_admin_handlers
from bot.jobs import check_deadlines_job


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
        BotCommand("lembrar", "Cria um lembrete personalizado"),
    ]
    await application.bot.set_my_commands(commands)


def main() -> None:
    """Inicia o bot e o mantém rodando."""

    logger.info("Criando/Verificando tabelas no banco de dados...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tabelas verificadas/criadas com sucesso.")

    application = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(post_init_configuration).build()



     # --- Agendamento de Tarefas Recorrentes ---
    job_queue = application.job_queue
    # Agenda a tarefa para rodar todo dia às 09:00 da manhã
    job_queue.run_daily(check_deadlines_job, time=time(hour=9, minute=0), name="check_deadlines_daily")
    
    
    # --- Registra os Handlers de Comando ---
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("hoje", today_command))
    application.add_handler(CommandHandler("semana", week_command))
    application.add_handler(CommandHandler("grade", list_subjects))
    application.add_handler(CommandHandler("calendario", list_activities))
    application.add_handler(CommandHandler("faltas", report_absences))
    
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
    application.add_handlers(setup_admin_handlers())
    application.add_handler(setup_reminder_handler())
    
    # --- Handlers de Callback (Botões Genéricos) ---
    application.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Iniciando o bot e o agendador de tarefas...")
    application.run_polling()


if __name__ == "__main__":
    main()