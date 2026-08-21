import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    TypeHandler,
)

from bot.db.base import SessionLocal
from bot.services import user_service, subject_service, activity_service
from bot.core import dialogs
from bot.core.conversation_timeout import CONVERSATION_TIMEOUT_SECONDS, notify_conversation_timeout

logger = logging.getLogger(__name__)

# Estados para a conversa de CRIAÇÃO
A_NAME, A_SUBJECT, A_DUEDATE, A_NOTES = range(20, 24)

# Estados para a conversa de GERENCIAMENTO
SELECT_ACTIVITY_ACTION, CONFIRM_ACTIVITY_DELETE, SHOWING_ACTIVITY_EDIT_OPTIONS, AWAITING_ACTIVITY_NEW_VALUE = range(30, 34)

# =============================================================================
# Seção 1: Handler de Conversa para /addtrabalho e /addprova
# =============================================================================

async def new_activity_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Função de entrada genérica que funciona com comandos e botões."""
    query = update.callback_query
    activity_type = ""

    if query:
        await query.answer()
        data = query.data
        activity_type = "trabalho" if "trabalho" in data else "prova"
    else:
        command = update.message.text.split(' ')[0][1:]
        activity_type = "trabalho" if command == "addtrabalho" else "prova"
    
    context.user_data['activity_type'] = activity_type
    text = dialogs.ACTIVITY_CREATE_PROMPT.format(activity_type=activity_type)
    
    if query:
        await query.message.reply_text(text, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, parse_mode='Markdown')
        
    return A_NAME

async def received_activity_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["activity_name"] = update.message.text
    telegram_user = update.effective_user
    with SessionLocal() as db:
        user, _ = user_service.get_or_create_user(db, telegram_user.id, telegram_user.first_name, telegram_user.username)
        subjects = subject_service.get_subjects_by_user(db, user)

    if not subjects:
        await update.message.reply_text(dialogs.ACTIVITY_CREATE_NO_SUBJECTS)
        context.user_data.clear()
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(s.name, callback_data=f"link_subject_{s.id}")] for s in subjects]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(dialogs.ACTIVITY_CREATE_ASK_SUBJECT, reply_markup=reply_markup)
    return A_SUBJECT

async def received_activity_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    subject_id = int(query.data.split('_')[2])
    context.user_data["subject_id"] = subject_id
    with SessionLocal() as db:
        subject = subject_service.get_subject_by_id(db, subject_id)
    await query.edit_message_text(
        dialogs.ACTIVITY_CREATE_CONFIRM_SUBJECT_ASK_DATE.format(subject_name=subject.name),
        parse_mode="HTML"
    )
    return A_DUEDATE

async def received_activity_due_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    date_str = update.message.text
    try:
        due_date_obj = datetime.strptime(date_str, "%d/%m/%Y").date()
        context.user_data["due_date"] = due_date_obj
    except ValueError:
        await update.message.reply_text(dialogs.ERROR_INVALID_DATE, parse_mode="HTML")
        return A_DUEDATE
    await update.message.reply_text(dialogs.ACTIVITY_CREATE_ASK_NOTES)
    return A_NOTES

async def received_activity_notes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    notes = update.message.text
    if notes.lower() in ['não', 'nao', 'n', 'pular']:
        notes = None

    data = context.user_data
    telegram_user = update.effective_user
    with SessionLocal() as db:
        user, _ = user_service.get_or_create_user(db, telegram_user.id, telegram_user.first_name, telegram_user.username)
        subject = subject_service.get_subject_by_id(db, data["subject_id"])
        activity_service.create_activity(
            db=db, user=user, subject=subject, name=data["activity_name"],
            due_date=data["due_date"], notes=notes, activity_type=data["activity_type"],
        )
    await update.message.reply_text(
        dialogs.ACTIVITY_CREATE_SUCCESS.format(activity_type=data["activity_type"].capitalize(), activity_name=data["activity_name"])
    )
    context.user_data.clear()
    return ConversationHandler.END

async def activity_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.edit_message_text(dialogs.OPERATION_CANCELED)
    else:
        await update.message.reply_text(dialogs.OPERATION_CANCELED)
    context.user_data.clear()
    return ConversationHandler.END

def setup_activity_handler() -> ConversationHandler:
    """Cria o ConversationHandler para /addtrabalho e /addprova."""
    return ConversationHandler(
        entry_points=[
            CommandHandler("addtrabalho", new_activity_start),
            CommandHandler("addprova", new_activity_start),
            CallbackQueryHandler(new_activity_start, pattern="^start_new_activity_trabalho$"),
            CallbackQueryHandler(new_activity_start, pattern="^start_new_activity_prova$")
        ],
        states={
            A_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_activity_name)],
            A_SUBJECT: [CallbackQueryHandler(received_activity_subject, pattern="^link_subject_")],
            A_DUEDATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_activity_due_date)],
            A_NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_activity_notes)],
            ConversationHandler.TIMEOUT: [TypeHandler(Update, notify_conversation_timeout)],
        },
        fallbacks=[CommandHandler("cancelar", activity_cancel)],
        conversation_timeout=CONVERSATION_TIMEOUT_SECONDS,
    )
    
    
# =============================================================================
# Seção 2: Lógica de Listagem e Gerenciamento
# =============================================================================

ACTIVITIES_PER_PAGE = 10
SAFE_MESSAGE_LENGTH = 3500  # abaixo do limite de 4096 do Telegram, com folga pro rodapé de paginação


def _build_activity_line(a) -> str:
    icon = "📝" if a.activity_type == "trabalho" else "❗️"
    date_str = a.due_date.strftime("%d/%m/%Y")
    line = (
        f"{icon} <b>{a.name}</b> ({a.activity_type.capitalize()})\n"
        f"   • <b>Matéria:</b> {a.subject.name}\n"
        f"   • <b>Data:</b> {date_str}\n"
    )
    if a.notes:
        line += f"   • <b>Obs:</b> {a.notes}\n"
    return line + dialogs.SEPARATOR


def build_activity_list_view(activities: list, page: int = 0):
    """
    Monta o texto do /calendario. Se a lista inteira couber numa mensagem,
    manda tudo de uma vez (comportamento de sempre); só pagina quando
    o usuário tem atividades demais pra caber numa única mensagem.
    """
    if not activities:
        return dialogs.ACTIVITY_LIST_NO_ACTIVITIES, None

    full_message = dialogs.ACTIVITY_LIST_HEADER + "".join(_build_activity_line(a) for a in activities)
    if len(full_message) <= SAFE_MESSAGE_LENGTH:
        return full_message, None

    start = page * ACTIVITIES_PER_PAGE
    end = start + ACTIVITIES_PER_PAGE
    total_pages = (len(activities) - 1) // ACTIVITIES_PER_PAGE + 1

    message = dialogs.ACTIVITY_LIST_HEADER
    message += "".join(_build_activity_line(a) for a in activities[start:end])
    message += f"\nPágina {page + 1} de {total_pages}"

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Anterior", callback_data=f"activity_page_{page - 1}"))
    if end < len(activities):
        nav_buttons.append(InlineKeyboardButton("Próxima ➡️", callback_data=f"activity_page_{page + 1}"))
    reply_markup = InlineKeyboardMarkup([nav_buttons]) if nav_buttons else None

    return message, reply_markup


async def list_activities(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lista as atividades, respondendo a um comando ou editando uma mensagem de botão."""
    query = update.callback_query
    if query:
        await query.answer()
        telegram_user = query.from_user
    else:
        telegram_user = update.effective_user

    with SessionLocal() as db:
        user, _ = user_service.get_or_create_user(db, telegram_user.id, telegram_user.first_name, telegram_user.username)
        activities = activity_service.get_activities_by_user(db, user)
        message, reply_markup = build_activity_list_view(activities, page=0)

    if query:
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode="HTML")
    else:
        await update.message.reply_html(message, reply_markup=reply_markup)


