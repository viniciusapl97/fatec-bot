import logging
from datetime import date, datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, filters, CallbackQueryHandler,
)
from bot.db.base import SessionLocal
from bot.services import user_service, subject_service, absence_service

logger = logging.getLogger(__name__)

# Estados para /faltei
SELECT_SUBJECT_FOR_ABSENCE, GET_ABSENCE_DATE, GET_ABSENCE_QUANTITY, GET_ABSENCE_NOTES = range(40, 44)
# Estados para /gerenciarfaltas
SELECT_SUBJECT_TO_MANAGE, LIST_ABSENCES, CONFIRM_DELETE, AWAIT_NEW_QUANTITY = range(44, 48)


# =============================================================================
# Seção 1: Handler de Conversa para /faltei (Criação)
# =============================================================================

async def new_absence_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia a conversa para registrar uma falta, pedindo a matéria."""
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
        text = "Você precisa ter matérias cadastradas para registrar uma falta. Use /addmateria."
        if query: await query.message.reply_text(text)
        else: await update.message.reply_text(text)
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(s.name, callback_data=f"absence_subject_{s.id}")] for s in subjects]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "Para qual matéria você deseja registrar a falta?\n\nEnvie /cancelar para interromper."
    if query: await query.message.reply_text(text, reply_markup=reply_markup)
    else: await update.message.reply_text(text, reply_markup=reply_markup)

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
        text="Quando foi a falta? Clique no botão ou envie a data no formato *DD/MM/AAAA*.",
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
        await query.edit_message_text(text=f"Data selecionada: {absence_date_obj.strftime('%d/%m/%Y')}")
    else:
        date_str = update.message.text
        try:
            absence_date_obj = datetime.strptime(date_str, "%d/%m/%Y").date()
        except ValueError:
            await update.message.reply_text("Formato de data inválido. 😓\nPor favor, tente novamente no formato *DD/MM/AAAA*.", parse_mode='Markdown')
            return GET_ABSENCE_DATE

    context.user_data['absence_date'] = absence_date_obj
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Entendido. Quantas aulas/faltas você perdeu nesse dia? (normalmente 2 ou 4)"
    )
    return GET_ABSENCE_QUANTITY

async def received_absence_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe a quantidade e pede por uma observação opcional."""
    try:
        quantity = int(update.message.text)
        if quantity <= 0: raise ValueError
    except (ValueError, TypeError):
        await update.message.reply_text("Por favor, envie um número inteiro e positivo.")
        return GET_ABSENCE_QUANTITY
    
    context.user_data['absence_quantity'] = quantity
    await update.message.reply_text("Deseja adicionar uma observação? (ex: 'atestado médico'). Se não, envie 'não' ou 'pular'.")
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
            f"✅ {data['absence_quantity']} falta(s) registrada(s) para *{subject.name}*.\n"
            f"Total atual: *{subject.total_absences}* faltas.", parse_mode='Markdown'
        )

    context.user_data.clear()
    return ConversationHandler.END

async def absence_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela a operação atual de faltas."""
    if update.callback_query:
        await update.callback_query.edit_message_text("Operação cancelada.")
    else:
        await update.message.reply_text("Operação cancelada.")
    context.user_data.clear()
    return ConversationHandler.END

# =============================================================================
# Seção 2: Handler de Conversa para /gerenciarfaltas (Gerenciamento)
# =============================================================================

async def manage_absences_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Pede para o usuário escolher uma matéria para gerenciar as faltas (via comando ou botão)."""
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
        text = "Você não tem matérias para gerenciar faltas."
        if query:
            await query.edit_message_text(text=text)
        else:
            await update.message.reply_text(text)
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(f"{s.name} ({s.total_absences} faltas)", callback_data=f"mng_abs_subj_{s.id}")] for s in subjects]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "Escolha uma matéria para ver o histórico de faltas:"

    if query:
        await query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)
        
    return SELECT_SUBJECT_TO_MANAGE

async def list_absences_for_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    subject_id = int(query.data.split('_')[-1])
    context.user_data['subject_id_for_absence_mng'] = subject_id

    with SessionLocal() as db:
        subject = subject_service.get_subject_by_id(db, subject_id)
        absences = absence_service.get_absences_by_subject(db, subject)

    if not absences:
        await query.edit_message_text(f"Nenhum registro de falta encontrado para *{subject.name}*.", parse_mode='Markdown')
        return ConversationHandler.END

    message = f"Histórico de faltas para *{subject.name}* (Total: {subject.total_absences}):\n"
    keyboard = []
    for absence in absences:
        date_str = absence.absence_date.strftime('%d/%m/%Y')
        notes_str = f" ({absence.notes[:20]}...)" if absence.notes else ""
        keyboard.append(
            [InlineKeyboardButton(f"Falta em {date_str} (Qtd: {absence.quantity}){notes_str}", callback_data=f"select_absence_{absence.id}")]
        )
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    return LIST_ABSENCES

