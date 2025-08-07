import logging
from collections import defaultdict
from datetime import time, datetime
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)

from bot.db.base import SessionLocal
from bot.services import user_service, subject_service, grade_service, activity_service
from bot.core import dialogs

logger = logging.getLogger(__name__)

# Estados para CRIAÇÃO
NAME, PROFESSOR, DAY, ROOM, START_TIME, END_TIME, SEMESTER = range(7)
# Estados para GERENCIAMENTO
SELECTING_ACTION, CONFIRMING_DELETE, SHOWING_EDIT_OPTIONS, AWAITING_NEW_VALUE = range(10, 14)
# Estado para RELATÓRIO
SELECT_SUBJECT_FOR_REPORT = 20


# =============================================================================
# Seção 1: Handler de Conversa para /addmateria (Criação)
# =============================================================================

async def new_subject_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = dialogs.SUBJECT_CREATE_ASK_NAME
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(text)
    else:
        await update.message.reply_text(text)
    return NAME

async def received_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["subject_name"] = update.message.text
    text = dialogs.SUBJECT_CREATE_ASK_PROFESSOR.format(subject_name=context.user_data["subject_name"])
    await update.message.reply_html(text)
    return PROFESSOR

async def received_professor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["professor_name"] = update.message.text
    kb = [["Segunda", "Terça", "Quarta"], ["Quinta", "Sexta", "Sábado"]]
    await update.message.reply_text(dialogs.SUBJECT_CREATE_ASK_DAY, reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True))
    return DAY

async def received_day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["day_of_week"] = update.message.text
    await update.message.reply_text(dialogs.SUBJECT_CREATE_ASK_ROOM, reply_markup=ReplyKeyboardRemove())
    return ROOM

