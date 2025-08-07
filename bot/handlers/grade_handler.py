import logging
from decimal import Decimal, InvalidOperation
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)

from bot.db.base import SessionLocal
from bot.services import user_service, subject_service, grade_service
from bot.core import dialogs

logger = logging.getLogger(__name__)

# --- Estados para /addnota (Criação) ---
SELECT_GRADE_SUBJECT, SELECT_GRADE_NAME, SELECT_GRADE_VALUE = range(50, 53)
# --- Estados para /gerenciarnotas (Gerenciamento) ---
SELECT_SUBJECT_TO_MANAGE, LIST_GRADES, CONFIRM_DELETE, AWAIT_NEW_GRADE_NAME, AWAIT_NEW_GRADE_VALUE = range(53, 58)


# =============================================================================
# Seção 1: Handler de Conversa para /addnota
# =============================================================================

async def new_grade_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    telegram_user = query.from_user if query else update.effective_user
    if query:
        await query.answer()

    with SessionLocal() as db:
        user, _ = user_service.get_or_create_user(
            db, telegram_user.id, telegram_user.first_name, telegram_user.username
        )
        subjects = subject_service.get_subjects_by_user(db, user)

    if not subjects:
        text = dialogs.GRADE_CREATE_NO_SUBJECTS
        if query:
            await query.message.reply_text(text)
        else:
            await update.message.reply_text(text)
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(s.name, callback_data=f"grade_subject_{s.id}")] for s in subjects]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = dialogs.GRADE_CREATE_ASK_SUBJECT
    
    if query:
        await query.message.reply_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)
    return SELECT_GRADE_SUBJECT


async def received_grade_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    subject_id = int(query.data.split("_")[-1])
    context.user_data["grade_subject_id"] = subject_id
    await query.edit_message_text(dialogs.GRADE_CREATE_ASK_NAME)
    return SELECT_GRADE_NAME


async def received_grade_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["grade_name"] = update.message.text
    await update.message.reply_text(dialogs.GRADE_CREATE_ASK_VALUE, parse_mode="HTML")
    return SELECT_GRADE_VALUE


async def received_grade_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        val = Decimal(update.message.text.replace(",", "."))
        if val < 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await update.message.reply_text(dialogs.GRADE_CREATE_INVALID_VALUE)
        return SELECT_GRADE_VALUE

    subj_id = context.user_data["grade_subject_id"]
    name = context.user_data["grade_name"]
    telegram_user = update.effective_user

    with SessionLocal() as db:
        user, _ = user_service.get_or_create_user(
            db, telegram_user.id, telegram_user.first_name, telegram_user.username
        )
        subject = subject_service.get_subject_by_id(db, subj_id)
        grade_service.add_grade(db, user, subject, name, val)

        # CORREÇÃO: A formatação e o envio da mensagem agora estão DENTRO do 'with'
        text = dialogs.GRADE_CREATE_SUCCESS.format(
            grade_value=f"{val:.2f}", 
            grade_name=name, 
            subject_name=subject.name
        )
        await update.message.reply_html(text)

    context.user_data.clear()
    return ConversationHandler.END


async def grade_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.edit_message_text(dialogs.OPERATION_CANCELED)
    else:
        await update.message.reply_text(dialogs.OPERATION_CANCELED)
    context.user_data.clear()
    return ConversationHandler.END

# =============================================================================
# Seção 2: Handler de Conversa para /gerenciarnotas
# =============================================================================

async def manage_grades_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query:
        await query.answer()
        telegram_user = query.from_user
    else:
        telegram_user = update.effective_user

    with SessionLocal() as db:
        user, _ = user_service.get_or_create_user(
            db, telegram_user.id, telegram_user.first_name, telegram_user.username
        )
        subjects = subject_service.get_subjects_by_user(db, user)

    if not subjects:
        text = dialogs.GRADE_MANAGE_NO_SUBJECTS
        if query:
            await query.edit_message_text(text)
        else:
            await update.message.reply_text(text)
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(s.name, callback_data=f"mng_grade_subj_{s.id}")] for s in subjects]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = dialogs.GRADE_MANAGE_ASK_SUBJECT

    if query:
        await query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)
        
    return SELECT_SUBJECT_TO_MANAGE


async def list_grades_for_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    subj_id = int(query.data.split("_")[-1])
    context.user_data["subject_id_for_grade_mng"] = subj_id

    with SessionLocal() as db:
        subject = subject_service.get_subject_by_id(db, subj_id)
        grades = grade_service.get_grades_by_subject(db, subject)

    if not grades:
        await query.edit_message_text(
            dialogs.GRADE_MANAGE_NO_GRADES.format(subject_name=subject.name),
            parse_mode="HTML"
        )
        return ConversationHandler.END

    message = dialogs.GRADE_MANAGE_LIST_HEADER.format(subject_name=subject.name)
    message += "".join(f" • <b>{g.name}:</b> {g.value:.2f}\n" for g in grades)
    keyboard = [
        [InlineKeyboardButton(f"Editar / Excluir: {g.name}", callback_data=f"select_grade_{g.id}")]
        for g in grades
    ]
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return LIST_GRADES


