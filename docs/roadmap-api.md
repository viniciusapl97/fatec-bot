# Roadmap — API (`api/`)

Ver [`ROADMAP.md`](ROADMAP.md) para o índice geral entre frentes, e
[`specs/api-design.md`](specs/api-design.md) para as decisões de design
(autenticação, separação de schemas, pegadinhas de teste encontradas).

Última atualização: 2026-08-21.

## ✅ Feito

1. **Primeira fatia da API** (2026-08-21) — FastAPI expondo
   `bot/services/` por HTTP, sem duplicar lógica nenhuma:
   - Autenticação por token de acesso pessoal. Novo model `AccessToken`
     (`bot/db/models.py`), comandos `/tokendeacesso` (gera, mostra uma
     vez só) e `/revogartokens` (invalida todos de uma vez) no bot.
     Migration `e00d525f47d4_adiciona_access_tokens`.
   - Endpoints: `GET /health` (sem auth), `GET /me`, `GET /subjects`.
   - `api/deps.py` (dependências compartilhadas `get_db`/`get_current_user`),
     `api/schemas.py` (modelos Pydantic de resposta).
   - 12 testes novos (`tests/test_access_token_service.py`,
     `tests/test_api.py`).
2. **Mais endpoints de leitura** (2026-08-21):
   - `GET /activities` — aceita `?activity_type=trabalho|prova`.
   - `GET /absences` — nova `absence_service.get_absences_by_user` (só
     existia por matéria).
   - `GET /grades`.
   - Os três embutem `subject_name` na resposta (montado no router, não é
     atributo direto do model).
   - 9 testes novos (2 em `tests/test_absence_service.py`, 7 em
     `tests/test_api.py`, incluindo o caso que expôs o bug de isolamento
     de teste documentado em `specs/api-design.md`).

Ver `git log` para o histórico completo de commits de cada item.

## 🎯 Próximos passos

- **Frequência/média por matéria** — reaproveitar
  `subject_service.get_attendance_info` / `grade_service.get_average`,
  ainda não exposto. Provavelmente como `GET /subjects/{id}/attendance` e
  embutido na resposta de notas por matéria, não achatado nos endpoints
  de listagem que já existem.
- **Endpoints de escrita** (criar/editar/apagar matéria, atividade,
  falta, nota) — a "paridade completa" do app com o bot depende disso.
- **Telegram Login Widget** — autenticação pro site (diferente do token
  pessoal usado pelo app), ver
  [`specs/frontend-web-and-app.md`](specs/frontend-web-and-app.md). Só
  faz sentido quando o site começar de verdade.
- Decidir se listagens ganham paginação real — a API não tem o limite de
  4096 caracteres do Telegram, mas listas grandes ainda merecem
  paginação por performance/UX.

## Lembrete operacional

Toda vez que um model novo for adicionado (ex.: `AccessToken`), precisa de
migration — ver [`specs/alembic-migrations.md`](specs/alembic-migrations.md).
