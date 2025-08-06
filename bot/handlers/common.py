import logging
from datetime import date, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.db.base import SessionLocal
from bot.services import user_service, subject_service, activity_service

# Importa as funções de listagem de outros handlers para serem chamadas pelos botões
from bot.handlers.subject_handler import list_subjects
from bot.handlers.activity_handler import list_activities
from bot.handlers.absence_handler import report_absences

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Processa o /start, mostrando mensagem de boas-vindas e o novo menu principal aprimorado."""
    telegram_user = update.effective_user
    if update.callback_query:
        telegram_user = update.callback_query.from_user

    with SessionLocal() as db:
        user, is_new = user_service.get_or_create_user(
            db=db,
            user_id=telegram_user.id,
            first_name=telegram_user.first_name,
            username=telegram_user.username
        )

    if is_new:
        logger.info("Novo usuário %s (ID: %s) iniciou o bot.", user.first_name, user.user_id)
        welcome_message = (
            f"Olá, {user.first_name}! Bem-vindo(a) ao seu novo assistente de estudos. 🚀\n\n"
            "A jornada para a excelência começa com organização, e eu estou aqui para te ajudar a trilhar o caminho rumo à aprovação!\n\n"
            "Use os botões abaixo para navegar por todas as minhas funcionalidades."
        )
    else:
        logger.info("Usuário %s (ID: %s) retornou.", user.first_name, user.user_id)
        welcome_message = f"Olá de volta, {user.first_name}! 👋\n\nO que vamos organizar hoje?"

    keyboard = [
        [
            InlineKeyboardButton("☀️ Resumo de Hoje", callback_data="summary_today"),
            InlineKeyboardButton("🗓️ Resumo da Semana", callback_data="summary_week")
        ],
        [
            InlineKeyboardButton("📚 Matérias", callback_data="menu_subjects"),
            InlineKeyboardButton("🗓️ Trabalhos e Provas", callback_data="menu_activities")
        ],
        [
            InlineKeyboardButton("✖️ Faltas", callback_data="menu_absences"),
            InlineKeyboardButton("🎓 Notas", callback_data="menu_grades")
        ],
        [InlineKeyboardButton("❓ Ajuda", callback_data="main_help")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=welcome_message, reply_markup=reply_markup, parse_mode='HTML')
    else:
        await update.message.reply_html(text=welcome_message, reply_markup=reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Processa os cliques nos botões, agindo como um roteador para os menus."""
    query = update.callback_query
    data = query.data

    if data == "main_menu":
        await start(update, context)
        return

    # --- Sub-Menus ---
    elif data == "menu_subjects":
        keyboard = [
            [InlineKeyboardButton("📖 Ver Grade Horária", callback_data="main_grade")],
            [InlineKeyboardButton("➕ Adicionar Matéria", callback_data="start_new_subject")],
            [InlineKeyboardButton("⚙️ Gerenciar Matérias", callback_data="start_manage_subjects")],
            [InlineKeyboardButton("« Voltar ao Menu Principal", callback_data="main_menu")]
        ]
        await query.edit_message_text("📚 *Matérias*\n\nO que deseja fazer?", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    elif data == "menu_activities":
        keyboard = [
            [InlineKeyboardButton("📅 Ver Calendário Completo", callback_data="main_agenda")],
            [
                InlineKeyboardButton("📝 Add Trabalho", callback_data="start_new_activity_trabalho"),
                InlineKeyboardButton("❗️ Add Prova", callback_data="start_new_activity_prova")
            ],
            [
                InlineKeyboardButton("⚙️ Gerenciar Trabalhos", callback_data="start_manage_trabalhos"),
                InlineKeyboardButton("⚙️ Gerenciar Provas", callback_data="start_manage_provas")
            ],
            [InlineKeyboardButton("« Voltar ao Menu Principal", callback_data="main_menu")]
        ]
        await query.edit_message_text("🗓️ *Trabalhos e Provas*\n\nO que deseja fazer?", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        
    elif data == "menu_absences":
        keyboard = [
            [InlineKeyboardButton("➕ Registrar Falta", callback_data="start_new_absence")],
            [InlineKeyboardButton("⚙️ Gerenciar Faltas", callback_data="start_manage_absences")],
            [InlineKeyboardButton("📊 Ver Relatório de Faltas", callback_data="report_absences_action")],
            [InlineKeyboardButton("« Voltar ao Menu Principal", callback_data="main_menu")]
        ]
        await query.edit_message_text("✖️ *Faltas*\n\nO que deseja fazer?", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    elif data == "menu_grades":
        keyboard = [
            [InlineKeyboardButton("➕ Lançar Nota", callback_data="start_new_grade")],
            # [InlineKeyboardButton("⚙️ Gerenciar Notas", callback_data="start_manage_grades")], # Descomentado quando implementado
            [InlineKeyboardButton("« Voltar ao Menu Principal", callback_data="main_menu")]
        ]
        await query.edit_message_text("🎓 *Notas*\n\nO que deseja fazer?", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    # --- Ações Diretas ---
    elif data == "summary_today":
        await today_command(update, context)
    elif data == "summary_week":
        await week_command(update, context)
    elif data == "main_grade":
        await list_subjects(update, context)
    elif data == "main_agenda":
        await list_activities(update, context)
    elif data == "report_absences_action":
        await report_absences(update, context)
    elif data == "main_help":
        await help_command(update, context)


async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Exibe um resumo do dia, respondendo a um comando ou editando uma mensagem de botão."""
    query = update.callback_query
    if query:
        await query.answer()
        telegram_user = query.from_user
    else:
        telegram_user = update.effective_user
    
    today = date.today()
    weekday_map = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    today_weekday_name = weekday_map[today.weekday()]
    message = f"☀️ *Resumo para hoje, {today.strftime('%d/%m/%Y')} ({today_weekday_name})*:\n\n"
    
    with SessionLocal() as db:
        user, _ = user_service.get_or_create_user(db, telegram_user.id, telegram_user.first_name, telegram_user.username)
        todays_subjects = subject_service.get_subjects_by_day_of_week(db, user, today_weekday_name)
        message += "📚 *Aulas de Hoje:*\n"
        if not todays_subjects:
            message += "   - Nenhuma aula hoje. Aproveite!\n"
        else:
            for subject in todays_subjects:
                start_str = subject.start_time.strftime('%H:%M') if subject.start_time else '--:--'
                end_str = subject.end_time.strftime('%H:%M') if subject.end_time else '--:--'
                message += f"   • `{start_str}`-`{end_str}`: *{subject.name}* (Sala: {subject.room})\n"
        
        message += "\n" + "—" * 20 + "\n\n"

        todays_activities = activity_service.get_activities_by_date(db, user, today)
        message += "📌 *Entregas e Provas para Hoje:*\n"
        if not todays_activities:
            message += "   - Nenhuma entrega ou prova agendada para hoje!\n"
        else:
            for activity in todays_activities:
                icon = "📝" if activity.activity_type == 'trabalho' else "❗️"
                message += f"   {icon} *{activity.name}* (Matéria: {activity.subject.name})\n"

    if query:
        await query.edit_message_text(message, parse_mode='HTML')
    else:
        await update.message.reply_html(message)


async def week_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Exibe as atividades da semana, respondendo a um comando ou editando uma mensagem de botão."""
    query = update.callback_query
    if query:
        await query.answer()
        telegram_user = query.from_user
    else:
        telegram_user = update.effective_user

    today = date.today()
    end_of_week = today + timedelta(days=6)
    message = f"🗓️ *Agenda para os próximos 7 dias (de {today.strftime('%d/%m')} a {end_of_week.strftime('%d/%m')})*:\n\n"
    
    with SessionLocal() as db:
        user, _ = user_service.get_or_create_user(db, telegram_user.id, telegram_user.first_name, telegram_user.username)
        week_activities = activity_service.get_activities_by_date_range(db, user, today, end_of_week)

        if not week_activities:
            message += "Nenhuma atividade agendada para esta semana. Que tranquilidade!"
        else:
            for activity in week_activities:
                icon = "📝" if activity.activity_type == 'trabalho' else "❗️"
                message += f" • *{activity.due_date.strftime('%d/%m (%a)')}:* {icon} {activity.name} ({activity.subject.name})\n"

    if query:
        await query.edit_message_text(message, parse_mode='HTML')
    else:
        await update.message.reply_html(message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envia uma mensagem de ajuda completa e estruturada."""
    query = update.callback_query
    if query:
        await query.answer()

    help_text = (
        "Olá! Eu sou seu assistente de estudos. Aqui está um resumo de tudo que posso fazer:\n\n"
        "💡 **Dica Principal:** A melhor forma de me usar é através do menu interativo. "
        "Basta enviar /start para acessá-lo a qualquer momento!\n\n"
        "Aqui estão os comandos diretos, organizados por categoria:\n\n"
        "— — — — — — — — — —\n\n"
        "📚 *Matérias*\n"
        "• /grade - Exibe sua grade horária completa.\n"
        "• /addmateria - Inicia o cadastro de uma nova matéria.\n"
        "• /gerenciarmaterias - Permite editar ou excluir matérias existentes.\n\n"
        
        "🗓️ *Trabalhos e Provas*\n"
        "• /calendario - Lista todos os seus trabalhos e provas.\n"
        "• /addtrabalho - Adiciona um novo trabalho na sua agenda.\n"
        "• /addprova - Adiciona uma nova prova na sua agenda.\n"
        "• /gerenciartrabalhos - Permite editar ou excluir trabalhos.\n"
        "• /gerenciarprovas - Permite editar ou excluir provas.\n\n"

        "✖️ *Faltas e 🎓 Notas*\n"
        "• /faltei - Registra uma ou mais faltas em uma matéria.\n"
        "• /gerenciarfaltas - Edita ou exclui o total de faltas de uma matéria.\n"
        "• /addnota - Lança uma nova nota para uma matéria.\n\n"
        
        "⚡ *Resumos Rápidos*\n"
        "• /hoje - Mostra um resumo das aulas e atividades do dia.\n"
        "• /semana - Lista as atividades dos próximos 7 dias.\n"
        "• /relatorio - Gera um relatório detalhado de uma matéria.\n\n"
        
        "⚙️ *Comandos Gerais*\n"
        "• /start - Inicia o bot e mostra o menu principal.\n"
        "• /help - Mostra esta mensagem de ajuda.\n"
        "• /cancelar - *(Importante!)* Interrompe qualquer operação em andamento."
    )
    
    if query:
        await query.edit_message_text(help_text, parse_mode='HTML')
    else:
        await update.message.reply_html(help_text)