async def received_room(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["room"] = update.message.text
    await update.message.reply_html(dialogs.SUBJECT_CREATE_ASK_START_TIME)
    return START_TIME

async def received_start_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data["start_time"] = datetime.strptime(update.message.text, "%H:%M").time()
    except ValueError:
        await update.message.reply_html(dialogs.ERROR_INVALID_TIME)
        return START_TIME
    await update.message.reply_html(dialogs.SUBJECT_CREATE_ASK_END_TIME)
    return END_TIME

async def received_end_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data["end_time"] = datetime.strptime(update.message.text, "%H:%M").time()
    except ValueError:
        await update.message.reply_html(dialogs.ERROR_INVALID_TIME)
        return END_TIME
    await update.message.reply_text(dialogs.SUBJECT_CREATE_ASK_SEMESTER)
    return SEMESTER

async def received_semester(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data["semestre"] = int(update.message.text)
    except ValueError:
        await update.message.reply_text(dialogs.ERROR_INVALID_SEMESTER)
        return SEMESTER

    data = context.user_data
    telegram_user = update.effective_user
    with SessionLocal() as db:
        user, _ = user_service.get_or_create_user(
            db, telegram_user.id, telegram_user.first_name, telegram_user.username
        )
        subject_service.create_subject(
            db=db, user=user, name=data["subject_name"], professor=data["professor_name"],
            day=data["day_of_week"], room=data["room"], start_time=data["start_time"],
            end_time=data["end_time"], semestre=data["semestre"],
        )
    await update.message.reply_html(dialogs.SUBJECT_CREATE_SUCCESS.format(subject_name=data["subject_name"]))
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(dialogs.OPERATION_CANCELED, reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END


# =============================================================================
# Seção 2: Handler de Comando para /grade (Leitura)
# =============================================================================

async def list_subjects(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lista as matérias com a nova formatação de grade aprimorada."""
    query = update.callback_query
    if query:
        await query.answer()
        telegram_user = query.from_user
    else:
        telegram_user = update.effective_user

    message = ""
    with SessionLocal() as db:
        user, _ = user_service.get_or_create_user(
            db, telegram_user.id, telegram_user.first_name, telegram_user.username
        )
        subjects = subject_service.get_subjects_by_user(db, user)

        if not subjects:
            message = dialogs.SUBJECT_LIST_NO_SUBJECTS
        else:
            days = defaultdict(list)
            for s in subjects:
                days[s.day_of_week].append(s)
            
            message = dialogs.SUBJECT_LIST_HEADER
            weekdays = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"]
            
            for d in weekdays:
                day_subjects = days.get(d, [])
                if day_subjects:
                    message += dialogs.SUBJECT_LIST_DAY_HEADER.format(day=d.upper())
                    for s in day_subjects:
                        message += dialogs.SUBJECT_LIST_ITEM.format(
                            st=s.start_time.strftime('%H:%M') if s.start_time else '--:--',
                            et=s.end_time.strftime('%H:%M') if s.end_time else '--:--',
                            name=s.name,
                            professor=s.professor,
                            room=s.room
                        )
                        
                        grades = grade_service.get_grades_by_subject(db, s)
                        if grades:
                            gl = ", ".join(f"<b>{g.name}</b>: {g.value:.2f}" for g in grades)
                            message += dialogs.SUBJECT_LIST_GRADES_LINE.format(grades=gl)
                        
                        if s.total_absences > 0:
                            message += dialogs.SUBJECT_LIST_ABSENCES_LINE.format(absences=s.total_absences)
                        
                        # Adiciona um pequeno espaço entre as matérias de um mesmo dia
                        message += "\n"

                    # Adiciona o separador no final de cada dia com aulas
                    message += dialogs.SEPARATOR
    
    if query:
        await query.edit_message_text(message, parse_mode='HTML')
    else:
        await update.message.reply_html(message)

# =============================================================================
# Seção 3: Handler de Conversa para /gerenciarmaterias
# =============================================================================

async def manage_subjects_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query:
        await query.answer()
        telegram_user = query.from_user
    else:
        telegram_user = update.effective_user

    with SessionLocal() as db:
        user, _ = user_service.get_or_create_user(db, telegram_user.id, telegram_user.first_name, telegram_user.username)
        subjects = subject_service.get_subjects_by_user(db, user)

    if not subjects:
        text = dialogs.SUBJECT_MANAGE_NO_SUBJECTS
        if query: await query.edit_message_text(text=text)
        else: await update.message.reply_text(text)
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(s.name, callback_data=f"manage_{s.id}")] for s in subjects]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = dialogs.SUBJECT_MANAGE_PROMPT

    if query: await query.edit_message_text(text, reply_markup=reply_markup)
    else: await update.message.reply_text(text, reply_markup=reply_markup)
        
    return SELECTING_ACTION

async def select_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    subject_id = int(query.data.split('_')[1])
    context.user_data['subject_id_to_manage'] = subject_id
    
    with SessionLocal() as db:
        subject = subject_service.get_subject_by_id(db, subject_id)

    keyboard = [
        [InlineKeyboardButton("Editar ✏️", callback_data=f"edit_{subject_id}")],
        [InlineKeyboardButton("Excluir 🗑️", callback_data=f"delete_{subject_id}")],
        [InlineKeyboardButton("« Voltar para a lista", callback_data="back_to_list")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(dialogs.SUBJECT_MANAGE_ACTION_PROMPT.format(subject_name=subject.name), reply_markup=reply_markup, parse_mode='HTML')
    return SELECTING_ACTION

async def show_edit_options_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    subject_id = context.user_data.get('subject_id_to_manage')
    if not subject_id:
        subject_id = int(query.data.split('_')[1])
        context.user_data['subject_id_to_manage'] = subject_id

    with SessionLocal() as db:
        subject = subject_service.get_subject_by_id(db, subject_id)

    if not subject:
        await query.edit_message_text(dialogs.ERROR_NOT_FOUND)
        return ConversationHandler.END
    
    start_str = subject.start_time.strftime('%H:%M') if subject.start_time else 'N/A'
    end_str = subject.end_time.strftime('%H:%M') if subject.end_time else 'N/A'
    
    text = dialogs.SUBJECT_EDIT_HEADER.format(
        subject_name=subject.name, professor=subject.professor,
        day_of_week=subject.day_of_week, start_str=start_str, end_str=end_str,
        room=subject.room, semestre=(subject.semestre or 'N/A')
    )
    # A sua implementação pessoal de edição de horários e formatação irá aqui!
    # Por enquanto, vou omitir os botões de horário para não causar erros.
    keyboard = [
        [
            InlineKeyboardButton("Nome", callback_data="editfield_name"),
            InlineKeyboardButton("Professor", callback_data="editfield_professor"),
        ],
        [
            InlineKeyboardButton("Dia da Semana", callback_data="editfield_day_of_week"),
            InlineKeyboardButton("Sala", callback_data="editfield_room"),
            InlineKeyboardButton("Semestre", callback_data="editfield_semestre"),
        ],
        [InlineKeyboardButton("« Voltar", callback_data=f"manage_{subject_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    return SHOWING_EDIT_OPTIONS

async def select_field_to_edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    # A CORREÇÃO ESTÁ AQUI
    field_to_edit = query.data.split('_', 1)[1]
    context.user_data['field_to_edit'] = field_to_edit

    field_map = {
        'name': 'nome', 'professor': 'nome do professor', 'room': 'sala',
        'start_time': 'horário de início (HH:MM)', 'end_time': 'horário de término (HH:MM)',
        'semestre': 'semestre'
    }

    # Agora, com o field_to_edit correto ('day_of_week'), este bloco será executado
    if field_to_edit == "day_of_week":
        keyboard = [["Segunda", "Terça", "Quarta"], ["Quinta", "Sexta", "Sábado"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await query.message.reply_text(dialogs.SUBJECT_EDIT_DAY_KEYBOARD, reply_markup=reply_markup)
    else:
        await query.message.reply_html(dialogs.SUBJECT_EDIT_ASK_NEW_VALUE.format(field_name=field_map[field_to_edit]))

    return AWAITING_NEW_VALUE
async def receive_field_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    new_value = update.message.text
    field_to_edit = context.user_data.get('field_to_edit')
    subject_id = context.user_data.get('subject_id_to_manage')

    # Valida e converte o novo valor
    try:
        if field_to_edit in ['start_time', 'end_time']:
            new_value = datetime.strptime(new_value, "%H:%M").time()
        elif field_to_edit == 'semestre':
            new_value = int(new_value)
    except ValueError:
        error_message = dialogs.ERROR_INVALID_TIME if 'time' in field_to_edit else dialogs.ERROR_INVALID_SEMESTER
        await update.message.reply_html(error_message)
        return AWAITING_NEW_VALUE

    with SessionLocal() as db:
        subject_service.update_subject(db, subject_id, {field_to_edit: new_value})
        # Busca a matéria novamente para pegar os dados atualizados
        subject = subject_service.get_subject_by_id(db, subject_id)

    await update.message.reply_text(dialogs.SUBJECT_EDIT_SUCCESS, reply_markup=ReplyKeyboardRemove())

    # --- LÓGICA DE RECARREGAMENTO (SEM 'fake_update') ---
    # Simplesmente recria e reenvia o menu de edição
    
    start_str = subject.start_time.strftime('%H:%M') if subject.start_time else 'N/A'
    end_str = subject.end_time.strftime('%H:%M') if subject.end_time else 'N/A'
    
    text = dialogs.SUBJECT_EDIT_HEADER.format(
        subject_name=subject.name, professor=subject.professor,
        day_of_week=subject.day_of_week, start_str=start_str, end_str=end_str,
        room=subject.room, semestre=(subject.semestre or 'N/A')
    )
    keyboard = [
        [
            InlineKeyboardButton("Nome", callback_data="editfield_name"),
            InlineKeyboardButton("Professor", callback_data="editfield_professor"),
        ],
        # Adicione os botões de horário aqui quando implementar a sua parte
        [
            InlineKeyboardButton("Dia da Semana", callback_data="editfield_day_of_week"),
            InlineKeyboardButton("Sala", callback_data="editfield_room"),
            InlineKeyboardButton("Semestre", callback_data="editfield_semestre"),
        ],
        [InlineKeyboardButton("« Voltar", callback_data=f"manage_{subject_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Envia o menu de edição atualizado como uma nova mensagem
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    return SHOWING_EDIT_OPTIONS
async def handle_delete_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    subject_id = int(query.data.split('_')[-1])
    with SessionLocal() as db:
        subject = subject_service.get_subject_by_id(db, subject_id)
    
    keyboard = [[
        InlineKeyboardButton("✅ Sim, tenho certeza", callback_data=f"confirmdelete_{subject_id}"),
        InlineKeyboardButton("❌ Não, cancelar", callback_data=f"manage_{subject_id}")
    ]]
    await query.edit_message_text(dialogs.SUBJECT_DELETE_CONFIRM.format(subject_name=subject.name), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    return CONFIRMING_DELETE

async def confirm_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    subject_id = int(query.data.split('_')[-1])
    with SessionLocal() as db:
        subject = subject_service.get_subject_by_id(db, subject_id)
        subject_name = subject.name
        deleted = subject_service.delete_subject_by_id(db, subject_id)
    
    if deleted:
        await query.edit_message_text(dialogs.SUBJECT_DELETE_SUCCESS.format(subject_name=subject_name), parse_mode='HTML')
    else:
        await query.edit_message_text(dialogs.ERROR_SUBJECT_NOT_FOUND) # Usando um erro genérico
        
    context.user_data.clear()
    return ConversationHandler.END

async def back_to_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    # Chama a função de início, que agora é context-aware
    return await manage_subjects_start(update, context)

async def manage_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(dialogs.OPERATION_CANCELED, reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END


# =============================================================================
# Seção 4: Handler de Conversa para /relatorio
# =============================================================================

async def report_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    telegram_user = update.effective_user
    with SessionLocal() as db:
        user, _ = user_service.get_or_create_user(db, telegram_user.id, telegram_user.first_name, telegram_user.username)
        subjects = subject_service.get_subjects_by_user(db, user)

    if not subjects:
        await update.message.reply_text(dialogs.REPORT_NO_SUBJECTS)
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(s.name, callback_data=f"report_subject_{s.id}")] for s in subjects]
    await update.message.reply_text(dialogs.REPORT_PROMPT, reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_SUBJECT_FOR_REPORT

async def show_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    subject_id = int(query.data.split('_')[-1])

    with SessionLocal() as db:
        subject = subject_service.get_subject_by_id(db, subject_id)
        if not subject:
            await query.edit_message_text(dialogs.REPORT_NOT_FOUND)
            return ConversationHandler.END
        
        activities = activity_service.get_activities_by_subject(db, subject)
        grades = grade_service.get_grades_by_subject(db, subject)

    start_str = subject.start_time.strftime('%H:%M') if subject.start_time else 'N/A'
    end_str = subject.end_time.strftime('%H:%M') if subject.end_time else 'N/A'
    
    report_text = dialogs.REPORT_HEADER.format(subject_name=subject.name)
    report_text += dialogs.REPORT_SUBJECT_DETAILS.format(
        semestre=(subject.semestre or 'N/A'), professor=subject.professor,
        day_of_week=subject.day_of_week, start_str=start_str, end_str=end_str,
        room=subject.room, total_absences=subject.total_absences
    )
    report_text += "\n" + dialogs.SEPARATOR + "\n"

    report_text += dialogs.REPORT_ACTIVITIES_HEADER
    if not activities:
        report_text += dialogs.REPORT_NO_ACTIVITIES
    else:
        for act in activities:
            report_text += dialogs.REPORT_ACTIVITY_ITEM.format(due_date=act.due_date.strftime('%d/%m/%Y'), activity_name=act.name)
    report_text += "\n" + dialogs.SEPARATOR + "\n"
    
    report_text += dialogs.REPORT_GRADES_HEADER
    if not grades:
        report_text += dialogs.REPORT_NO_GRADES
    else:
        for grade in grades:
            report_text += dialogs.REPORT_GRADE_ITEM.format(grade_name=grade.name, grade_value=f"{grade.value:.2f}")

    await query.edit_message_text(report_text, parse_mode='HTML')
    return ConversationHandler.END


# =============================================================================
# Seção 5: Funções de Setup que Montam os Handlers
# =============================================================================

def setup_subject_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("addmateria", new_subject_start),
            CallbackQueryHandler(new_subject_start, pattern="^start_new_subject$")
        ],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_name)],
            PROFESSOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_professor)],
            DAY: [MessageHandler(filters.Regex("^(Segunda|Terça|Quarta|Quinta|Sexta|Sábado)$"), received_day)],
            ROOM: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_room)],
            START_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_start_time)],
            END_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_end_time)],
            SEMESTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_semester)],
        },
        fallbacks=[CommandHandler("cancelar", cancel)],
        per_message=False,
    )

def setup_management_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("gerenciarmaterias", manage_subjects_start),
            CallbackQueryHandler(manage_subjects_start, pattern="^start_manage_subjects$")
        ],
        states={
            SELECTING_ACTION: [
                CallbackQueryHandler(select_action_callback, pattern="^manage_"),
                CallbackQueryHandler(show_edit_options_callback, pattern="^edit_"),
                CallbackQueryHandler(handle_delete_confirmation, pattern="^delete_"),
                CallbackQueryHandler(back_to_list_callback, pattern="^back_to_list$")
            ],
            SHOWING_EDIT_OPTIONS: [
                CallbackQueryHandler(select_field_to_edit_callback, pattern="^editfield_"),
                CallbackQueryHandler(select_action_callback, pattern="^manage_"),
            ],
            AWAITING_NEW_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_field_update)
            ],
            CONFIRMING_DELETE: [
                CallbackQueryHandler(confirm_delete_callback, pattern="^confirmdelete_"),
                CallbackQueryHandler(select_action_callback, pattern="^manage_")
            ],
        },
        fallbacks=[CommandHandler("cancelar", manage_cancel)],
        per_message=False,
    )

def setup_report_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("relatorio", report_start)],
        states={
            SELECT_SUBJECT_FOR_REPORT: [CallbackQueryHandler(show_report, pattern="^report_subject_")]
        },
        fallbacks=[CommandHandler("cancelar", cancel)],
        per_message=False,
    )