# bot/core/dialogs.py
"""
Central de mensagens do bot: utilize constantes definidas abaixo e formate com .format() quando necessário.
A formatação padrão é HTML (<b> para negrito, <code> para monoespaçado).
"""

# =============================================================================
# GERAL, MENUS E AJUDA
# =============================================================================
WELCOME_NEW = (
    "Olá, {first_name}! Bem-vindo(a) ao J.O.V.I.S. 🤖\n\n"
    "Irei te auxiliar na organização dos seus estudos.\n\n"
    "Ainda estou em fase de testes, me perdoe por qualquer erro ou caso algo não funcionar corretamente.\n\n"
    "Se encontrar algum comportamento estranho, se algum comando ou botão não funcionar tire um print e me envie pelo comando /bug.\n\n"
    "Use os botões abaixo para navegar por algumas de minhas funcionalidades."
)
WELCOME_BACK = "Olá de volta, {first_name}! 👋\n\nO que temos pra hoje?"
OPERATION_CANCELED = "Operação cancelada."
BACK_TO_MAIN_MENU_PROMPT = "« Voltar ao Menu Principal"
SEPARATOR = "—" * 20 + "\n"

MENU_SUBJECTS = "📚 <b>Matérias</b>\n\nO que deseja fazer?"
MENU_ACTIVITIES = "🗓️ <b>Trabalhos e Provas</b>\n\nO que deseja fazer?"
MENU_ABSENCES = "✖️ <b>Faltas</b>\n\nO que deseja fazer?"
MENU_GRADES = "🎓 <b>Notas</b>\n\nO que deseja fazer?"
MENU_SUMMARIES = "⚡ <b>Resumos Rápidos</b>\n\nQual resumo você quer ver?"


# --- Resumos Rápidos (/hoje, /semana) ---
SUMMARY_TODAY_HEADER = "☀️ <b>Resumo para hoje, {date} ({weekday})</b>:\n\n"
TODAY_COURSES_HEADER = "📚 <b>Aulas de Hoje:</b>\n"
TODAY_NO_COURSES = "   - Nenhuma aula hoje. Aproveite!\n"
TODAY_COURSE_LINE = "   • <code>{start}</code>–<code>{end}</code>: <b>{name}</b> (Sala: {room})\n"

ACTIVITIES_FOR_TODAY_HEADER = "📌 <b>Entregas e Provas para Hoje:</b>\n"
NO_ACTIVITIES_TODAY = "   - Nenhuma entrega ou prova agendada para hoje!\n"
TODAY_ACTIVITY_LINE = "   {icon} <b>{name}</b> (Matéria: {subject_name})\n"

AGENDA_WEEK_HEADER = "🗓️ <b>Agenda para os próximos 7 dias (de {start} a {end})</b>:\n\n"
NO_ACTIVITIES_WEEK = "Nenhuma atividade agendada para esta semana. Que tranquilidade!"
WEEK_ACTIVITY_LINE = " • <b>{date_str}:</b> {icon} {name} ({subject_name})\n"


# Ajuda
HELP_TEXT = (
    "Olá! Sou seu mano JOVIS. Aqui está um resumo de tudo que posso fazer:\n\n"
    "💡 <b>Dica:</b> Tenho um menu interativo com atalhos para algumas funções. "
    "Basta enviar /start para acessá-lo a qualquer momento!\n\n"
    "<b>Comandos Diretos:</b>\n"
    "— — — — — — — — — —\n\n"
    "📚 <b>Matérias</b>\n"
    "• /grade - Exibe sua grade horária completa.\n"
    "• /addmateria - Cadastra uma nova matéria.\n"
    "• /gerenciarmaterias - Edita ou exclui matérias.\n"
    "• /relatorio - Gera um relatório detalhado de uma matéria.\n\n"
    "🗓️ <b>Trabalhos e Provas</b>\n"
    "• /calendario - Lista seus trabalhos e provas.\n"
    "• /addtrabalho - Adiciona um novo trabalho.\n"
    "• /addprova - Adiciona uma nova prova.\n"
    "• /gerenciartrabalhos - Edita ou exclui trabalhos.\n"
    "• /gerenciarprovas - Edita ou exclui provas.\n\n"
    "✖️ <b>Faltas e 🎓 Notas</b>\n"
    "• /faltei - Registra uma ou mais faltas.\n"
    "• /gerenciarfaltas - Edita ou exclui registros de faltas.\n"
    "• /addnota - Lança uma nova nota.\n"
    "• /gerenciarnotas - Edita ou exclui notas.\n\n"
    "⚙️ <b>Geral</b>\n"
    "• /start - Mostra o menu principal.\n"
    "• /help - Mostra esta mensagem de ajuda.\n"
    "• /cancelar - <b>(Importante!)</b> Interrompe qualquer operação.\n"
    "• /bug - Reportar um problema ou bug para o desenvolvedor."
)

