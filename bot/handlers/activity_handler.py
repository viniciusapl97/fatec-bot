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
)

from bot.db.base import SessionLocal
from bot.services import user_service, subject_service, activity_service

logger = logging.getLogger(__name__)

# --- Estados para a conversa de CRIAÇÃO ---
A_NAME, A_SUBJECT, A_DUEDATE, A_NOTES = range(20, 24)

# --- Estados para a conversa de GERENCIAMENTO ---
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
    
    text = (
        f"Vamos adicionar um(a) novo(a) *{activity_type}*.\n"
        "Qual o nome? (Ex: Entrega da API, Prova P2)\n\n"
        "Envie /cancelar para interromper."
    )

    if query:
        await query.message.reply_text(text, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, parse_mode='Markdown')
        
    return A_NAME

async def received_activity_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['activity_name'] = update.message.text
    telegram_user = update.effective_user
    with SessionLocal() as db:
        user, _ = user_service.get_or_create_user(db, telegram_user.id, telegram_user.first_name, telegram_user.username)
        subjects = subject_service.get_subjects_by_user(db, user)

    if not subjects:
        await update.message.reply_text("Você precisa ter matérias cadastradas para adicionar uma atividade. Use /addmateria primeiro.")
        context.user_data.clear()
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(s.name, callback_data=f"link_subject_{s.id}")] for s in subjects]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Ok. Agora, a qual matéria este item pertence?", reply_markup=reply_markup)
    return A_SUBJECT

async def received_activity_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    subject_id = int(query.data.split('_')[2])
    context.user_data['subject_id'] = subject_id
    with SessionLocal() as db:
        subject = subject_service.get_subject_by_id(db, subject_id)
    await query.edit_message_text(f"Matéria '{subject.name}' selecionada.\n\nQual a data de entrega? Por favor, envie no formato *DD/MM/AAAA*.", parse_mode='Markdown')
    return A_DUEDATE

async def received_activity_due_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    date_str = update.message.text
    try:
        due_date_obj = datetime.strptime(date_str, "%d/%m/%Y").date()
        context.user_data['due_date'] = due_date_obj
    except ValueError:
        await update.message.reply_text("Formato de data inválido. 😓\nPor favor, envie novamente no formato *DD/MM/AAAA*.", parse_mode='Markdown')
        return A_DUEDATE
    await update.message.reply_text("Data anotada! Você quer adicionar alguma observação? Se não, pode enviar 'não' ou 'pular'.")
    return A_NOTES

async def received_activity_notes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    notes = update.message.text
    if notes.lower() in ['não', 'nao', 'n', 'pular']:
        notes = None

    data = context.user_data
    telegram_user = update.effective_user
    with SessionLocal() as db:
        user, _ = user_service.get_or_create_user(db, telegram_user.id, telegram_user.first_name, telegram_user.username)
        subject = subject_service.get_subject_by_id(db, data['subject_id'])
        activity_service.create_activity(
            db=db, user=user, subject=subject, name=data['activity_name'],
            due_date=data['due_date'], notes=notes, activity_type=data['activity_type']
        )
    await update.message.reply_text(f"✅ *{data['activity_type'].capitalize()}* '{data['activity_name']}' adicionado(a) com sucesso!")
    context.user_data.clear()
    return ConversationHandler.END

async def activity_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.edit_message_text("Operação cancelada.")
    else:
        await update.message.reply_text("Operação cancelada.")
    context.user_data.clear()
    return ConversationHandler.END

# =============================================================================
# Seção 2: Handler de Comando para /calendario (Leitura)
# =============================================================================

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

        if not activities:
            message = "Você não tem nenhuma atividade na sua agenda. Use /addtrabalho ou /addprova para começar."
        else:
            message = "🗓️ *Seu Calendário de Entregas e Provas:*\n\n"
            for activity in activities:
                icon = "📝" if activity.activity_type == 'trabalho' else "❗️"
                formatted_date = activity.due_date.strftime("%d/%m/%Y")
                
                message += f"{icon} *{activity.name}* ({activity.activity_type.capitalize()})\n"
                message += f"   • *Matéria:* {activity.subject.name}\n"
                message += f"   • *Data:* {formatted_date}\n"
                if activity.notes:
                    message += f"   • *Obs:* {activity.notes}\n"
                message += "—" * 20 + "\n\n"
    
    if query:
        await query.edit_message_text(message, parse_mode='HTML')
    else:
        await update.message.reply_html(message)

# =============================================================================
# Seção 3: Handler de Conversa para Gerenciamento (Editar/Excluir)
# =============================================================================

