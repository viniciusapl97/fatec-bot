# Roadmap — Bot (Telegram)

Ver [`ROADMAP.md`](ROADMAP.md) para o índice geral entre frentes.

Última atualização: 2026-08-21.

## ✅ Feito

Revisão de código completa (2026-08-21) encontrou e corrigiu 4 bugs
críticos que quebravam o bot em produção:
- `dialogs.py` sem várias constantes referenciadas por
  `activity_handler.py` e `subject_handler.py` — `/gerenciartrabalhos` e
  `/gerenciarprovas` estavam 100% quebrados (`AttributeError`).
- `/cancelar` quebrado em `/broadcast`, `/lembrar` e `/bug` (fallback
  passava uma string do `dialogs` como callback do `CommandHandler` em vez
  de uma função).
- Hacks de `Update`/`CallbackQuery` falsos em `activity_handler.py` e
  `grade_handler.py` que quebravam ao recarregar a tela após editar uma
  atividade ou nota.

Depois da correção dos bugs, implementado nesta ordem:

1. Fuso horário (`America/Sao_Paulo`) aplicado via `Defaults(tzinfo=...)`
   — corrigiu o lembrete diário de prazos, que disparava no horário
   errado.
2. `conversation_timeout` (10 min) em todos os `ConversationHandler`s —
   evita que uma conversa abandonada fique presa pra sempre.
3. Persistência dos lembretes personalizados (`/lembrar`) — antes viviam
   só em memória e somem num restart; agora ficam na tabela `reminders` e
   são reagendados na inicialização (`main.py:reschedule_pending_reminders`).
4. `%` de frequência por matéria (campo opcional `total_classes` +
   `subject_service.get_attendance_info`) e média de notas
   (`grade_service.get_average`) — aparecem em `/faltas`, `/relatorio` e
   `/gerenciarnotas`.
5. `/exportar` — baixa um JSON com tudo do usuário (matérias, atividades,
   faltas, notas, lembretes pendentes).
6. Suíte de testes unitários (`tests/`, pytest, SQLite em memória)
   cobrindo toda a camada `bot/services/`.
7. `CLAUDE.md` e `docs/ROADMAP.md`.
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
11. Edição de horário de matéria em `/gerenciarmaterias` — a lógica de
    conversão/validação de `start_time`/`end_time` já existia em
    `receive_field_update` (não usada, faltavam os botões). Adicionados
    os botões "Horário de Início"/"Horário de Término" em
    `build_subject_edit_view`, e a edição agora passa pela mesma checagem
    de conflito do item 10 — `check_conflict_with_existing` ganhou o
    parâmetro `exclude_subject_id` pra a matéria não colidir consigo
    mesma.
12. Resumo semanal automático — job `send_weekly_summary_job`
    (`bot/jobs.py`) roda toda segunda às 08:00 (`job_queue.run_daily(...,
    days=(1,))`; atenção: no python-telegram-bot v20+ `days` é
    0-6=domingo-sábado, não a convenção antiga de segunda-domingo) e
    manda pra cada usuário cadastrado o mesmo resumo do `/semana`.
    Extraído `build_week_summary_message(db, user)` de `common.py` pra
    ser reaproveitado tanto pelo comando quanto pelo job.
13. `/notificacoes` — liga/desliga os avisos automáticos de prazo por
    usuário (`User.notifications_enabled`, default `True`). Comando +
    botão de alternância; `check_deadlines_job` pula quem desativou via
    `user_service.get_user_ids_with_notifications_disabled`. **Bônus: ao
    testar isso encontrei e corrigi um bug real e pré-existente** —
    `check_deadlines_job` chamava
    `activity_service.get_upcoming_activities`, mas essa função sempre
    esteve definida em `user_service.py`, não em `activity_service.py`. O
    job diário de lembretes de prazo vinha estourando `AttributeError`
    (engolido pelo APScheduler) toda vez que rodava — os lembretes de
    "vence amanhã"/"vence em 3 dias" nunca tinham sido entregues de
    verdade em produção. Corrigido.
14. `/exportarcalendario` — gera um `.ics` (iCalendar/RFC 5545) com os
    trabalhos e provas do usuário, pra importar no Google Agenda/Apple
    Calendário/Outlook. É um retrato do momento (snapshot baixável), não
    uma assinatura ao vivo — o bot não tem servidor HTTP público pra
    hospedar uma URL de calendário que os apps re-sincronizem sozinhos.
    Gerado à mão em `export_service.build_activities_ics` (escaping e
    "line folding" do RFC 5545 implementados na unha, sem dependência
    nova). **Bug real encontrado e corrigido**: a primeira versão do
    handler montava o `.ics` fora do `with SessionLocal()`, e como isso
    acessa `activity.subject.name` (lazy load), quebrava com
    `DetachedInstanceError` assim que a sessão fechava.
15. `/stats` pra admin — contagens gerais (`bot/services/stats_service.py`):
    usuários cadastrados, matérias, atividades (trabalhos/provas
    separados), registros de falta, notas lançadas, lembretes pendentes.
    **Nota de escopo:** `User` não guarda data de cadastro nem de último
    acesso, então "usuários ativos" aqui significa "total já cadastrado",
    não "ativo recentemente".
16. Horário de notificação configurável por usuário
    (`/horarionotificacao`) — grade de botões 0h-23h,
    `User.notification_hour` (default 9). Mudou a arquitetura do job de
    prazos: antes rodava uma vez por dia às 9h fixas pra todo mundo,
    agora roda de hora em hora (`run_repeating`) e filtra por dentro quem
    tem `notification_hour == hora_atual`.
17. Paginação em `/grade` e `/calendario` — **automática**, não muda nada
    pra quem tem poucas matérias/atividades (o caso comum): só entra em
    ação se a mensagem inteira não couber no limite de 4096 caracteres do
    Telegram. `/calendario` pagina por contagem fixa de itens
    (`ACTIVITIES_PER_PAGE = 10`); `/grade` pagina por **dia da semana**
    (`SUBJECT_DAYS_PER_PAGE = 2`) pra nunca cortar as matérias de um dia
    no meio entre duas páginas. Validado manualmente forçando 32 matérias
    e 62 atividades — nenhuma página gerada jamais ultrapassa 4096
    caracteres.
18. Migrations com Alembic — substitui `Base.metadata.create_all()`.
    Detalhes completos, incluindo o passo de adoção necessário no banco
    de dev que já existe, em
    [`specs/alembic-migrations.md`](specs/alembic-migrations.md).

Ver `git log` para o histórico completo de commits de cada item.

## 🔭 Pendente

- Testes de handler/integração (fora de escopo da suíte atual de
  propósito — exigem mockar bastante a API do `python-telegram-bot`; os
  `services/` concentram a lógica de negócio testável isoladamente, e são
  reaproveitados 1:1 pela API — ver [`roadmap-api.md`](roadmap-api.md)).