# =============================================================================
# ERROS DE VALIDAÇÃO
# =============================================================================
ERROR_INVALID_TIME = "Formato de hora inválido. 😓 Tente novamente: <b>HH:MM</b>."
ERROR_INVALID_DATE = "Formato de data inválido. 😓 Tente novamente: <b>DD/MM/AAAA</b>."
ERROR_INVALID_SEMESTER = "Por favor, envie apenas o número do semestre."
ERROR_INVALID_NUMBER_POSITIVE = "Por favor, envie um número inteiro e positivo."
ERROR_INVALID_GRADE = "Valor inválido. 😓 Por favor, envie um número (ex: 7.5 ou 10)."
ERROR_NOT_FOUND = "Erro: O item que você tentou acessar não foi encontrado. Pode já ter sido excluído."

# =============================================================================
# MATÉRIAS (SUBJECTS)
# =============================================================================
SUBJECT_CREATE_ASK_NAME = "Ok, vamos cadastrar uma nova matéria.\nPrimeiro, qual é o nome da matéria? (Ex: Cálculo I)\n\nEnvie /cancelar para interromper."
SUBJECT_CREATE_ASK_PROFESSOR = "Nome da matéria: '<b>{subject_name}</b>'.\nAgora, qual o nome do(a) professor(a)?"
SUBJECT_CREATE_ASK_DAY = "Anotado. Agora escolha o dia da semana da aula:"
SUBJECT_CREATE_ASK_ROOM = "Dia definido. Qual a sala ou laboratório?"
SUBJECT_CREATE_ASK_START_TIME = "Sala anotada. Qual o horário de <b>início</b> da aula? (formato HH:MM, ex: 19:00)"
SUBJECT_CREATE_ASK_END_TIME = "Horário de início salvo. E qual o horário de <b>término</b>? (formato HH:MM, ex: 22:30)"
SUBJECT_CREATE_ASK_SEMESTER = "Horários salvos. Em qual semestre você está cursando esta matéria? (ex: 1, 2, 3...)"
SUBJECT_CREATE_SUCCESS = "✅ Matéria '<b>{subject_name}</b>' cadastrada com sucesso!"

SUBJECT_LIST_HEADER = "📅 <b>Sua Grade Horária Semanal:</b>\n\n"
SUBJECT_LIST_NO_SUBJECTS = "Você ainda não cadastrou nenhuma matéria. Use /addmateria para começar."
SUBJECT_LIST_DAY_HEADER = "<b>{day}:</b>\n"
SUBJECT_LIST_ITEM = (
    "   <code>{st}</code>–<code>{et}</code>  <b>{name}</b> - Prof.(a) {professor}\n"
    "   (Sala: {room})\n"
)


SUBJECT_LIST_GRADES_LINE = "       <i>Notas:</i> {grades}\n"
SUBJECT_LIST_ABSENCES_LINE = "       <i>Faltas:</i> {absences}\n"
SUBJECT_LIST_SEPARATOR = "—" * 20 + "\n"
SUBJECT_LIST_GRADES_PREFIX = "      <b>Notas:</b> {grades}\n"
SUBJECT_LIST_ABSENCES_PREFIX = "      <b>Faltas:</b> {absences}\n"

SUBJECT_MANAGE_PROMPT = "Escolha uma matéria para gerenciar:"
SUBJECT_MANAGE_NO_SUBJECTS = "Você não tem matérias para gerenciar. Use /addmateria para adicionar uma."
SUBJECT_MANAGE_ACTION_PROMPT = "Gerenciando a matéria: <b>{subject_name}</b>\nO que você deseja fazer?"
SUBJECT_EDIT_HEADER = "📝 <b>Editando: {subject_name}</b>\n\n▪️ <b>Professor:</b> {professor}\n▪️ <b>Horário:</b> {day_of_week}, das {start_str} às {end_str}\n▪️ <b>Sala:</b> {room}\n▪️ <b>Semestre:</b> {semestre}\n\nSelecione o campo que deseja alterar:"
SUBJECT_EDIT_ASK_NEW_VALUE = "Por favor, envie o novo valor para <b>{field_name}</b>:"
SUBJECT_EDIT_DAY_KEYBOARD = "Por favor, escolha o novo dia da semana:"
SUBJECT_EDIT_SUCCESS = "✅ Campo atualizado com sucesso!"
SUBJECT_DELETE_CONFIRM = "⚠️ <b>ATENÇÃO:</b>\nTem certeza que deseja excluir a matéria <b>{subject_name}</b>? Esta ação não pode ser desfeita e apagará todas as atividades, faltas e notas associadas."
SUBJECT_DELETE_SUCCESS = "Matéria <b>{subject_name}</b> foi excluída com sucesso."

