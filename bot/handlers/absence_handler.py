import logging
from datetime import date, datetime
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
from bot.services import user_service, subject_service, absence_service
from bot.core import dialogs

logger = logging.getLogger(__name__)

# Estados para /faltei
SELECT_SUBJECT_FOR_ABSENCE, GET_ABSENCE_DATE, GET_ABSENCE_QUANTITY, GET_ABSENCE_NOTES = range(40, 44)
# Novos estados para /gerenciarfaltas
SELECT_SUBJECT_TO_MANAGE, AWAITING_RECORD_CHOICE, AWAITING_ACTION_CHOICE, AWAITING_NEW_QUANTITY, CONFIRM_DELETE = range(44, 49)


# =============================================================================
# Seção 1: Handler de Conversa para /faltei (Criação)
# =============================================================================

async def new_absence_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia a conversa para registrar uma falta (via comando ou botão)."""
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
        text = dialogs.ABSENCE_CREATE_NO_SUBJECTS
        if query:
            await query.message.reply_text(text)
        else:
            await update.message.reply_text(text)
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(s.name, callback_data=f"absence_subject_{s.id}")] for s in subjects]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = dialogs.ABSENCE_CREATE_ASK_SUBJECT
    if query:
        await query.message.reply_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

    return SELECT_SUBJECT_FOR_ABSENCE

async def received_absence_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe a matéria e pede a data da falta."""
    query = update.callback_query
    await query.answer()

    subject_id = int(query.data.split('_')[-1])
    context.user_data['absence_subject_id'] = subject_id
    
    keyboard = [[InlineKeyboardButton("A aula foi hoje", callback_data="absence_date_today")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text=dialogs.ABSENCE_CREATE_ASK_DATE,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return GET_ABSENCE_DATE

async def received_absence_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe a data (por botão ou texto) e pede a quantidade de faltas."""
    query = update.callback_query
    absence_date_obj = None

    if query:
        await query.answer()
        absence_date_obj = date.today()
        await query.edit_message_text(text=dialogs.ABSENCE_CREATE_DATE_SELECTED.format(date=absence_date_obj.strftime('%d/%m/%Y')))
    else:
        date_str = update.message.text
        try:
            absence_date_obj = datetime.strptime(date_str, "%d/%m/%Y").date()
        except ValueError:
            await update.message.reply_text(dialogs.ERROR_INVALID_DATE, parse_mode='Markdown')
            return GET_ABSENCE_DATE

    context.user_data['absence_date'] = absence_date_obj
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=dialogs.ABSENCE_CREATE_ASK_QUANTITY
    )
    return GET_ABSENCE_QUANTITY

async def received_absence_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe a quantidade e pede por uma observação opcional."""
    try:
        quantity = int(update.message.text)
        if quantity <= 0: raise ValueError
    except (ValueError, TypeError):
        await update.message.reply_text(dialogs.ERROR_INVALID_NUMBER_POSITIVE)
        return GET_ABSENCE_QUANTITY
    
    context.user_data['absence_quantity'] = quantity
    await update.message.reply_text(dialogs.ABSENCE_CREATE_ASK_NOTES)
    return GET_ABSENCE_NOTES

async def received_absence_notes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe as observações e salva tudo no banco."""
    notes = update.message.text
    if notes.lower() in ['não', 'nao', 'n', 'pular']:
        notes = None

    data = context.user_data
    telegram_user = update.effective_user
    
    with SessionLocal() as db:
        user, _ = user_service.get_or_create_user(db, telegram_user.id, telegram_user.first_name, telegram_user.username)
        subject = subject_service.get_subject_by_id(db, data['absence_subject_id'])
        
        absence_service.add_absence(db, user, subject, data['absence_date'], data['absence_quantity'], notes)
        
        await update.message.reply_text(
            dialogs.ABSENCE_CREATE_SUCCESS.format(
                quantity=data['absence_quantity'],
                subject_name=subject.name,
                total_absences=subject.total_absences
            ), 
            parse_mode='Markdown'
        )

    context.user_data.clear()
    return ConversationHandler.END

async def absence_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela a operação atual de faltas."""
    if update.callback_query:
        await update.callback_query.edit_message_text(dialogs.OPERATION_CANCELED)
    else:
        await update.message.reply_text(dialogs.OPERATION_CANCELED)
    context.user_data.clear()
    return ConversationHandler.END
    
    
# =============================================================================
# Seção 2: Relatório e Gerenciamento de Faltas
# =============================================================================

async def report_absences(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gera um relatório com o total de faltas para cada matéria."""
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
        message = dialogs.ABSENCE_REPORT_NO_SUBJECTS
        if query: await query.edit_message_text(text=message)
        else: await update.message.reply_text(text=message)
        return

    message = dialogs.ABSENCE_REPORT_HEADER
    for subject in subjects:
        message += dialogs.ABSENCE_REPORT_ITEM.format(subject_name=subject.name, total_absences=subject.total_absences)

    if query:
        await query.edit_message_text(message, parse_mode='HTML')
    else:
        await update.message.reply_html(message)


async def manage_absences_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Pede para o usuário escolher uma matéria para gerenciar as faltas."""
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
        text = dialogs.ABSENCE_MANAGE_NO_SUBJECTS
        if query: await query.edit_message_text(text=text)
        else: await update.message.reply_text(text)
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(f"{s.name} ({s.total_absences} faltas)", callback_data=f"mng_abs_subj_{s.id}")] for s in subjects]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = dialogs.ABSENCE_MANAGE_PROMPT
    
    if query: await query.edit_message_text(text, reply_markup=reply_markup)
    else: await update.message.reply_text(text, reply_markup=reply_markup)
        
    return SELECT_SUBJECT_TO_MANAGE

async def show_numbered_absences(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Mostra a lista numerada de faltas e pede para o usuário escolher um número."""
    query = update.callback_query
    await query.answer()
    subject_id = int(query.data.split('_')[-1])

    with SessionLocal() as db:
        subject = subject_service.get_subject_by_id(db, subject_id)
        absences = absence_service.get_absences_by_subject(db, subject)

    if not absences:
        await query.edit_message_text(dialogs.ABSENCE_MANAGE_NO_RECORDS.format(subject_name=subject.name), parse_mode='HTML')
        return ConversationHandler.END

    message = f"Histórico de faltas para <b>{subject.name}</b>:\n\n"
    absence_ids = []
    for i, absence in enumerate(absences, 1):
        absence_ids.append(absence.id)
        date_str = absence.absence_date.strftime('%d/%m/%Y')
        message += f"<b>{i}</b> - {date_str} - {absence.quantity} Falta(s)\n"
        if absence.notes:
            message += f"Obs: {absence.notes}\n"
        message += dialogs.SEPARATOR

    message += "\nPor favor, envie o <b>número</b> do registro que deseja gerenciar."
    
    # Salva a lista de IDs para referência futura
    context.user_data['absence_ids_map'] = absence_ids
    
    await query.edit_message_text(message, parse_mode='HTML')
    return AWAITING_RECORD_CHOICE

async def received_record_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe o número do registro e pergunta a ação (editar ou excluir)."""
    try:
        choice = int(update.message.text)
        absence_ids_map = context.user_data['absence_ids_map']
        if not (1 <= choice <= len(absence_ids_map)):
            raise ValueError
    except (ValueError, TypeError):
        await update.message.reply_text("Número inválido. Por favor, envie um número da lista acima.")
        return AWAITING_RECORD_CHOICE

    # Converte a escolha do usuário (ex: 1) para o ID real do banco (ex: 17)
    selected_absence_id = absence_ids_map[choice - 1]
    context.user_data['absence_id_to_manage'] = selected_absence_id

    text = "O que você deseja fazer?\n\n<b>1</b> - Editar a quantidade\n<b>2</b> - Excluir o registro"
    await update.message.reply_text(text, parse_mode='HTML')
    return AWAITING_ACTION_CHOICE

async def received_action_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe a ação (1 ou 2) e direciona para o próximo passo."""
    choice = update.message.text
    if choice == '1': # Editar
        await update.message.reply_text(dialogs.ABSENCE_MANAGE_ASK_NEW_QUANTITY)
        return AWAITING_NEW_QUANTITY
    elif choice == '2': # Excluir
        await update.message.reply_text("Tem certeza? Digite <b>SIM</b> para confirmar a exclusão.", parse_mode='HTML')
        return CONFIRM_DELETE
    else:
        await update.message.reply_text("Opção inválida. Por favor, envie <b>1</b> para editar ou <b>2</b> para excluir.", parse_mode='HTML')
        return AWAITING_ACTION_CHOICE


async def received_new_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe a nova quantidade e finaliza."""
    try:
        new_quantity = int(update.message.text)
        if new_quantity <= 0: raise ValueError
    except (ValueError, TypeError):
        await update.message.reply_text(dialogs.ERROR_INVALID_NUMBER_POSITIVE)
        return AWAITING_NEW_QUANTITY

    absence_id = context.user_data['absence_id_to_manage']
    with SessionLocal() as db:
        absence_service.update_absence_quantity(db, absence_id, new_quantity)
    
    await update.message.reply_text(dialogs.ABSENCE_MANAGE_UPDATE_SUCCESS)
    context.user_data.clear()
    return ConversationHandler.END

async def confirm_text_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe a confirmação de exclusão por texto e finaliza."""
    if update.message.text.upper() == 'SIM':
        absence_id = context.user_data['absence_id_to_manage']
        with SessionLocal() as db:
            absence_service.delete_absence_by_id(db, absence_id)
        await update.message.reply_text(dialogs.ABSENCE_MANAGE_DELETE_SUCCESS)
        context.user_data.clear()
        return ConversationHandler.END
    else:
        await update.message.reply_text("Exclusão cancelada.")
        context.user_data.clear()
        return ConversationHandler.END


# =============================================================================
# Seção 3: Funções de Setup que Montam os Handlers
# =============================================================================

def setup_absence_handler() -> ConversationHandler:
    """Cria e configura o ConversationHandler para /faltei."""
    return ConversationHandler(
        entry_points=[
            CommandHandler("faltei", new_absence_start),
            CallbackQueryHandler(new_absence_start, pattern="^start_new_absence$")
        ],
        states={
            SELECT_SUBJECT_FOR_ABSENCE: [CallbackQueryHandler(received_absence_subject, pattern="^absence_subject_")],
            GET_ABSENCE_DATE: [
                CallbackQueryHandler(received_absence_date, pattern="^absence_date_today$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, received_absence_date)
            ],
            GET_ABSENCE_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_absence_quantity)],
            GET_ABSENCE_NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_absence_notes)],
        },
        fallbacks=[CommandHandler("cancelar", absence_cancel)],
        per_message=False
    )

def setup_absence_management_handler() -> ConversationHandler:
    """Cria o ConversationHandler para /gerenciarfaltas com base em texto."""
    return ConversationHandler(
        entry_points=[
            CommandHandler("gerenciarfaltas", manage_absences_start),
            # Removido o entry_point de botão, pois o comando agora é explícito
        ],
        states={
            SELECT_SUBJECT_TO_MANAGE: [CallbackQueryHandler(show_numbered_absences, pattern="^mng_abs_subj_")],
            AWAITING_RECORD_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_record_choice)],
            AWAITING_ACTION_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_action_choice)],
            AWAITING_NEW_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_new_quantity)],
            CONFIRM_DELETE: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_text_delete)],
        },
        fallbacks=[CommandHandler("cancelar", absence_cancel)],
        per_message=False,
    )
    
    
    
    
async def debug_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Função temporária para capturar qualquer clique de botão não tratado."""
    query = update.callback_query
    await query.answer("DEBUG: Clique capturado pelo handler geral.")
    print("\n--- DEBUG: COLETOR GERAL CAPTUROU UM CLIQUE ---")
    print(f"Callback Data recebido: '{query.data}'")
    print("Isso significa que o estado AWAITING_ACTION está correto, mas os patterns dos handlers específicos falharam.")
    print("--- FIM DO DEBUG ---\n")
    # Não retorna nada para não mudar de estado