async def select_grade_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    grade_id = int(query.data.split("_")[-1])
    context.user_data["grade_id_to_manage"] = grade_id

    keyboard = [
        [
            InlineKeyboardButton("✏️ Editar Nota", callback_data=f"edit_grade_{grade_id}"),
            InlineKeyboardButton("🗑️ Excluir Nota", callback_data=f"delete_grade_{grade_id}")
        ],
        [InlineKeyboardButton("« Voltar", callback_data=f"mng_grade_subj_{context.user_data['subject_id_for_grade_mng']}")]
    ]
    await query.edit_message_text(dialogs.GRADE_MANAGE_ACTION_PROMPT, reply_markup=InlineKeyboardMarkup(keyboard))
    return LIST_GRADES


async def handle_grade_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    action, id_str = query.data.split("_", 2)[1:]
    gid = int(id_str)

    if action == "delete":
        await query.edit_message_text(
            dialogs.GRADE_MANAGE_DELETE_CONFIRM,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Sim, excluir", callback_data=f"confirm_delete_grade_{gid}"),
                InlineKeyboardButton("❌ Cancelar", callback_data=f"select_grade_{gid}")
            ]])
        )
        return CONFIRM_DELETE

    if action == "edit":
        await query.message.reply_text(dialogs.GRADE_EDIT_ASK_NAME)
        return AWAIT_NEW_GRADE_NAME


async def received_new_grade_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["new_grade_name"] = update.message.text
    await update.message.reply_text(dialogs.GRADE_EDIT_ASK_VALUE, parse_mode="HTML")
    return AWAIT_NEW_GRADE_VALUE


async def received_new_grade_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        new_val = Decimal(update.message.text.replace(",", "."))
        if new_val < 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await update.message.reply_text(dialogs.GRADE_EDIT_INVALID_VALUE)
        return AWAIT_NEW_GRADE_VALUE

    grade_id = context.user_data["grade_id_to_manage"]
    subject_id = context.user_data["subject_id_for_grade_mng"]
    new_name = context.user_data["new_grade_name"]

    with SessionLocal() as db:
        grade_service.update_grade(db, grade_id, new_name, new_val)

    await update.message.reply_text(dialogs.GRADE_EDIT_SUCCESS)

    # LÓGICA DE RECARREGAMENTO (SEM 'fake_update')
    # Prepara os dados e chama a função que lista as notas novamente
    query_data = f"mng_grade_subj_{subject_id}"
    update.callback_query = type('CallbackQuery', (), {'data': query_data, 'answer': (lambda: None), 'message': update.message, 'from_user': update.effective_user})()
    
    return await list_grades_for_subject(update, context)

async def confirm_delete_grade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    gid = int(query.data.split("_")[-1])
    subj_id = context.user_data["subject_id_for_grade_mng"]

    with SessionLocal() as db:
        grade_service.delete_grade_by_id(db, gid)

    await query.edit_message_text(dialogs.GRADE_DELETE_SUCCESS)
    query.data = f"mng_grade_subj_{subj_id}"
    return await list_grades_for_subject(update, context)


# =============================================================================
# Seção 3: Funções de Setup que Montam os Handlers
# =============================================================================

def setup_grade_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("addnota", new_grade_start),
            CallbackQueryHandler(new_grade_start, pattern="^start_new_grade$")
        ],
        states={
            SELECT_GRADE_SUBJECT: [CallbackQueryHandler(received_grade_subject, pattern="^grade_subject_")],
            SELECT_GRADE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_grade_name)],
            SELECT_GRADE_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_grade_value)],
        },
        fallbacks=[CommandHandler("cancelar", grade_cancel)],
        per_message=False
    )


def setup_grade_management_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("gerenciarnotas", manage_grades_start),
            CallbackQueryHandler(manage_grades_start, pattern="^start_manage_grades$")
        ],
        states={
            SELECT_SUBJECT_TO_MANAGE: [CallbackQueryHandler(list_grades_for_subject, pattern="^mng_grade_subj_")],
            LIST_GRADES: [
                CallbackQueryHandler(select_grade_action, pattern="^select_grade_"),
                CallbackQueryHandler(handle_grade_action, pattern="^(edit_grade_|delete_grade_)"),
                CallbackQueryHandler(list_grades_for_subject, pattern="^mng_grade_subj_"),
            ],
            CONFIRM_DELETE: [
                CallbackQueryHandler(confirm_delete_grade, pattern="^confirm_delete_grade_"),
                CallbackQueryHandler(select_grade_action, pattern="^select_grade_"),
            ],
            AWAIT_NEW_GRADE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_new_grade_name)],
            AWAIT_NEW_GRADE_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_new_grade_value)],
        },
        fallbacks=[CommandHandler("cancelar", grade_cancel)],
        per_message=False,
    )