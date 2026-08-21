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
3. **Frequência e notas por matéria** (2026-08-21):
   - `GET /subjects/{id}/attendance` — reaproveita
     `subject_service.get_attendance_info`; campos de percentual/faltas
     restantes ficam `null` se a matéria ainda não tem `total_classes`
     definido (mesma semântica do bot).
   - `GET /subjects/{id}/grades` — lista de notas da matéria + média
     (`grade_service.get_average`), embutidas num único payload em vez de
     achatadas na listagem geral de `/grades`.
   - Ambos checam posse da matéria (`subject.user_id == user.user_id`) e
     retornam 404 (não 403) tanto pra matéria inexistente quanto pra
     matéria de outro usuário, pra não vazar quais IDs existem.
   - 10 testes novos em `tests/test_api.py`.
4. **Endpoints de escrita** (2026-08-21) — POST/PATCH/DELETE pras 4
   entidades, paridade completa de CRUD com o bot:
   - Matérias: `POST /subjects`, `PATCH /subjects/{id}`,
     `DELETE /subjects/{id}`. Checa conflito de horário no mesmo dia (409),
     igual `/addmateria`/edição no bot — só quando dia+início+fim
     resultantes (após o merge do PATCH com o valor atual) estão todos
     definidos. `PATCH` usa `exclude_unset` do Pydantic pra atualizar só os
     campos enviados, distinguindo "campo omitido" de "campo enviado como
     `null`" (usado pra limpar `total_classes`).
   - Atividades: `POST /activities`, `PATCH /activities/{id}` (inclui
     mover pra outra matéria via `subject_id`), `DELETE /activities/{id}`.
     `activity_type` não é editável (mesma regra do bot — é fixado na
     criação).
   - Faltas: `POST /absences`, `PATCH /absences/{id}` (só `quantity`,
     mesma limitação do bot), `DELETE /absences/{id}` — os três
     recalculam `Subject.total_absences` via `absence_service` (não
     duplicado no router).
   - Notas: `POST /grades`, `PATCH /grades/{id}` (nome e valor juntos,
     mesma assinatura de `grade_service.update_grade`), `DELETE
     /grades/{id}`.
   - Todo endpoint que recebe `subject_id` (no corpo ou na URL) valida
     posse com o novo `api/deps.get_owned_subject` — 404 se a matéria não
     existir ou for de outro usuário. Movido de `subjects.py` pra
     `deps.py` porque activities/absences/grades passaram a precisar da
     mesma checagem.
   - 49 testes de API no total agora (`tests/test_api.py`), cobrindo
     autenticação, posse, validação (dia da semana inválido, quantidade
     ≤0, nota negativa) e conflito de horário.
5. **Telegram Login Widget** (2026-08-21) — `POST /auth/telegram`, login
   pro site (adiantado antes do site existir, por pedido explícito — ver
   [`specs/api-design.md`](specs/api-design.md) pra decisão completa):
   - Valida a assinatura HMAC-SHA256 do payload do widget contra
     `SHA256(TELEGRAM_TOKEN)`, rejeita `auth_date` com mais de 24h.
   - Não cria um mecanismo de sessão novo: resolve o usuário com
     `user_service.get_or_create_user` e emite um `AccessToken` comum
     (mesmo mecanismo do `/tokendeacesso` do bot) — o site autentica
     depois exatamente como o app, via Bearer token.
   - 5 testes novos em `tests/test_api.py` (usuário novo, usuário
     existente, payload adulterado, hash errado, `auth_date` expirado).

Ver `git log` para o histórico completo de commits de cada item.

## 🎯 Próximos passos

- Decidir se listagens ganham paginação real — a API não tem o limite de
  4096 caracteres do Telegram, mas listas grandes ainda merecem
  paginação por performance/UX.
- Onde o site vai guardar o token emitido por `/auth/telegram` (e se vale
  a pena dar expiração/rotação a esses tokens especificamente) — decisão
  adiada pra quando o site começar de verdade, ver
  [`roadmap-app.md`](roadmap-app.md).

## Lembrete operacional

Toda vez que um model novo for adicionado (ex.: `AccessToken`), precisa de
migration — ver [`specs/alembic-migrations.md`](specs/alembic-migrations.md).
