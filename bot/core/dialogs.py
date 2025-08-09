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
    "Olá! Eu sou seu assistente de estudos. Aqui está um resumo de tudo que posso fazer:\n\n"
    "💡 <b>Dica Principal:</b> A melhor forma de me usar é através do menu interativo. "
    "Basta enviar /start para acessá-lo a qualquer momento!\n\n"
    "<b>Comandos Diretos:</b>\n"
    "— — — — — — — — — —\n\n"
    "🚀 <b>Configuração Rápida</b>\n"
    "• /fatec - Configura sua grade horária completa de um curso da Fatec S.B. de forma automática.\n\n"

    "📚 <b>Matérias</b>\n"
    "• /grade - Exibe sua grade horária completa.\n"
    "• /addmateria - Cadastra uma nova matéria manualmente.\n"
    "• /gerenciarmaterias - Permite editar ou excluir matérias.\n"
    "• /relatorio - Gera um relatório detalhado de uma matéria.\n\n"

    "🗓️ <b>Trabalhos e Provas</b>\n"
    "• /calendario - Lista todos os seus trabalhos e provas.\n"
    "• /addtrabalho - Adiciona um novo trabalho na sua agenda.\n"
    "• /addprova - Adiciona uma nova prova na sua agenda.\n"
    "• /gerenciartrabalhos - Edita ou exclui trabalhos.\n"
    "• /gerenciarprovas - Edita ou exclui provas.\n\n"

    "✖️ <b>Faltas e 🎓 Notas</b>\n"
    "• /faltei - Registra uma ou mais faltas.\n"
    "• /gerenciarfaltas - Edita ou exclui registros de faltas.\n"
    "• /addnota - Lança uma nova nota.\n"
    "• /gerenciarnotas - Edita ou exclui notas.\n\n"

    "⚡ <b>Resumos Rápidos</b>\n"
    "• /hoje - Mostra um resumo das aulas e atividades do dia.\n"
    "• /semana - Lista as atividades dos próximos 7 dias.\n\n"
    
    "⚙️ <b>Comandos Gerais</b>\n"
    "• /start - Mostra o menu principal.\n"
    "• /help - Mostra esta mensagem de ajuda.\n"
    "• /bug - Reportar um problema para o desenvolvedor.\n"
    "• /import - (Avançado) Cadastra matérias em massa a partir de um arquivo JSON.\n"
    "• /deletardados - Apaga todos os seus dados do bot.\n"
    "• /privacidade - Mostra a política de privacidade.\n"
    "• /cancelar - <b>(Importante!)</b> Interrompe qualquer operação."
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



# =============================================================================
# FLUXO FATEC (/fatec)
# =============================================================================
FATEC_ONBOARDING_START = "Olá, futuro(a) FATECano(a)! Vamos configurar sua grade horária.\n\nPrimeiro, escolha seu curso:"
FATEC_ONBOARDING_ASK_SHIFT = "Ótima escolha! Agora, qual o seu turno?"
FATEC_ONBOARDING_ASK_GRADE_TYPE = "Entendido. Como você prefere montar sua grade?\n\nA grade personalizada é ideal para quem tem DPs ou adiantou matérias."
FATEC_ONBOARDING_ASK_IDEAL_SEMESTER = "Perfeito! Agora, por favor, selecione o seu semestre:"
FATEC_ONBOARDING_PROCESSING = "Processando sua grade, um momento..."
FATEC_ONBOARDING_NO_IDEAL_GRADE = "Desculpe, não encontrei a grade ideal para o {semester}º semestre do seu curso/turno."
FATEC_ONBOARDING_IDEAL_SUCCESS = "✅ Sucesso! Sua grade com {count} matérias para o {semester}º semestre foi cadastrada. Use o comando /grade para visualizar."
FATEC_ONBOARDING_NO_CATALOG = "Desculpe, não encontrei o catálogo de matérias para seu curso/turno."
FATEC_ONBOARDING_CUSTOM_LIST_HEADER = "Certo! Abaixo está a lista de TODAS as matérias disponíveis para o seu curso.\n\n"
FATEC_ONBOARDING_CUSTOM_PROMPT = "Por favor, envie uma mensagem com os <b>IDs</b> das matérias que você irá cursar, separados por vírgula ou espaço (ex: 1, 5, 12, 18)."
FATEC_ONBOARDING_INVALID_IDS = "Formato de IDs inválido. Por favor, envie apenas os números separados por espaço ou vírgula."
FATEC_ONBOARDING_CONFLICT_ERROR = "{error}\n\nPor favor, escolha uma nova combinação de IDs."
FATEC_ONBOARDING_NO_CONFLICT_ASK_SEMESTER = "Ótima escolha! Nenhum conflito de horário encontrado.\n\nPara finalizar, em qual semestre você está? (Isto é opcional, envie 'pular' se não quiser informar)"
FATEC_ONBOARDING_INVALID_SEMESTER = "Semestre inválido. O cadastro será feito sem essa informação."
FATEC_ONBOARDING_FINALIZING_CUSTOM = "Finalizando o cadastro da sua grade personalizada..."
FATEC_ONBOARDING_CUSTOM_SUCCESS = "✅ Tudo pronto! Sua grade personalizada com {count} matérias foi cadastrada com sucesso. Use /grade para ver o resultado."




