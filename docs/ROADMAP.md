# Roadmap

Mapa do que já foi feito e do que ainda falta no Jovis. Mantido manualmente
entre sessões — atualize esta lista ao concluir ou decidir adiar algo.

Última atualização: 2026-08-21.

## ✅ Feito

Revisão de código completa (2026-08-21) encontrou e corrigiu 4 bugs críticos
que quebravam o bot em produção:
- `dialogs.py` sem várias constantes referenciadas por `activity_handler.py`
  e `subject_handler.py` — `/gerenciartrabalhos` e `/gerenciarprovas`
  estavam 100% quebrados (`AttributeError`).
- `/cancelar` quebrado em `/broadcast`, `/lembrar` e `/bug` (fallback
  passava uma string do `dialogs` como callback do `CommandHandler` em vez
  de uma função).
- Hacks de `Update`/`CallbackQuery` falsos em `activity_handler.py` e
  `grade_handler.py` que quebravam ao recarregar a tela após editar uma
  atividade ou nota.

Depois da correção dos bugs, implementado nesta ordem:
1. Fuso horário (`America/Sao_Paulo`) aplicado via `Defaults(tzinfo=...)` —
   corrigiu o lembrete diário de prazos, que disparava no horário errado.
2. `conversation_timeout` (10 min) em todos os `ConversationHandler`s —
   evita que uma conversa abandonada fique presa pra sempre.
3. Persistência dos lembretes personalizados (`/lembrar`) — antes viviam só
   em memória e somem num restart; agora ficam na tabela `reminders` e são
   reagendados na inicialização (`main.py:reschedule_pending_reminders`).
4. `%` de frequência por matéria (campo opcional `total_classes` +
   `subject_service.get_attendance_info`) e média de notas
   (`grade_service.get_average`) — aparecem em `/faltas`, `/relatorio` e
   `/gerenciarnotas`.
5. `/exportar` — baixa um JSON com tudo do usuário (matérias, atividades,
   faltas, notas, lembretes pendentes).
6. Suíte de testes unitários (`tests/`, pytest, SQLite em memória) cobrindo
   toda a camada `bot/services/` — 70 testes.
7. `CLAUDE.md` e `docs/ROADMAP.md` (este arquivo).
8. `/meuslembretes` — lista os lembretes pendentes do usuário com um botão
   de cancelar cada um; ao cancelar, remove tanto o registro no banco
   quanto o job agendado em memória (`job_queue.get_jobs_by_name` +
   `schedule_removal()`), senão o lembrete dispararia mesmo cancelado.
9. `/privacidade` — implementado de verdade (antes só era citado no
   `/help`, sem handler). Texto em `dialogs.PRIVACY_POLICY_TEXT`,
   informativo, não é uma política jurídica formal — revisar/atualizar se
   o que o bot coleta ou compartilha mudar.
10. Conflito de horário no `/addmateria` manual — nova
    `subject_service.check_conflict_with_existing` (mesma lógica de
    sobreposição do `course_service.check_schedule_conflict`, mas
    comparando com as matérias já cadastradas do usuário, não com o
    catálogo). Se colidir, avisa qual matéria conflita e pede um novo
    horário de início (volta pro estado `START_TIME` da conversa).
    4 testes novos em `tests/test_subject_service.py`.
11. Edição de horário de matéria em `/gerenciarmaterias` — a lógica de
    conversão/validação de `start_time`/`end_time` já existia em
    `receive_field_update` (não usada, faltavam os botões). Adicionados
    os botões "Horário de Início"/"Horário de Término" em
    `build_subject_edit_view`, e a edição agora passa pela mesma checagem
    de conflito do item 10 — `check_conflict_with_existing` ganhou o
    parâmetro `exclude_subject_id` pra a matéria não colidir consigo
    mesma. 2 testes novos.
12. Resumo semanal automático — job `send_weekly_summary_job`
    (`bot/jobs.py`) roda toda segunda às 08:00 (`job_queue.run_daily(...,
    days=(1,))`; atenção: no python-telegram-bot v20+ `days` é
    0-6=domingo-sábado, não a convenção antiga de segunda-domingo) e manda
    pra cada usuário cadastrado o mesmo resumo do `/semana`. Extraído
    `build_week_summary_message(db, user)` de `common.py` pra ser
    reaproveitado tanto pelo comando quanto pelo job.