async def activity_list_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Navega entre as páginas do /calendario quando a lista não coube numa mensagem só."""
    query = update.callback_query
    await query.answer()
    page = int(query.data.split('_')[-1])
    telegram_user = query.from_user

    with SessionLocal() as db:
        user, _ = user_service.get_or_create_user(db, telegram_user.id, telegram_user.first_name, telegram_user.username)
        activities = activity_service.get_activities_by_user(db, user)
        message, reply_markup = build_activity_list_view(activities, page=page)

    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode="HTML")


async def manage_activities_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Função de entrada para /gerenciartrabalhos e /gerenciarprovas."""
    query = update.callback_query
    activity_type = ""
    if query:
        await query.answer()
        data = query.data
        activity_type = "trabalho" if "trabalhos" in data else "prova"
    else:
        command = update.message.text.split(' ')[0][1:]
        activity_type = "trabalho" if command == "gerenciartrabalhos" else "prova"
    
    context.user_data["activity_type_to_manage"] = activity_type
    telegram_user = query.from_user if query else update.effective_user

    with SessionLocal() as db:
        user, _ = user_service.get_or_create_user(db, telegram_user.id, telegram_user.first_name, telegram_user.username)
        acts = activity_service.get_activities_by_user_and_type(db, user, activity_type)

    if not acts:
        text = dialogs.MANAGE_ACTIVITIES_NONE.format(type=activity_type)
        if query: await query.edit_message_text(text)
        else: await update.message.reply_text(text)
        return ConversationHandler.END

    kb = [[InlineKeyboardButton(f"{a.name} ({a.due_date.strftime('%d/%m')})", callback_data=f"mng_act_{a.id}")] for a in acts]
    text = dialogs.MANAGE_ACTIVITIES_HEADER.format(type=activity_type.capitalize())
    reply_markup = InlineKeyboardMarkup(kb)
    
    if query: await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else: await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        
    return SELECT_ACTIVITY_ACTION


