import logging
from collections import defaultdict
from datetime import time, datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, filters, CallbackQueryHandler,
)
from bot.db.base import SessionLocal
from bot.services import user_service, subject_service, grade_service, activity_service

logger = logging.getLogger(__name__)

# --- Estados para CRIAÇÃO de matéria ---
NAME, PROFESSOR, DAY, ROOM, START_TIME, END_TIME, SEMESTRE = range(7)

# --- Estados para GERENCIAMENTO de matéria ---
SELECTING_ACTION, CONFIRMING_DELETE, SHOWING_EDIT_OPTIONS, AWAITING_NEW_VALUE = range(10, 14)

# --- Estados para RELATÓRIO de matéria ---
SELECT_SUBJECT_FOR_REPORT = range(20, 21)

# =============================================================================
# Seção 1: Handler de Conversa para /addmateria (Criação)
# =============================================================================

async def new_subject_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = "Ok, vamos cadastrar uma nova matéria.\nPrimeiro, qual é o nome da matéria? (Ex: Cálculo I)\n\nEnvie /cancelar para interromper."
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(text)
    else:
        await update.message.reply_text(text)
    return NAME

async def received_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['subject_name'] = update.message.text
    await update.message.reply_text(f"Nome da matéria: '{context.user_data['subject_name']}'.\nAgora, qual o nome do(a) professor(a)?")
    return PROFESSOR