13. `/notificacoes` — liga/desliga os avisos automáticos de prazo por
    usuário (`User.notifications_enabled`, default `True`). Comando +
    botão de alternância; `check_deadlines_job` pula quem desativou via
    `user_service.get_user_ids_with_notifications_disabled`. **Bônus: ao
    testar isso encontrei e corrigi um bug real e pré-existente** —
    `check_deadlines_job` chamava `activity_service.get_upcoming_activities`,
    mas essa função sempre esteve definida em `user_service.py`, não em
    `activity_service.py`. Ou seja, o job diário de lembretes de prazo
    vinha estourando `AttributeError` (e sendo engolido pelo
    APScheduler) toda vez que rodava — os lembretes de "vence amanhã" /
    "vence em 3 dias" nunca tinham sido entregues de verdade em
    produção. Corrigido trocando a chamada para `user_service.get_upcoming_activities`.
    3 testes novos em `tests/test_user_service.py`.
14. `/exportarcalendario` — gera um `.ics` (iCalendar/RFC 5545) com os
    trabalhos e provas do usuário, pra importar no Google Agenda/Apple
    Calendário/Outlook. É um retrato do momento (snapshot baixável), não
    uma assinatura ao vivo — o bot não tem servidor HTTP público pra
    hospedar uma URL de calendário que os apps re-sincronizem sozinhos.
    Gerado à mão em `export_service.build_activities_ics` (sem dependência
    nova: escaping e "line folding" do RFC 5545 implementados na unha),
    validado de verdade parseando o arquivo gerado com a lib `icalendar`
    (só pra conferência, não é dependência do projeto). **Bug real
    encontrado e corrigido no processo**: a primeira versão do handler
    (`export_handler.py:export_calendar`) montava o `.ics` FORA do
    `with SessionLocal()`, e como isso acessa `activity.subject.name`
    (lazy load), quebrava com `DetachedInstanceError` assim que a sessão
    fechava — corrigido movendo a montagem do `.ics` pra dentro do bloco
    da sessão. 4 testes novos em `tests/test_export_service.py`.
15. `/stats` pra admin — contagens gerais (`bot/services/stats_service.py`):
    usuários cadastrados, matérias, atividades (trabalhos/provas
    separados), registros de falta, notas lançadas, lembretes pendentes.
    **Nota de escopo:** `User` não guarda data de cadastro nem de último
    acesso, então "usuários ativos" aqui significa "total já cadastrado",
    não "ativo recentemente" — não dá pra medir isso sem adicionar uma
    coluna de timestamp e passar a atualizá-la a cada interação (fica
    como possível refinamento futuro). Registrado em `setup_admin_handlers()`
    junto com `/broadcast`/`/enviar`, protegido por `@admin_only`. 2 testes
    novos em `tests/test_stats_service.py`.
16. Horário de notificação configurável por usuário
    (`/horarionotificacao`) — grade de botões 0h-23h,
    `User.notification_hour` (default 9). Isso mudou a arquitetura do job
    de prazos: antes `check_deadlines_job` rodava **uma vez por dia** às
    9h fixas pra todo mundo (`run_daily`); agora roda **de hora em hora**
    (`run_repeating(..., interval=timedelta(hours=1))`) e filtra por
    dentro quem tem `notification_hour == hora_atual` via
    `user_service.get_user_ids_with_notification_hour`. 3 testes novos em
    `tests/test_user_service.py`.

    ⚠️ **Migração pendente em produção**: assim como `notifications_enabled`
    (item 13), a coluna `notification_hour` só é criada automaticamente em
    bancos novos via `create_all()`. Numa instância já rodando é preciso
    `ALTER TABLE users ADD COLUMN notification_hour INTEGER NOT NULL DEFAULT 9;`
    antes do deploy — reforça por que Alembic (ver abaixo) vale a pena.