# =============================================================================
# EXCLUSÃO DE DADOS (/deletardados)
# =============================================================================
DELETE_DATA_WARNING = (
    "⚠️ <b>ATENÇÃO: AÇÃO IRREVERSÍVEL</b> ⚠️\n\n"
    "Você está prestes a apagar <b>TODOS</b> os seus dados do Jovis. "
    "Isso inclui sua grade horária, todas as atividades, faltas e notas cadastradas.\n\n"
    "Esta ação não pode ser desfeita.\n\n"
    "Para confirmar que você entende e deseja prosseguir, por favor, digite a frase exata abaixo:\n"
    "<code>excluir todos os meus dados</code>"
)
DELETE_DATA_CONFIRMATION_INVALID = "A confirmação está incorreta. A operação foi cancelada para sua segurança."
DELETE_DATA_SUCCESS = "Todos os seus dados foram permanentemente removidos. Obrigado por usar o Jovis. Adeus! 👋"



# =============================================================================
# COMANDOS DE ADMINISTRADOR
# =============================================================================
ADMIN_BROADCAST_START = (
    "<b>Modo Administrador: Transmissão</b>\n\n"
    "Por favor, envie a mensagem que você deseja transmitir para <b>TODOS</b> os usuários do bot.\n\n"
    "A mensagem pode conter formatação HTML. Use /cancelar para sair."
)
ADMIN_BROADCAST_CONFIRM = (
    "<b>Revisão da Mensagem de Transmissão:</b>\n\n"
    "— — — Mensagem Abaixo — — —\n"
    "{message}\n"
    "— — — Fim da Mensagem — — —\n\n"
    "Você tem certeza que deseja enviar esta mensagem para <b>{user_count}</b> usuário(s)?\n"
    "Esta ação não pode ser desfeita."
)
ADMIN_BROADCAST_SENDING = "Iniciando a transmissão... A mensagem está sendo enviada em segundo plano. Você receberá um relatório ao final."
ADMIN_BROADCAST_CANCELED = "Transmissão cancelada."
ADMIN_BROADCAST_REPORT = (
    "✅ <b>Relatório de Transmissão Concluído</b> ✅\n\n"
    "• <b>Sucessos:</b> {success_count}\n"
    "• <b>Falhas (usuários que bloquearam o bot):</b> {failure_count}"
)
ADMIN_SEND_USAGE = "Uso incorreto. Formato: /enviar <ID_DO_USUARIO> <mensagem>"
ADMIN_SEND_SUCCESS = "✅ Mensagem enviada com sucesso para o usuário {user_name} (ID: {user_id})."
ADMIN_SEND_FAILURE_NOT_FOUND = "❌ Falha: Usuário com ID {user_id} não encontrado no banco de dados."
ADMIN_SEND_FAILURE_BLOCKED = "❌ Falha: Não foi possível enviar a mensagem. O usuário {user_name} (ID: {user_id}) provavelmente bloqueou o bot."
ADMIN_SEND_FAILURE_GENERAL = "❌ Falha: Ocorreu um erro inesperado ao tentar enviar a mensagem para o usuário {user_id}."


# =============================================================================
# LEMBRETES (REMINDERS)
# =============================================================================

# --- Lembretes Automáticos de Prazos ---
REMINDER_AUTOMATIC_HEADER = "Ei! Tenho alguns lembretes importantes para você:\n\n"
REMINDER_AUTOMATIC_TOMORROW = "🔔 <b>Atenção, vence AMANHÃ:</b> {activity_type} '<b>{activity_name}</b>' (Matéria: {subject_name})"
REMINDER_AUTOMATIC_3_DAYS = "🔔 <b>Lembrete para daqui a 3 dias:</b> {activity_type} '<b>{activity_name}</b>' (Matéria: {subject_name})"

# --- Lembretes Personalizados (/lembrar) ---
REMINDER_CUSTOM_ASK_MESSAGE = "Ok, vamos criar um lembrete. Primeiro, me diga: <b>o que</b> você quer que eu te lembre?"
REMINDER_CUSTOM_ASK_TIME = "Entendido. Agora, <b>quando</b> você quer ser lembrado? (Ex: em 1 hora, amanhã às 10:30, 25/12/2025 18:00)"
REMINDER_CUSTOM_ERROR_TIME = "Desculpe, não consegui entender essa data/hora. Tente ser mais específico, como 'amanhã às 14h'."
REMINDER_CUSTOM_SUCCESS = "✅ Certo! Agendei um lembrete para '<b>{reminder_message}</b>' em {reminder_datetime}."
REMINDER_CUSTOM_NOTIFICATION = "🔔 <b>Lembrete:</b> {reminder_message}"


