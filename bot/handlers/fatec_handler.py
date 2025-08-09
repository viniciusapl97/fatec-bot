# bot/handlers/fatec_handler.py

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, filters, CallbackQueryHandler,
)

from bot.db.base import SessionLocal
from bot.services import user_service, subject_service, course_service
from bot.core import dialogs

logger = logging.getLogger(__name__)

# Estados da conversa
CHOOSE_COURSE, CHOOSE_SHIFT, CHOOSE_GRADE_TYPE, IDEAL_SEMESTER, PAGINATING_SUBJECTS, CUSTOM_IDS, CUSTOM_SEMESTER = range(7)

# Lista de cursos
COURSES = [
    "Informática para Negócios",
    "Automação Industrial",
    "Manufatura Avançada",
]

async def fatec_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia o fluxo de cadastro da Fatec, pedindo o curso."""
    keyboard = [[InlineKeyboardButton(course, callback_data=course)] for course in COURSES]
    await update.message.reply_text(dialogs.FATEC_ONBOARDING_START, reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSE_COURSE

async def received_course(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe o curso e pede o turno."""
    query = update.callback_query
    await query.answer()
    context.user_data['course'] = query.data
    
    keyboard = [[
        InlineKeyboardButton("Matutino", callback_data="Matutino"),
        InlineKeyboardButton("Noturno", callback_data="Noturno")
    ]]
    await query.edit_message_text(dialogs.FATEC_ONBOARDING_ASK_SHIFT, reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSE_SHIFT

async def received_shift(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe o turno e pergunta o tipo de grade."""
    query = update.callback_query
    await query.answer()
    context.user_data['shift'] = query.data

    keyboard = [
        [InlineKeyboardButton("Grade Ideal do Semestre", callback_data="ideal")],
        [InlineKeyboardButton("Montar Grade Personalizada", callback_data="custom")]
    ]
    await query.edit_message_text(dialogs.FATEC_ONBOARDING_ASK_GRADE_TYPE, reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSE_GRADE_TYPE


def build_subjects_page(page: int, all_subjects: list, course_info: dict):
    """Função auxiliar para montar o texto e os botões de uma página."""
    items_per_page = 5  # Quantas matérias mostrar por página
    start_index = page * items_per_page
    end_index = start_index + items_per_page
    
    paginated_subjects = all_subjects[start_index:end_index]

    message = dialogs.FATEC_ONBOARDING_CUSTOM_LIST_HEADER
    for sub in paginated_subjects:
        start = sub.start_time.strftime('%H:%M')
        end = sub.end_time.strftime('%H:%M')
        message += (
            f"<b>ID:</b> {sub.id:02}\n"
            f"<b>Matéria:</b> {sub.subject_name} ({sub.semester}º Sem.)\n"
            f"<b>Professor:</b> {sub.professor_name or 'N/A'}\n"
            f"<b>Horário:</b> {sub.day_of_week}, {start} - {end}\n"
            f"<b>Sala:</b> {sub.room or 'N/A'}\n\n"
        )
    
    total_pages = (len(all_subjects) - 1) // items_per_page
    message += f"Página {page + 1} de {total_pages + 1}\n\n"
    message += dialogs.FATEC_ONBOARDING_CUSTOM_PROMPT

    # Monta os botões de navegação
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Anterior", callback_data=f"custom_page_{page - 1}"))
    if end_index < len(all_subjects):
        nav_buttons.append(InlineKeyboardButton("Próxima ➡️", callback_data=f"custom_page_{page + 1}"))

    keyboard = [nav_buttons] if nav_buttons else []
    reply_markup = InlineKeyboardMarkup(keyboard)

    return message, reply_markup

async def received_grade_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Direciona o usuário com base na escolha (ideal vs personalizada)."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "ideal":
        keyboard = [[InlineKeyboardButton(f"{i}º Semestre", callback_data=str(i))] for i in range(1, 7)]
        await query.edit_message_text(dialogs.FATEC_ONBOARDING_ASK_IDEAL_SEMESTER, reply_markup=InlineKeyboardMarkup(keyboard))
        return IDEAL_SEMESTER
        
    elif query.data == "custom":
        course = context.user_data['course']
        shift = context.user_data['shift']
        
        with SessionLocal() as db:
            all_subjects = course_service.get_all_subjects_for_course(db, course, shift)

        if not all_subjects:
            await query.edit_message_text(dialogs.FATEC_ONBOARDING_NO_CATALOG)
            return ConversationHandler.END

        # Salva a lista completa para uso futuro
        context.user_data['all_subjects_list'] = all_subjects
        
        # Monta e exibe a primeira página (página 0)
        message, reply_markup = build_subjects_page(page=0, all_subjects=all_subjects, course_info=context.user_data)
        
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')
        return PAGINATING_SUBJECTS
    
async def custom_grade_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Navega entre as páginas da lista de matérias."""
    query = update.callback_query
    await query.answer()
    
    page = int(query.data.split('_')[-1])
    all_subjects = context.user_data.get('all_subjects_list', [])
    
    if not all_subjects:
        await query.edit_message_text("Ocorreu um erro ao carregar a lista de matérias. Por favor, comece de novo com /fatec.")
        return ConversationHandler.END

    message, reply_markup = build_subjects_page(page=page, all_subjects=all_subjects, course_info=context.user_data)
    
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')
    return PAGINATING_SUBJECTS    


async def register_ideal_grade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cadastra a grade ideal para o semestre escolhido."""
    query = update.callback_query
    await query.answer()
    
    semester = int(query.data)
    data = context.user_data
    telegram_user = query.from_user

    with SessionLocal() as db:
        user, _ = user_service.get_or_create_user(db, telegram_user.id, telegram_user.first_name, telegram_user.username)
        ideal_subjects = course_service.get_ideal_grade_subjects(db, data['course'], data['shift'], semester)
        
        if not ideal_subjects:
            await query.edit_message_text(dialogs.FATEC_ONBOARDING_NO_IDEAL_GRADE.format(semester=semester))
            context.user_data.clear()
            return ConversationHandler.END
            
        count = subject_service.bulk_create_from_course_subjects(db, user, ideal_subjects)
    
    await query.edit_message_text(dialogs.FATEC_ONBOARDING_IDEAL_SUCCESS.format(count=count, semester=semester))
    context.user_data.clear()
    return ConversationHandler.END

async def received_custom_ids(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe os IDs, verifica conflitos e pede o semestre."""
    try:
        ids_str = update.message.text.replace(',', ' ').split()
        selected_ids = [int(id_str) for id_str in ids_str]
        if not selected_ids: raise ValueError
    except (ValueError, TypeError):
        await update.message.reply_text(dialogs.FATEC_ONBOARDING_INVALID_IDS)
        return CUSTOM_IDS

    with SessionLocal() as db:
        selected_subjects = course_service.get_subjects_by_ids(db, selected_ids)
        conflict_error = course_service.check_schedule_conflict(selected_subjects)

    if conflict_error:
        await update.message.reply_text(dialogs.FATEC_ONBOARDING_CONFLICT_ERROR.format(error=conflict_error))
        return CUSTOM_IDS
    
    context.user_data['selected_ids'] = [s.id for s in selected_subjects]
    await update.message.reply_text(dialogs.FATEC_ONBOARDING_NO_CONFLICT_ASK_SEMESTER)
    return CUSTOM_SEMESTER

async def register_custom_grade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe o semestre opcional e cadastra a grade personalizada."""
    semester_text = update.message.text
    semester = None
    if semester_text.lower() not in ['pular', 'nao', 'não']:
        try:
            semester = int(semester_text)
        except (ValueError, TypeError):
            await update.message.reply_text(dialogs.FATEC_ONBOARDING_INVALID_SEMESTER)
            
    await update.message.reply_text(dialogs.FATEC_ONBOARDING_FINALIZING_CUSTOM)
    
    selected_ids = context.user_data['selected_ids']
    telegram_user = update.effective_user

    with SessionLocal() as db:
        user, _ = user_service.get_or_create_user(db, telegram_user.id, telegram_user.first_name, telegram_user.username)
        subjects_to_create = course_service.get_subjects_by_ids(db, selected_ids)
        count = subject_service.bulk_create_from_course_subjects(db, user, subjects_to_create, semester_override=semester)

    await update.message.reply_text(dialogs.FATEC_ONBOARDING_CUSTOM_SUCCESS.format(count=count))
    context.user_data.clear()
    return ConversationHandler.END

# CORREÇÃO: A função de cancelamento foi movida para ANTES da função de setup
async def fatec_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela o fluxo de onboarding da Fatec."""
    if update.callback_query:
        await update.callback_query.edit_message_text(text=dialogs.OPERATION_CANCELED)
    else:
        await update.message.reply_text(text=dialogs.OPERATION_CANCELED)
    
    context.user_data.clear()
    return ConversationHandler.END

def setup_fatec_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("fatec", fatec_start)],
        states={
            CHOOSE_COURSE: [CallbackQueryHandler(received_course)],
            CHOOSE_SHIFT: [CallbackQueryHandler(received_shift)],
            CHOOSE_GRADE_TYPE: [CallbackQueryHandler(received_grade_type)],
            IDEAL_SEMESTER: [CallbackQueryHandler(register_ideal_grade, pattern=r"^[1-6]$")],
            PAGINATING_SUBJECTS: [
                CallbackQueryHandler(custom_grade_page_callback, pattern=r"^custom_page_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, received_custom_ids)
            ],
            CUSTOM_IDS: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_custom_ids)],
            CUSTOM_SEMESTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_custom_grade)],
        },
        fallbacks=[CommandHandler("cancelar", fatec_cancel)], # Use a função correta de cancelamento
    )