17. Paginação em `/grade` e `/calendario` — **automática**, não muda nada
    pra quem tem poucas matérias/atividades (o caso comum): só entra em
    ação se a mensagem inteira não couber no limite de 4096 caracteres do
    Telegram (checado contra um limiar conservador de 3500, com folga pro
    rodapé "Página X de Y" + botões). `/calendario` pagina por contagem
    fixa de itens (`ACTIVITIES_PER_PAGE = 10`); `/grade` pagina por **dia
    da semana** (`SUBJECT_DAYS_PER_PAGE = 2`) pra nunca cortar as matérias
    de um dia no meio entre duas páginas. Mesmo padrão de botões
    Anterior/Próxima já usado no onboarding do `/fatec`.

    Não cobri essas duas funções (`build_subject_list_view`,
    `build_activity_list_view`) na suíte pytest — mantendo a política já
    documentada de só testar `services/` com unidade automatizada — mas
    validei manualmente de forma rigorosa: forcei 32 matérias e 62
    atividades, naveguei por todas as páginas geradas conferindo que
    nenhuma jamais ultrapassa 4096 caracteres, e testei os handlers
    completos (comando + callback) ponta a ponta.
18. Migrations com Alembic (`migrations/`) — substitui
    `Base.metadata.create_all()`, que foi removido de `main.py` e
    `seed_db.py`. `migrations/env.py` lê a `DATABASE_URL` de
    `bot.core.settings` em runtime (nada hardcoded em `alembic.ini`).
    Gerada a migration baseline (`migrations/versions/6cde7bf58518_*.py`)
    cobrindo as 7 tabelas atuais. `requirements.txt` ganhou `alembic` e foi
    convertido de UTF-16 pra UTF-8 nesse processo (ver nota abaixo).

    ⚠️ **Passo único de adoção necessário no banco de dev/produção que já
    existe** (o que você já está rodando localmente): em vez de
    `alembic upgrade head`, rode `alembic stamp head` na primeira vez —
    isso marca o banco como atualizado sem tentar recriar tabelas que já
    existem. Depois desse passo único, é sempre `alembic upgrade head`
    normalmente. Resolve de vez os dois `ALTER TABLE` manuais pendentes
    dos itens 13 e 16 (`notifications_enabled`, `notification_hour`) — a
    migration baseline já inclui as duas colunas, então `stamp head`
    também cobre esse débito.

    Validado de ponta a ponta contra um Postgres real (container Docker
    `postgres:16-alpine`, já removido): `alembic upgrade head` do zero →
    `alembic check` sem diferença pendente → `alembic downgrade base`
    limpo → simulei o estado atual do usuário (tabelas via `create_all()`,
    sem Alembic) → `alembic stamp head` não tocou nos dados e `alembic
    check` continuou sem diferença → rodei operações reais dos `services/`
    (criar usuário, matéria, atividade, falta, nota, lembrete, calcular
    frequência) direto sobre o schema criado pela migration, tudo
    funcionando. Suíte pytest (88 testes, SQLite) não usa `main.py`/
    `seed_db.py` diretamente, então não foi afetada.

    **Nota sobre `requirements.txt`**: estava em UTF-16 (provavelmente
    `pip freeze` no PowerShell do Windows) — ao tentar só adicionar uma
    linha, a ferramenta de edição preservou a codificação original e
    quebrou o `pip` (erro "Invalid requirement" com bytes `\x00` literais
    no meio do nome do pacote). Precisei reescrever o arquivo via shell
    (heredoc) pra forçar UTF-8. Detalhe registrado no `CLAUDE.md` pra não
    se repetir.

Ver `git log` para o histórico completo de commits de cada item.

## 🔭 Mais ambiciosas / longo prazo

- Testes de handler/integração (fora de escopo da suíte atual de
  propósito — exigem mockar bastante a API do `python-telegram-bot`; os
  `services/` concentram a lógica de negócio testável isoladamente).

## 💭 Em standby: frontend web + app Android/iOS

Ideia discutida em 2026-08-21, guardada pra depois — usuário pediu explicitamente
pra só anotar, sem implementar nada por enquanto. Evoluiu ao longo da conversa:
começou como "só um site" → depois "site + widget Android" → decisão final foi
"site + app completo (React Native), com widget, iOS talvez um dia".