REPORT_PROMPT = "Escolha uma matéria para ver o relatório detalhado:"
REPORT_NO_SUBJECTS = "Você não tem matérias cadastradas para gerar um relatório."
REPORT_HEADER = "📊 <b>Relatório Completo: {subject_name}</b>\n\n"
REPORT_SUBJECT_DETAILS = "▪️ <b>Semestre:</b> {semestre}\n▪️ <b>Professor:</b> {professor}\n▪️ <b>Horário:</b> {day_of_week}, das {start_str} às {end_str}\n▪️ <b>Sala:</b> {room}\n▪️ <b>Total de Faltas:</b> {total_absences}\n"
REPORT_ACTIVITIES_HEADER = "🗓️ <b>Agenda de Atividades:</b>\n"
REPORT_NO_ACTIVITIES = "   - Nenhuma atividade cadastrada.\n"
REPORT_ACTIVITY_ITEM = "   • {due_date}: {activity_name}\n"
REPORT_GRADES_HEADER = "🎓 <b>Notas Lançadas:</b>\n"
REPORT_NO_GRADES = "   - Nenhuma nota lançada.\n"
REPORT_GRADE_ITEM = "   • {grade_name}: <b>{grade_value}</b>\n"


# =============================================================================
# ATIVIDADES (TRABALHOS E PROVAS)
# =============================================================================
ACTIVITY_CREATE_PROMPT = "Vamos adicionar um(a) novo(a) <b>{activity_type}</b>.\nQual o nome? (Ex: Entrega da API, Prova P2)\n\nEnvie /cancelar para interromper."
ACTIVITY_CREATE_NO_SUBJECTS = "Você precisa ter pelo menos uma matéria cadastrada para adicionar uma atividade. Use /addmateria primeiro."
ACTIVITY_CREATE_ASK_SUBJECT = "Ok. Agora, a qual matéria este item pertence?"
ACTIVITY_CREATE_CONFIRM_SUBJECT_ASK_DATE = "Matéria '<b>{subject_name}</b>' selecionada.\n\nQual a data de entrega? Por favor, envie no formato <b>DD/MM/AAAA</b>."
ACTIVITY_CREATE_ASK_NOTES = "Data anotada! Você quer adicionar alguma observação? Se não, pode enviar 'não' ou 'pular'."
ACTIVITY_CREATE_SUCCESS = "✅ <b>{activity_type}</b> '{activity_name}' adicionado(a) com sucesso!"
ACTIVITY_LIST_HEADER = "🗓️ <b>Seu Calendário de Entregas e Provas:</b>\n\n"
ACTIVITY_LIST_NO_ACTIVITIES = "Você não tem nenhuma atividade na sua agenda. Use /addtrabalho ou /addprova para começar."
# ... (Adicionar aqui os textos de gerenciamento quando implementado)


# =============================================================================
# FALTAS (ABSENCES)
# =============================================================================
ABSENCE_CREATE_NO_SUBJECTS = "Você precisa ter matérias cadastradas para registrar uma falta. Use /addmateria."
ABSENCE_CREATE_ASK_SUBJECT = "Para qual matéria você deseja registrar a falta?\n\nEnvie /cancelar para interromper."
ABSENCE_CREATE_ASK_DATE = "Quando foi a falta? Clique no botão ou envie a data no formato <b>DD/MM/AAAA</b>."
ABSENCE_CREATE_DATE_SELECTED = "Data selecionada: {date}"
ABSENCE_CREATE_ASK_QUANTITY = "Entendido. Quantas aulas/faltas você perdeu nesse dia? (normalmente 1 ou 2)"
ABSENCE_CREATE_ASK_NOTES = "Deseja adicionar uma observação? (ex: 'atestado médico'). Se não, envie 'não' ou 'pular'."
ABSENCE_CREATE_SUCCESS = "✅ {quantity} falta(s) registrada(s) para <b>{subject_name}</b>.\nTotal atual: <b>{total_absences}</b> faltas."

