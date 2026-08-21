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

Ver `git log` para o histórico completo de commits de cada item.

## 🐛 Bugs/gaps conhecidos, ainda não corrigidos

- **Edição de horário de matéria desabilitada.** `subject_handler.py` tem
  um comentário do dev original admitindo que os botões de editar
  `start_time`/`end_time` foram deixados de fora do menu de
  `/gerenciarmaterias` "para não causar erros". Só dá pra editar
  nome/professor/dia/sala/semestre/total de aulas.

## 🎯 Próximos passos sugeridos (alto valor, baixo esforço)

- **Conflito de horário no `/addmateria` manual.** A lógica já existe
  (`course_service.check_schedule_conflict`), hoje só é usada no onboarding
  `/fatec`. Cadastrar matéria manualmente num horário já ocupado não avisa
  nada.
- Corrigir o `/privacidade` fantasma (criar o comando ou tirar do `/help`).

## 🧭 Boa experiência de uso (médio prazo)

- Resumo semanal automático (mandar `/semana` sozinho toda segunda de
  manhã).
- Silenciar notificações automáticas de prazo (`/notificacoes on|off`).
- Sincronizar provas/trabalhos com o calendário do celular (exportar
  `.ics`).

## 🔭 Mais ambiciosas / longo prazo

- `/stats` pra admin (usuários ativos, matérias/atividades cadastradas).
- Horário de notificação configurável por usuário (hoje é fixo às 9h pra
  todo mundo).
- Paginação em `/grade`/`/calendario` pra quem acumular muitas
  matérias/atividades.
- Migrations com Alembic em vez de `Base.metadata.create_all()` — hoje
  qualquer mudança de coluna depende de mexer manualmente no banco em
  produção.
- Testes de handler/integração (fora de escopo da suíte atual de
  propósito — exigem mockar bastante a API do `python-telegram-bot`; os
  `services/` concentram a lógica de negócio testável isoladamente).

## Hospedagem

Ainda rodando localmente. Decisão em aberto (2026-08-21): o usuário quer
aproveitar o assunto pra estudar AWS, usando o free tier (EC2 t2/t3.micro +
RDS Postgres t3/t4g.micro, ambos elegíveis por 12 meses em conta nova).
Ainda não começou — avisou que "por enquanto não" quando perguntado se
queria seguir com o setup. Quando retomar, o plano combinado foi: criar
budget alert primeiro, depois IAM user próprio, EC2, RDS, rodar o bot como
systemd service, CloudWatch pros logs.