### A base: API por cima de `bot/services/`
Toda a regra de negócio já está isolada em `bot/services/`, sem nenhuma
dependência do Telegram — dá pra expor esses mesmos services por trás de uma
API (ex.: FastAPI) sem reescrever a lógica. **Isso é o que o site e o app têm
em comum** — a UI de cada um é separada (ver stack abaixo), só a API é
compartilhada. Comece por aqui, independente de qual cliente (site ou app)
vier primeiro.

### Stack decidida
- **Site**: React.
- **App**: React Native, via Expo (facilita o build local/sideload sem conta
  de desenvolvedor). Android primeiro; iOS "um dia" fica bem mais barato de
  adicionar depois por já estar no React Native, em vez de começar do zero em
  Swift futuramente.
- **Widget de tela inicial** (o motivo original de cogitar um app nativo): o
  motor JS do React Native roda dentro do processo do app — um widget é
  renderizado pelo *sistema operacional* fora desse processo, então **sempre
  vai precisar de uma peça nativa**, mesmo com React Native:
  - Android: lib `react-native-android-widget` — desenha o layout do widget
    em JSX, ela compila pra views nativas em build time. É a melhor opção
    atual pra esse cenário, não é "rodar JS dentro do widget".
  - iOS (se um dia acontecer): a Apple exige SwiftUI pra widgets, sem exceção
    — não existe bridge de React Native pra isso. Não tem como fugir de Swift
    nessa parte específica, mesmo com o app todo em React Native.
- **React Native Web** é uma opção pra unificar o código de UI entre site e
  app (usado em produção por apps grandes, ex. o X/Twitter novo) — mas não é
  o ponto de partida recomendado. Começar com React puro no site e React
  Native no app (compartilhando só os tipos/chamadas de API) é mais simples;
  migrar pra RN Web depois é uma opção, não um requisito.

### Autenticação — diferente pro site e pro app
- **Site**: como o bot serve qualquer usuário do Telegram (não é só de uso
  pessoal), o caminho certo é o **Telegram Login Widget** — usuário clica
  "Entrar com Telegram", o Telegram autentica e devolve um payload assinado
  (`user_id`, nome, username, foto) pro backend validar o hash. Zero senha
  nova pra gerenciar, e o `user_id` já bate com `User.user_id` no banco.
- **App/widget**: como esse app é só pra uso pessoal (sideload, sem loja), não
  vale a pena replicar o fluxo de Login Widget — mais simples é o bot gerar um
  **token de acesso pessoal** (ex. comando `/tokendeacesso`) vinculado ao seu
  `user_id`, colado uma vez na configuração do app.

### Estimativa por nível de ambição
- MVP somente-leitura (login + ver grade/notas/faltas/frequência/calendário),
  só no site: alguns fins de semana.
- Paridade completa (criar/editar/apagar tudo, igual ao bot) no site e/ou no
  app: várias semanas, part-time — o app soma tempo extra se React
  Native/Expo for novidade.
- Widget Android funcionando (`react-native-android-widget`): escopo pequeno
  uma vez que a API já existe — não precisa esperar o app inteiro ficar
  pronto pra fazer o widget.
- Design autoral + gráficos de evolução + iOS + tempo real ("muito foda"):
  meses — a parte mais aberta, sem teto.

### Recomendação quando retomar
1. API primeiro (FastAPI sobre `bot/services/`), independente de qual
   cliente vem depois.
2. App Android (React Native/Expo) com o essencial (ver/gerenciar
   grade, atividades, faltas, notas) + o widget — é o que motivou a
   conversa, então é o que traz retorno mais rápido.
3. Site como consumidor adicional da mesma API, quando fizer sentido.
4. iOS e unificação de UI (React Native Web) só depois de validar o resto.

## Hospedagem

Ainda rodando localmente. Decisão em aberto (2026-08-21): o usuário quer
aproveitar o assunto pra estudar AWS, usando o free tier (EC2 t2/t3.micro +
RDS Postgres t3/t4g.micro, ambos elegíveis por 12 meses em conta nova).
Ainda não começou — avisou que "por enquanto não" quando perguntado se
queria seguir com o setup. Quando retomar, o plano combinado foi: criar
budget alert primeiro, depois IAM user próprio, EC2, RDS, rodar o bot como
systemd service, CloudWatch pros logs.