async def select_activity_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    activity_id = int(query.data.split('_')[-1])
    context.user_data['activity_id_to_manage'] = activity_id

    with SessionLocal() as db:
        activity = activity_service.get_activity_by_id(db, activity_id)

    keyboard = [
        [InlineKeyboardButton("Editar ✏️", callback_data=f"edit_activity_{activity_id}")],
        [InlineKeyboardButton("Excluir 🗑️", callback_data=f"delete_activity_{activity_id}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(dialogs.MANAGING_ACTIVITY_HEADER.format(name=activity.name), reply_markup=reply_markup, parse_mode='HTML')
    return SELECT_ACTIVITY_ACTION


def build_activity_edit_view(activity):
    """Monta o texto e o teclado do menu de edição de uma atividade."""
    text = dialogs.EDITING_ACTIVITY_HEADER.format(
        name=activity.name,
        subject=activity.subject.name,
        date=activity.due_date.strftime('%d/%m/%Y'),
        notes=(activity.notes or 'Nenhuma')
    )
    keyboard = [
        [
            InlineKeyboardButton("Nome", callback_data="editactivityfield_name"),
            InlineKeyboardButton("Matéria", callback_data="editactivityfield_subject_id"),
        ],
        [
            InlineKeyboardButton("Data de Entrega", callback_data="editactivityfield_due_date"),
            InlineKeyboardButton("Observações", callback_data="editactivityfield_notes"),
        ],
        [InlineKeyboardButton("« Voltar", callback_data=f"mng_act_{activity.id}")]
    ]
    return text, InlineKeyboardMarkup(keyboard)


async def show_activity_edit_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    activity_id = context.user_data['activity_id_to_manage']
    with SessionLocal() as db:
        activity = activity_service.get_activity_by_id(db, activity_id)

    text, reply_markup = build_activity_edit_view(activity)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    return SHOWING_ACTIVITY_EDIT_OPTIONS


async def select_activity_field_to_edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    field_to_edit = query.data.split('_')[1]
    context.user_data['field_to_edit'] = field_to_edit

    if field_to_edit == "subject_id":
        telegram_user = query.from_user
        with SessionLocal() as db:
            user, _ = user_service.get_or_create_user(db, telegram_user.id, telegram_user.first_name, telegram_user.username)
            subjects = subject_service.get_subjects_by_user(db, user)
        keyboard = [[InlineKeyboardButton(s.name, callback_data=f"newsubjectid_{s.id}")] for s in subjects]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(dialogs.ASK_NEW_SUBJECTID, reply_markup=reply_markup)
    elif field_to_edit == "due_date":
        await query.message.reply_text(dialogs.ASK_NEW_DUE_DATE, parse_mode='HTML')
    else:
        field_map = {'name': 'nome', 'notes': 'observações'}
        await query.message.reply_text(dialogs.ASK_NEW_FIELD.format(field=field_map[field_to_edit]), parse_mode='HTML')
    return AWAITING_ACTIVITY_NEW_VALUE


async def receive_activity_field_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    field_to_edit = context.user_data.get('field_to_edit')
    activity_id = context.user_data.get('activity_id_to_manage')
    new_value = None

    if query:
        await query.answer()
        if query.data.startswith("newsubjectid_"):
            new_value = int(query.data.split('_')[1])
            await query.delete_message()
    else:
        new_value = update.message.text
        if field_to_edit == 'due_date':
            try:
                new_value = datetime.strptime(new_value, "%d/%m/%Y").date()
            except ValueError:
                await update.message.reply_text(dialogs.ERROR_INVALID_DATE, parse_mode='HTML')
                return AWAITING_ACTIVITY_NEW_VALUE
        elif field_to_edit == 'notes' and new_value.lower() in ['não', 'nao', 'n', 'pular', 'remover']:
            new_value = None

    with SessionLocal() as db:
        activity_service.update_activity(db, activity_id, {field_to_edit: new_value})
        activity = activity_service.get_activity_by_id(db, activity_id)

    text, reply_markup = build_activity_edit_view(activity)
    message_to_send_from = update.message if not query else query.message
    await message_to_send_from.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
    return SHOWING_ACTIVITY_EDIT_OPTIONS


async def handle_delete_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    activity_id = int(query.data.split('_')[-1])
    keyboard = [[
        InlineKeyboardButton("✅ Sim, excluir", callback_data=f"confirmdelete_activity_{activity_id}"),
        InlineKeyboardButton("❌ Cancelar", callback_data=f"mng_act_{activity_id}")
    ]]
    await query.edit_message_text(dialogs.CONFIRM_DELETE_ITEM, reply_markup=InlineKeyboardMarkup(keyboard))
    return CONFIRM_ACTIVITY_DELETE


async def confirm_activity_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    activity_id = int(query.data.split('_')[-1])
    with SessionLocal() as db:
        activity_service.delete_activity_by_id(db, activity_id)
    await query.edit_message_text(dialogs.ACTIVITY_DELETED)
    context.user_data.clear()
    return ConversationHandler.END


def setup_activity_management_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("gerenciartrabalhos", manage_activities_start),
            CommandHandler("gerenciarprovas", manage_activities_start),
            CallbackQueryHandler(manage_activities_start, pattern="^start_manage_trabalhos$"),
            CallbackQueryHandler(manage_activities_start, pattern="^start_manage_provas$")
        ],
        states={
            SELECT_ACTIVITY_ACTION: [
                CallbackQueryHandler(select_activity_action_callback, pattern="^mng_act_"),
                CallbackQueryHandler(show_activity_edit_options, pattern="^edit_activity_"),
                CallbackQueryHandler(handle_delete_confirmation, pattern="^delete_activity_"),
            ],
            SHOWING_ACTIVITY_EDIT_OPTIONS: [
                CallbackQueryHandler(select_activity_field_to_edit_callback, pattern="^editactivityfield_"),
                CallbackQueryHandler(select_activity_action_callback, pattern="^mng_act_"),
            ],
            AWAITING_ACTIVITY_NEW_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_activity_field_update),
                CallbackQueryHandler(receive_activity_field_update, pattern="^newsubjectid_"),
            ],
            CONFIRM_ACTIVITY_DELETE: [
                CallbackQueryHandler(confirm_activity_delete_callback, pattern="^confirmdelete_activity_"),
                CallbackQueryHandler(select_activity_action_callback, pattern="^mng_act_"),
            ],
            ConversationHandler.TIMEOUT: [TypeHandler(Update, notify_conversation_timeout)],
        },
        fallbacks=[CommandHandler("cancelar", activity_cancel)],
        per_message=False,
        conversation_timeout=CONVERSATION_TIMEOUT_SECONDS,
    )
    
    