ABSENCE_MANAGE_PROMPT = "Escolha uma matéria para ver o histórico de faltas:"
ABSENCE_MANAGE_NO_SUBJECTS = "Você não tem matérias para gerenciar faltas."
ABSENCE_MANAGE_NO_RECORDS = "Nenhum registro de falta encontrado para <b>{subject_name}</b>."
ABSENCE_MANAGE_HEADER = "Histórico de faltas para <b>{subject_name}</b> (Total: {total}):\n"
ABSENCE_MANAGE_ACTION_PROMPT = "O que deseja fazer com este registro de falta?"
ABSENCE_MANAGE_ASK_NEW_QUANTITY = "Qual a nova quantidade para este registro de falta?"
ABSENCE_MANAGE_DELETE_CONFIRM = "Tem certeza que deseja excluir este registro?"
ABSENCE_MANAGE_DELETE_SUCCESS = "Registro de falta excluído com sucesso."
ABSENCE_MANAGE_UPDATE_SUCCESS = "Quantidade de faltas atualizada com sucesso!"

ABSENCE_REPORT_HEADER = "📊 <b>Relatório de Faltas:</b>\n\n"
ABSENCE_REPORT_ITEM = "▪️ <b>{subject_name}:</b> {total_absences} falta(s)\n"
ABSENCE_REPORT_NO_SUBJECTS = "Você não tem matérias cadastradas para ver um relatório de faltas."

# =============================================================================
# NOTAS (GRADES)
# =============================================================================
# --- Criação (/addnota) ---
GRADE_CREATE_NO_SUBJECTS = "Você precisa ter matérias cadastradas para lançar uma nota. Use /addmateria."
GRADE_CREATE_ASK_SUBJECT = "Para qual matéria você quer lançar uma nota?\n\nEnvie /cancelar para interromper."
GRADE_CREATE_ASK_NAME = "Matéria selecionada. Qual o nome desta avaliação? (Ex: P1, Trabalho 1)"
GRADE_CREATE_ASK_VALUE = "Nome da avaliação definido. Agora, qual foi a nota que você tirou?\n\n(Use <b>ponto</b> para decimais, ex: 8.5)"
GRADE_CREATE_SUCCESS = "✅ Nota <b>{grade_value}</b> para '{grade_name}' lançada com sucesso na matéria <b>{subject_name}</b>!"

# --- Gerenciamento (/gerenciarnotas) ---
GRADE_MANAGE_NO_SUBJECTS = "Você não tem matérias para gerenciar notas."
GRADE_MANAGE_ASK_SUBJECT = "Escolha uma matéria para ver as notas lançadas:"
GRADE_MANAGE_NO_GRADES = "Nenhuma nota lançada para <b>{subject_name}</b>."
GRADE_MANAGE_LIST_HEADER = "Notas lançadas para <b>{subject_name}</b>:\n\n"
GRADE_MANAGE_ACTION_PROMPT = "O que deseja fazer com esta nota?"
GRADE_MANAGE_DELETE_CONFIRM = "Tem certeza que deseja excluir esta nota? Esta ação não pode ser desfeita."
GRADE_EDIT_ASK_NAME = "Qual o novo nome para esta avaliação? (Ex: P1, Trabalho Final)"
GRADE_EDIT_ASK_VALUE = "Nome atualizado. Agora, qual o novo valor da nota? (Ex: 8.5)"
GRADE_EDIT_SUCCESS = "✅ Nota atualizada com sucesso!"
GRADE_DELETE_SUCCESS = "Nota excluída com sucesso."

# Validações específicas do fluxo de notas
GRADE_CREATE_INVALID_VALUE = ERROR_INVALID_GRADE
GRADE_EDIT_INVALID_VALUE   = ERROR_INVALID_GRADE

# =============================================================================
# IMPORTAÇÃO (/import)
# =============================================================================
IMPORT_START_PROMPT = (
    "Olá! Esta é a função de importação em massa de matérias.\n\n"
    "Por favor, envie um arquivo `materias.json` contendo uma lista de suas matérias.\n\n"
    "<b>O formato do arquivo deve ser exatamente este:</b>\n"
    "{json_example}\n\n"
    "Envie o arquivo agora ou use /cancelar para sair."
)
IMPORT_INVALID_FILE_EXTENSION = "Por favor, envie um arquivo com a extensão `.json`."
IMPORT_PROCESSING_FILE = "Recebi seu arquivo! Processando..."
IMPORT_JSON_ERROR = "Erro ao ler o arquivo: {error}\nPor favor, verifique o formato e envie novamente."
IMPORT_JSON_NOT_A_LIST = "O JSON deve ser uma lista de matérias."
IMPORT_SUCCESS = "✅ <b>Importação concluída!</b>\n\n{count} matéria(s) cadastrada(s) com sucesso."
IMPORT_FAILURE = (
    "❌ <b>Ocorreram erros e nenhuma matéria foi importada.</b>\n\n"
    "Por favor, corrija os seguintes problemas no seu arquivo e envie novamente:\n"
    "{error_list}"
)