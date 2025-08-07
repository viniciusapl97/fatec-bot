
import logging
from datetime import date, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.db.base import SessionLocal
from bot.services import user_service, subject_service, activity_service

# Importa as funções de outros handlers
from bot.handlers.subject_handler import list_subjects
from bot.handlers.activity_handler import list_activities
from bot.handlers.absence_handler import report_absences

# SUGESTÃO DE MELHORIA: Importa o módulo inteiro
from bot.core import dialogs

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Processa o /start, mostrando mensagem de boas-vindas e o menu principal."""
    telegram_user = update.callback_query.from_user if update.callback_query else update.effective_user

    with SessionLocal() as db:
        user, is_new = user_service.get_or_create_user(
            db=db,
            user_id=telegram_user.id,
            first_name=telegram_user.first_name,
            username=telegram_user.username,
        )

    if is_new:
        logger.info("Novo usuário %s (ID: %s) iniciou o bot.", user.first_name, user.user_id)
        welcome_message = dialogs.WELCOME_NEW.format(first_name=user.first_name)
    else:
        logger.info("Usuário %s (ID: %s) retornou.", user.first_name, user.user_id)
        welcome_message = dialogs.WELCOME_BACK.format(first_name=user.first_name)

    keyboard = [
        [
            InlineKeyboardButton("☀️ Resumo de Hoje", callback_data="summary_today"),
            InlineKeyboardButton("🗓️ Resumo da Semana", callback_data="summary_week"),
        ],
        [
            InlineKeyboardButton("📚 Matérias", callback_data="menu_subjects"),
            InlineKeyboardButton("🗓️ Trabalhos e Provas", callback_data="menu_activities"),
        ],
        [
            InlineKeyboardButton("✖️ Faltas", callback_data="menu_absences"),
            InlineKeyboardButton("🎓 Notas", callback_data="menu_grades"),
        ],
        [InlineKeyboardButton("❓ Ajuda", callback_data="main_help")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=welcome_message,
            reply_markup=reply_markup,
            parse_mode="HTML",
        )
    else:
        await update.message.reply_html(text=welcome_message, reply_markup=reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Roteia os cliques dos botões principais."""
    query = update.callback_query
    
    await query.answer()
    data = query.data

    if data == "main_menu":
        # A função start já é context-aware e vai editar a mensagem
        return await start(update, context)

    # --- Sub-Menus ---
    if data == "menu_subjects":
        keyboard = [
            [InlineKeyboardButton("📖 Ver Grade Horária", callback_data="main_grade")],
            [InlineKeyboardButton("➕ Adicionar Matéria", callback_data="start_new_subject")],
            [InlineKeyboardButton("⚙️ Gerenciar Matérias", callback_data="start_manage_subjects")],
            [InlineKeyboardButton(dialogs.BACK_TO_MAIN_MENU_PROMPT, callback_data="main_menu")],
        ]
        await query.edit_message_text(dialogs.MENU_SUBJECTS, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    elif data == "menu_activities":
        keyboard = [
            [InlineKeyboardButton("📅 Ver Calendário Completo", callback_data="main_agenda")],
            [
                InlineKeyboardButton("📝 Add Trabalho", callback_data="start_new_activity_trabalho"),
                InlineKeyboardButton("❗️ Add Prova", callback_data="start_new_activity_prova"),
            ],
            [
                InlineKeyboardButton("⚙️ Gerenciar Trabalhos", callback_data="start_manage_trabalhos"),
                InlineKeyboardButton("⚙️ Gerenciar Provas", callback_data="start_manage_provas"),
            ],
            [InlineKeyboardButton(dialogs.BACK_TO_MAIN_MENU_PROMPT, callback_data="main_menu")],
        ]
        await query.edit_message_text(dialogs.MENU_ACTIVITIES, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        
    elif data == "menu_absences":
            # A MENSAGEM AGORA INCLUI A INSTRUÇÃO PARA O COMANDO
            message = (
                "✖️ <b>Faltas</b>\n\n"
                "Use os botões para ações rápidas.\n"
                "Para editar ou excluir registros, envie o comando /gerenciarfaltas."
            )
            keyboard = [
                [InlineKeyboardButton("➕ Registrar Falta", callback_data="start_new_absence")],
                [InlineKeyboardButton("📊 Ver Relatório de Faltas", callback_data="report_absences_action")],
                [InlineKeyboardButton(dialogs.BACK_TO_MAIN_MENU_PROMPT, callback_data="main_menu")]
            ]
            await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        
    elif data == "menu_grades":
        keyboard = [
            [InlineKeyboardButton("➕ Lançar Nota", callback_data="start_new_grade")],
            [InlineKeyboardButton("⚙️ Gerenciar Notas", callback_data="start_manage_grades")],
            [InlineKeyboardButton(dialogs.BACK_TO_MAIN_MENU_PROMPT, callback_data="main_menu")],
        ]
        await query.edit_message_text(dialogs.MENU_GRADES, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    
    # --- Ações Diretas ---
    elif data == "summary_today":
        return await today_command(update, context)
    elif data == "summary_week":
        return await week_command(update, context)
    elif data == "main_grade":
        return await list_subjects(update, context)
    elif data == "main_agenda":
        return await list_activities(update, context)
    elif data == "report_absences_action":
        return await report_absences(update, context)
    elif data == "main_help":
        return await help_command(update, context)

async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Exibe um resumo do dia, usando o arquivo de diálogos."""
    query = update.callback_query
    if query:
        await query.answer()
        telegram_user = query.from_user
    else:
        telegram_user = update.effective_user

    today = date.today()
    weekday_map = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    today_weekday_name = weekday_map[today.weekday()]

    message = dialogs.SUMMARY_TODAY_HEADER.format(date=today.strftime('%d/%m/%Y'), weekday=today_weekday_name)
    
    with SessionLocal() as db:
        user, _ = user_service.get_or_create_user(db, telegram_user.id, telegram_user.first_name, telegram_user.username)
        
        subjects = subject_service.get_subjects_by_day_of_week(db, user, today_weekday_name)
        message += dialogs.TODAY_COURSES_HEADER
        if not subjects:
            message += dialogs.TODAY_NO_COURSES
        else:
            for s in subjects:
                message += dialogs.TODAY_COURSE_LINE.format(
                    start=s.start_time.strftime('%H:%M') if s.start_time else '--:--',
                    end=s.end_time.strftime('%H:%M') if s.end_time else '--:--',
                    name=s.name, room=s.room
                )
        
        message += "\n" + dialogs.SEPARATOR + "\n\n"

        activities = activity_service.get_activities_by_date(db, user, today)
        message += dialogs.ACTIVITIES_FOR_TODAY_HEADER
        if not activities:
            message += dialogs.NO_ACTIVITIES_TODAY
        else:
            for act in activities:
                icon = "📝" if act.activity_type == "trabalho" else "❗️"
                message += dialogs.TODAY_ACTIVITY_LINE.format(icon=icon, name=act.name, subject_name=act.subject.name)

    if query:
        await query.edit_message_text(message, parse_mode="HTML")
    else:
        await update.message.reply_html(message)


async def week_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Exibe as atividades da semana, usando o arquivo de diálogos."""
    query = update.callback_query
    if query:
        await query.answer()
        telegram_user = query.from_user
    else:
        telegram_user = update.effective_user

    today = date.today()
    end_of_week = today + timedelta(days=6)
    message = dialogs.AGENDA_WEEK_HEADER.format(start=today.strftime('%d/%m'), end=end_of_week.strftime('%d/%m'))
    
    with SessionLocal() as db:
        user, _ = user_service.get_or_create_user(db, telegram_user.id, telegram_user.first_name, telegram_user.username)
        week_activities = activity_service.get_activities_by_date_range(db, user, today, end_of_week)

        if not week_activities:
            message += dialogs.NO_ACTIVITIES_WEEK
        else:
            for act in week_activities:
                icon = "📝" if act.activity_type == "trabalho" else "❗️"
                date_str = act.due_date.strftime("%d/%m (%a)")
                message += dialogs.WEEK_ACTIVITY_LINE.format(date_str=date_str, icon=icon, name=act.name, subject_name=act.subject.name)

    if query:
        await query.edit_message_text(message, parse_mode="HTML")
    else:
        await update.message.reply_html(message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mostra a mensagem de ajuda completa."""
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(dialogs.HELP_TEXT, parse_mode="HTML")
    else:
        await update.message.reply_html(dialogs.HELP_TEXT)