async def manage_activities_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Função de entrada para /gerenciartrabalhos e /gerenciarprovas (via comando ou botão)."""
    query = update.callback_query
    activity_type = ""

    if query:
        await query.answer()
        data = query.data
        activity_type = "trabalho" if "trabalhos" in data else "prova"
    else:
        command = update.message.text.split(' ')[0][1:]
        activity_type = "trabalho" if command == "gerenciartrabalhos" else "prova"
    
    context.user_data['activity_type_to_manage'] = activity_type
    
    telegram_user = update.effective_user or (query.from_user if query else None)
    with SessionLocal() as db:
        user, _ = user_service.get_or_create_user(db, telegram_user.id, telegram_user.first_name, telegram_user.username)
        activities = activity_service.get_activities_by_user_and_type(db, user, activity_type)

    if not activities:
        text = f"Você não tem nenhum(a) {activity_type} para gerenciar."
        if query: await query.edit_message_text(text)
        else: await update.message.reply_text(text)
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(f"{a.name} ({a.due_date.strftime('%d/%m')})", callback_data=f"mng_act_{a.id}")] for a in activities]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"Escolha um(a) *{activity_type}* para gerenciar:"

    if query: await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else: await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        
    return SELECT_ACTIVITY_ACTION

async def select_activity_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Mostra as opções de Edição/Exclusão para a atividade escolhida."""
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
    await query.edit_message_text(f"Gerenciando: *{activity.name}*\nO que você deseja fazer?", reply_markup=reply_markup, parse_mode='Markdown')
    return SELECT_ACTIVITY_ACTION

async def show_activity_edit_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Mostra os dados atuais da atividade e botões para editar cada campo."""
    query = update.callback_query
    await query.answer()
    activity_id = context.user_data['activity_id_to_manage']
    with SessionLocal() as db:
        activity = activity_service.get_activity_by_id(db, activity_id)
    
    text = (
        f"📝 *Editando: {activity.name}*\n\n"
        f"▪️ *Matéria:* {activity.subject.name}\n"
        f"▪️ *Data:* {activity.due_date.strftime('%d/%m/%Y')}\n"
        f"▪️ *Obs:* {activity.notes or 'Nenhuma'}\n\n"
        "Selecione o campo que deseja alterar:"
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
        [InlineKeyboardButton("« Voltar", callback_data=f"mng_act_{activity_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    return SHOWING_ACTIVITY_EDIT_OPTIONS

async def select_activity_field_to_edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe o campo a ser editado e pede o novo valor."""
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
        await query.edit_message_text("Por favor, escolha a nova matéria:", reply_markup=reply_markup)
    elif field_to_edit == "due_date":
        await query.message.reply_text("Por favor, envie a nova data no formato *DD/MM/AAAA*:", parse_mode='Markdown')
    else:
        field_map = {'name': 'nome', 'notes': 'observações'}
        await query.message.reply_text(f"Por favor, envie o novo valor para *{field_map[field_to_edit]}*:", parse_mode='Markdown')
    return AWAITING_ACTIVITY_NEW_VALUE

async def receive_activity_field_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe o novo valor, atualiza e volta ao menu de edição."""
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
                await update.message.reply_text("Formato de data inválido. 😓 Tente novamente: *DD/MM/AAAA*.", parse_mode='Markdown')
                return AWAITING_ACTIVITY_NEW_VALUE
        elif field_to_edit == 'notes' and new_value.lower() in ['não', 'nao', 'n', 'pular', 'remover']:
            new_value = None

    with SessionLocal() as db:
        activity_service.update_activity(db, activity_id, {field_to_edit: new_value})

    # Simula um clique de botão para voltar ao menu de edição
    message_to_send_from = update.message if not query else query.message
    fake_update = type('Update', (), {'callback_query': type('CallbackQuery', (), {'data': f"edit_activity_{activity_id}", 'answer': (lambda: None), 'from_user': update.effective_user, 'message': message_to_send_from})(), 'effective_user': update.effective_user})()
    return await show_activity_edit_options(fake_update, context)


async def handle_delete_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    activity_id = int(query.data.split('_')[-1])
    keyboard = [[
        InlineKeyboardButton("✅ Sim, excluir", callback_data=f"confirmdelete_activity_{activity_id}"),
        InlineKeyboardButton("❌ Cancelar", callback_data=f"mng_act_{activity_id}")
    ]]
    await query.edit_message_text("Tem certeza que deseja excluir este item?", reply_markup=InlineKeyboardMarkup(keyboard))
    return CONFIRM_ACTIVITY_DELETE

async def confirm_activity_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    activity_id = int(query.data.split('_')[-1])
    with SessionLocal() as db:
        activity_service.delete_activity_by_id(db, activity_id)
    await query.edit_message_text("Item excluído com sucesso.")
    context.user_data.clear()
    return ConversationHandler.END


# =============================================================================
# Seção 4: Funções de Setup que Montam os Handlers
# =============================================================================

def setup_activity_handler() -> ConversationHandler:
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
        },
        fallbacks=[CommandHandler("cancelar", activity_cancel)],
    )

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
                CallbackQueryHandler(select_activity_action_callback, pattern="^mng_act_"), # Botão Voltar
            ],
            AWAITING_ACTIVITY_NEW_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_activity_field_update),
                CallbackQueryHandler(receive_activity_field_update, pattern="^newsubjectid_"),
            ],
            CONFIRM_ACTIVITY_DELETE: [
                CallbackQueryHandler(confirm_activity_delete_callback, pattern="^confirmdelete_activity_"),
                CallbackQueryHandler(select_activity_action_callback, pattern="^mng_act_"), # Botão Cancelar
            ],
        },
        fallbacks=[CommandHandler("cancelar", activity_cancel)],
        per_message=False,
    )