async def received_professor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['professor_name'] = update.message.text
    keyboard = [["Segunda", "Terça", "Quarta"], ["Quinta", "Sexta", "Sábado"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Anotado. Agora escolha o dia da semana da aula:", reply_markup=reply_markup)
    return DAY

async def received_day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['day_of_week'] = update.message.text
    await update.message.reply_text("Dia definido. Qual a sala ou laboratório?", reply_markup=ReplyKeyboardRemove())
    return ROOM

async def received_room(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['room'] = update.message.text
    await update.message.reply_text("Sala anotada. Qual o horário de *início* da aula? (formato HH:MM, ex: 19:00)")
    return START_TIME

async def received_start_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['start_time'] = datetime.strptime(update.message.text, '%H:%M').time()
    except ValueError:
        await update.message.reply_text("Formato de hora inválido. Tente novamente (HH:MM).")
        return START_TIME
    await update.message.reply_text("Horário de início salvo. E qual o horário de *término*? (formato HH:MM, ex: 22:30)")
    return END_TIME

async def received_end_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['end_time'] = datetime.strptime(update.message.text, '%H:%M').time()
    except ValueError:
        await update.message.reply_text("Formato de hora inválido. Tente novamente (HH:MM).")
        return END_TIME
    await update.message.reply_text("Horários salvos. Em qual semestre você está cursando esta matéria? (ex: 1, 2, 3...)")
    return SEMESTRE

async def received_semestre(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['semestre'] = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Por favor, envie apenas o número do semestre.")
        return SEMESTRE
    
    telegram_user = update.effective_user
    data = context.user_data
    with SessionLocal() as db:
        user, _ = user_service.get_or_create_user(db, telegram_user.id, telegram_user.first_name, telegram_user.username)
        subject_service.create_subject(
            db=db, user=user, name=data['subject_name'], professor=data['professor_name'],
            day=data['day_of_week'], room=data['room'], start_time=data['start_time'],
            end_time=data['end_time'], semestre=data['semestre']
        )
    await update.message.reply_text(f"✅ Matéria '{data['subject_name']}' cadastrada com sucesso!")
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Operação cancelada.", reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END

# =============================================================================
# Seção 2: Handler de Comando para /minhasmaterias (Leitura)
# =============================================================================

async def list_subjects(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lista as matérias, garantindo que a sessão com o banco permaneça aberta."""
    query = update.callback_query
    if query:
        await query.answer()
        telegram_user = query.from_user
    else:
        telegram_user = update.effective_user

    message = "" # Inicializa a variável

    with SessionLocal() as db:
        user, _ = user_service.get_or_create_user(db, telegram_user.id, telegram_user.first_name, telegram_user.username)
        subjects = subject_service.get_subjects_by_user(db, user)

        if not subjects:
            message = "Você ainda não cadastrou nenhuma matéria. Use /addmateria para começar."
        else:
            subjects_by_day = defaultdict(list)
            for subject in subjects:
                subjects_by_day[subject.day_of_week].append(subject)

            weekdays = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"]
            message = "📅 *Sua Grade Horária Semanal:*\n\n"

            for day in weekdays:
                day_subjects = subjects_by_day.get(day, [])
                if day_subjects:
                    message += f"*{day.upper()}:*\n"
                    for subject in day_subjects:
                        start_str = subject.start_time.strftime('%H:%M') if subject.start_time else '--:--'
                        end_str = subject.end_time.strftime('%H:%M') if subject.end_time else '--:--'
                        message += f"   `{start_str}`-`{end_str}` 📚 *{subject.name}* (Sala: {subject.room})\n"
                        
                        # Este acesso agora também está dentro do 'with'
                        grades = grade_service.get_grades_by_subject(db, subject)
                        if grades:
                            grade_list = [f"{g.name}: *{g.value:.2f}*" for g in grades]
                            message += f"      *Notas:* {', '.join(grade_list)}\n"
                        
                        if subject.total_absences > 0:
                            message += f"      *Faltas:* {subject.total_absences}\n"
                    message += "\n"
    
    if query:
        await query.edit_message_text(message, parse_mode='HTML')
    else:
        await update.message.reply_html(message)    
    
# =============================================================================
# Seção 3: Handler de Conversa para /gerenciarmaterias (Edição/Exclusão)
# =============================================================================

# NOVOS ESTADOS para um fluxo de edição mais granular
SELECTING_ACTION, CONFIRMING_DELETE, SHOWING_EDIT_OPTIONS, AWAITING_NEW_VALUE = range(10, 14)


async def manage_subjects_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia o processo de gerenciamento, mostrando as matérias como botões."""
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
        text = "Você não tem matérias para gerenciar. Use /addmateria para adicionar uma."
        if query:
            # Edita a mensagem do menu para informar o usuário
            await query.edit_message_text(text=text)
        else:
            await update.message.reply_text(text)
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(s.name, callback_data=f"manage_{s.id}")] for s in subjects]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "Escolha uma matéria para gerenciar:"

    if query:
        # Edita a mensagem do menu para mostrar a lista de matérias
        await query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)
    
    return SELECTING_ACTION

async def select_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Callback para quando o usuário escolhe uma matéria. Mostra as opções de Edição/Exclusão."""
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
    await query.edit_message_text(f"Gerenciando a matéria: *{subject.name}*\nO que você deseja fazer?", reply_markup=reply_markup, parse_mode='Markdown')
    return SELECTING_ACTION

async def show_edit_options_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Mostra os dados atuais da matéria e os botões para editar cada campo."""
    query = update.callback_query
    await query.answer()

    subject_id = context.user_data.get('subject_id_to_manage')
    if not subject_id:
        # Pega o ID do callback se for a primeira vez
        subject_id = int(query.data.split('_')[1])
        context.user_data['subject_id_to_manage'] = subject_id

    with SessionLocal() as db:
        subject = subject_service.get_subject_by_id(db, subject_id)

    if not subject:
        await query.edit_message_text("Erro: Matéria não encontrada.")
        return ConversationHandler.END
    
    text = (
        f"📝 *Editando: {subject.name}*\n\n"
        f"▪️ *Professor:* {subject.professor}\n"
        f"▪️ *Dia da Semana:* {subject.day_of_week}\n"
        f"▪️ *Sala:* {subject.room}\n\n"
        "Selecione o campo que deseja alterar:"
    )
    keyboard = [
        [
            InlineKeyboardButton("Nome", callback_data=f"editfield_name"),
            InlineKeyboardButton("Professor", callback_data=f"editfield_professor"),
        ],
        [
            InlineKeyboardButton("Dia da Semana", callback_data=f"editfield_day_of_week"),
            InlineKeyboardButton("Sala", callback_data=f"editfield_room"),
        ],
        [InlineKeyboardButton("« Voltar", callback_data=f"manage_{subject_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    return SHOWING_EDIT_OPTIONS

async def select_field_to_edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe o campo a ser editado e pede o novo valor."""
    query = update.callback_query
    await query.answer()

    field_to_edit = query.data.split('_')[1]
    context.user_data['field_to_edit'] = field_to_edit

    # Se for o dia da semana, mostra o teclado de botões
    if field_to_edit == "day_of_week":
        keyboard = [["Segunda", "Terça", "Quarta"], ["Quinta", "Sexta", "Sábado"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await query.message.reply_text(f"Por favor, escolha o novo dia da semana:", reply_markup=reply_markup)
    else:
        # Para outros campos, apenas pede o texto
        field_map = {'name': 'nome', 'professor': 'nome do professor', 'room': 'sala'}
        await query.message.reply_text(f"Por favor, envie o novo valor para *{field_map[field_to_edit]}*:", parse_mode='Markdown')

    return AWAITING_NEW_VALUE

async def receive_field_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe o novo valor, atualiza no banco e volta ao menu de edição."""
    new_value = update.message.text
    field_to_edit = context.user_data.get('field_to_edit')
    subject_id = context.user_data.get('subject_id_to_manage')

    # Remove o teclado de dias da semana, se ele estiver visível
    await update.message.reply_text("Atualizando...", reply_markup=ReplyKeyboardRemove())

    with SessionLocal() as db:
        # Atualiza a matéria no banco de dados
        subject_service.update_subject(db, subject_id, {field_to_edit: new_value})
        
        # Busca a matéria novamente para obter todos os dados atualizados
        subject = subject_service.get_subject_by_id(db, subject_id)

    # --- Lógica para reenviar o menu de edição ---
    text = (
        f"✅ Campo atualizado com sucesso!\n\n"
        f"📝 *Editando: {subject.name}*\n\n"
        f"▪️ *Professor:* {subject.professor}\n"
        f"▪️ *Dia da Semana:* {subject.day_of_week}\n"
        f"▪️ *Sala:* {subject.room}\n\n"
        "Selecione outro campo para alterar ou volte para a lista."
    )
    keyboard = [
        [
            InlineKeyboardButton("Nome", callback_data=f"editfield_name"),
            InlineKeyboardButton("Professor", callback_data=f"editfield_professor"),
        ],
        [
            InlineKeyboardButton("Dia da Semana", callback_data=f"editfield_day_of_week"),
            InlineKeyboardButton("Sala", callback_data=f"editfield_room"),
        ],
        [InlineKeyboardButton("« Voltar", callback_data=f"manage_{subject_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Envia uma NOVA mensagem com o menu atualizado
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    # Mantém a conversa no estado de "mostrar opções de edição"
    return SHOWING_EDIT_OPTIONS

async def handle_delete_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processa a escolha de deletar (pede confirmação) ou voltar."""
    query = update.callback_query
    await query.answer()

    action, subject_id_str = query.data.split('_')
    subject_id = int(subject_id_str)

    if action == "delete":
        keyboard = [
            [InlineKeyboardButton("✅ Sim, tenho certeza", callback_data=f"confirmdelete_{subject_id}")],
            [InlineKeyboardButton("❌ Não, cancelar", callback_data=f"manage_{subject_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("⚠️ *ATENÇÃO:*\nTem certeza que deseja excluir esta matéria?", reply_markup=reply_markup, parse_mode='Markdown')
        return CONFIRMING_DELETE

async def confirm_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Deleta a matéria após confirmação."""
    query = update.callback_query
    await query.answer()
    
    subject_id = int(query.data.split('_')[1])
    with SessionLocal() as db:
        deleted = subject_service.delete_subject_by_id(db, subject_id)
    
    if deleted:
        await query.edit_message_text("Matéria excluída com sucesso.")
    else:
        await query.edit_message_text("Erro ao excluir a matéria.")
        
    context.user_data.clear()
    return ConversationHandler.END

async def back_to_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Função para o botão 'Voltar para a lista'. Edita a mensagem para mostrar a lista de matérias novamente."""
    query = update.callback_query
    await query.answer()

    # Pega o usuário a partir do 'callback_query'
    telegram_user = query.from_user

    # Busca as matérias do usuário
    with SessionLocal() as db:
        user = user_service.get_or_create_user(db, telegram_user.id, telegram_user.first_name, telegram_user.username)
        subjects = subject_service.get_subjects_by_user(db, user)

    if not subjects:
        await query.edit_message_text("Você não tem mais matérias para gerenciar.")
        return ConversationHandler.END

    # Monta o teclado com a lista de matérias
    keyboard = [[InlineKeyboardButton(s.name, callback_data=f"manage_{s.id}")] for s in subjects]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edita a mensagem atual para voltar a ser o menu inicial
    await query.edit_message_text("Escolha uma matéria para gerenciar:", reply_markup=reply_markup)
    
    # Retorna ao estado de "selecionando uma ação"
    return SELECTING_ACTION


async def manage_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Função de cancelamento geral para o gerenciamento."""
    await update.message.reply_text("Gerenciamento cancelado.", reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END


async def report_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia o fluxo de relatório, pedindo para o usuário escolher uma matéria."""
    telegram_user = update.effective_user
    with SessionLocal() as db:
        user, _ = user_service.get_or_create_user(db, telegram_user.id, telegram_user.first_name, telegram_user.username)
        subjects = subject_service.get_subjects_by_user(db, user)

    if not subjects:
        await update.message.reply_text("Você não tem matérias cadastradas para gerar um relatório.")
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(s.name, callback_data=f"report_subject_{s.id}")] for s in subjects]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Escolha uma matéria para ver o relatório detalhado:", reply_markup=reply_markup)
    return SELECT_SUBJECT_FOR_REPORT

async def show_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Busca todos os dados da matéria e exibe o relatório completo."""
    query = update.callback_query
    await query.answer()
    subject_id = int(query.data.split('_')[-1])

    with SessionLocal() as db:
        subject = subject_service.get_subject_by_id(db, subject_id)
        if not subject:
            await query.edit_message_text("Matéria não encontrada.")
            return ConversationHandler.END
        
        activities = activity_service.get_activities_by_subject(db, subject)
        grades = grade_service.get_grades_by_subject(db, subject)

    start_str = subject.start_time.strftime('%H:%M') if subject.start_time else 'N/A'
    end_str = subject.end_time.strftime('%H:%M') if subject.end_time else 'N/A'
    
    report_text = f"📊 *Relatório Completo: {subject.name}*\n\n"
    report_text += f"▪️ *Semestre:* {subject.semestre or 'Não definido'}\n"
    report_text += f"▪️ *Professor:* {subject.professor}\n"
    report_text += f"▪️ *Horário:* {subject.day_of_week}, das {start_str} às {end_str}\n"
    report_text += f"▪️ *Sala:* {subject.room}\n"
    report_text += f"▪️ *Total de Faltas:* {subject.total_absences}\n\n"
    report_text += "—" * 20 + "\n\n"

    report_text += "🗓️ *Agenda de Atividades:*\n"
    if not activities:
        report_text += "   - Nenhuma atividade cadastrada.\n"
    else:
        for act in activities:
            report_text += f"   • {act.due_date.strftime('%d/%m/%Y')}: {act.name}\n"
    report_text += "\n" + "—" * 20 + "\n\n"
    
    report_text += "🎓 *Notas Lançadas:*\n"
    if not grades:
        report_text += "   - Nenhuma nota lançada.\n"
    else:
        for grade in grades:
            report_text += f"   • {grade.name}: *{grade.value:.2f}*\n"

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
            SEMESTRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_semestre)],
        },
        fallbacks=[CommandHandler("cancelar", cancel)],
    )


def setup_management_handler() -> ConversationHandler:
    """Cria e configura o ConversationHandler para /gerenciarmaterias."""
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
                CallbackQueryHandler(back_to_list_callback, pattern="^back_to_list$"),
            ],
            SHOWING_EDIT_OPTIONS: [
                CallbackQueryHandler(select_field_to_edit_callback, pattern="^editfield_"),
                CallbackQueryHandler(select_action_callback, pattern="^manage_"), # Botão Voltar
            ],
            AWAITING_NEW_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_field_update),
            ],
            CONFIRMING_DELETE: [
                CallbackQueryHandler(confirm_delete_callback, pattern="^confirmdelete_"),
                CallbackQueryHandler(select_action_callback, pattern="^manage_"),
            ],
        },
        fallbacks=[CommandHandler("cancelar", manage_cancel)],
        per_message=False,
    )
    
def setup_report_handler() -> ConversationHandler:
    """Cria e configura o ConversationHandler para /relatorio."""
    return ConversationHandler(
        entry_points=[CommandHandler("relatorio", report_start)],
        states={
            SELECT_SUBJECT_FOR_REPORT: [CallbackQueryHandler(show_report, pattern="^report_subject_")]
        },
        fallbacks=[CommandHandler("cancelar", cancel)],
    )