async def select_absence_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    absence_id = int(query.data.split('_')[-1])
    context.user_data['absence_id_to_manage'] = absence_id
    
    keyboard = [
        [
            InlineKeyboardButton("✏️ Editar Quantidade", callback_data=f"edit_absence_{absence_id}"),
            InlineKeyboardButton("🗑️ Excluir Registro", callback_data=f"delete_absence_{absence_id}")
        ],
        [InlineKeyboardButton("« Voltar", callback_data=f"mng_abs_subj_{context.user_data['subject_id_for_absence_mng']}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("O que deseja fazer com este registro de falta?", reply_markup=reply_markup)
    return LIST_ABSENCES

async def handle_absence_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    action, absence_id_str = query.data.split('_', 2)[1:]
    absence_id = int(absence_id_str)

    if action == "delete":
        keyboard = [[
            InlineKeyboardButton("✅ Sim, excluir", callback_data=f"confirm_delete_absence_{absence_id}"),
            InlineKeyboardButton("❌ Cancelar", callback_data=f"select_absence_{absence_id}")
        ]]
        await query.edit_message_text("Tem certeza que deseja excluir este registro?", reply_markup=InlineKeyboardMarkup(keyboard))
        return CONFIRM_DELETE
    
    elif action == "edit":
        await query.message.reply_text("Qual a nova quantidade para este registro de falta?")
        return AWAIT_NEW_QUANTITY

async def confirm_delete_absence(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    absence_id = int(query.data.split('_')[-1])
    with SessionLocal() as db:
        absence = absence_service.get_absence_by_id(db, absence_id)
        subject_id = absence.subject.id
        absence_service.delete_absence_by_id(db, absence_id)
    
    await query.edit_message_text("Registro de falta excluído com sucesso.")
    query.data = f"mng_abs_subj_{subject_id}"
    return await list_absences_for_subject(update, context)

async def received_new_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        new_quantity = int(update.message.text)
        if new_quantity <= 0: raise ValueError
    except (ValueError, TypeError):
        await update.message.reply_text("Por favor, envie um número inteiro positivo.")
        return AWAIT_NEW_QUANTITY

    absence_id = context.user_data['absence_id_to_manage']
    with SessionLocal() as db:
        absence = absence_service.update_absence_quantity(db, absence_id, new_quantity)
        subject_id = absence.subject.id
    
    await update.message.reply_text("Quantidade de faltas atualizada com sucesso!")
    
    fake_update = type('Update', (), {'callback_query': type('CallbackQuery', (), {'data': f"mng_abs_subj_{subject_id}", 'answer': (lambda: None), 'message': update.message})()})()
    return await list_absences_for_subject(fake_update, context)


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
    )

def setup_absence_management_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("gerenciarfaltas", manage_absences_start),
            CallbackQueryHandler(manage_absences_start, pattern="^start_manage_absences$")
        ],
        states={
            SELECT_SUBJECT_TO_MANAGE: [CallbackQueryHandler(list_absences_for_subject, pattern="^mng_abs_subj_")],
            LIST_ABSENCES: [
                CallbackQueryHandler(select_absence_action, pattern="^select_absence_"),
                CallbackQueryHandler(handle_absence_action, pattern="^(edit_absence_|delete_absence_)"),
                CallbackQueryHandler(list_absences_for_subject, pattern="^mng_abs_subj_"),
            ],
            CONFIRM_DELETE: [
                CallbackQueryHandler(confirm_delete_absence, pattern="^confirm_delete_absence_"),
                CallbackQueryHandler(select_absence_action, pattern="^select_absence_"),
            ],
            AWAIT_NEW_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_new_quantity)],
        },
        fallbacks=[CommandHandler("cancelar", absence_cancel)],
        per_message=False,
    )
    
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
        message = "Você não tem matérias cadastradas para ver um relatório de faltas."
        if query: await query.edit_message_text(text=message)
        else: await update.message.reply_text(text=message)
        return

    message = "📊 *Relatório de Faltas:*\n\n"
    for subject in subjects:
        message += f"▪️ *{subject.name}:* {subject.total_absences} falta(s)\n"

    if query:
        # Edita a mensagem do menu para se transformar no relatório
        await query.edit_message_text(message, parse_mode='HTML')
    else:
        # Responde ao comando /faltas
        await update.message.reply_html(message)