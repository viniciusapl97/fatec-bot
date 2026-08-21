# Spec: Migrations com Alembic

Decisão tomada em 2026-08-21. Ver o item correspondente em
[`roadmap-bot.md`](../roadmap-bot.md) para o status/changelog resumido.

## Problema

O bot criava/atualizava as tabelas com `Base.metadata.create_all(bind=engine)`
toda vez que subia (`main.py`) ou que `seed_db.py` rodava. Isso funciona pra
criar tabelas que não existem, mas **não migra colunas em tabelas que já
existem** — cada mudança de schema em produção dependia de alguém lembrar de
rodar um `ALTER TABLE` manual. Já tínhamos acumulado duas pendências assim
(`notifications_enabled`, `notification_hour`) antes de resolver isso de vez.

## Decisão

Adotar [Alembic](https://alembic.sqlalchemy.org/) como dono do schema.
`Base.metadata.create_all()` foi removido de `main.py` e `seed_db.py` —
migrations passam a ser a única forma de criar/alterar tabelas.

- `migrations/env.py` importa `bot.db.base.Base` + `bot.db.models` (pra
  `Base.metadata` conter todas as tabelas) e define `sqlalchemy.url` em
  runtime a partir de `bot.core.settings.DATABASE_URL` — as mesmas
  variáveis de ambiente do resto do projeto, nada duplicado/hardcoded em
  `alembic.ini`.
- Migration baseline (`migrations/versions/6cde7bf58518_*.py`) cobre as 7
  tabelas que existiam na hora da adoção.

## Adotando em um banco que já existe (dev ou produção)

Um banco criado antes do Alembic existir (via `create_all()`, como o que
você já está rodando localmente) **não deve rodar `alembic upgrade head`
direto** — isso tentaria `CREATE TABLE` em tabelas que já existem e falharia.

```bash
# Uma única vez, no banco que já existe:
alembic stamp head

# Dali em diante, sempre:
alembic upgrade head
```

`stamp head` marca o banco como "já está na versão mais recente" sem
executar nenhum DDL — como a migration baseline já inclui
`notifications_enabled` e `notification_hour`, esse passo único também
resolve as duas pendências de `ALTER TABLE` manual que tínhamos.

## Validação

Testado de ponta a ponta contra um Postgres real (container Docker
`postgres:16-alpine`, descartado ao final — sem dependência nova pro
projeto):
1. `alembic upgrade head` do zero → tabelas criadas certinho.
2. `alembic check` → sem diferença pendente entre os models e o banco.
3. `alembic downgrade base` → limpo, remove tudo.
4. Simulado o estado real do usuário: tabelas criadas via `create_all()`
   (sem Alembic) → `alembic stamp head` → dados intactos, `alembic check`
   continua sem diferença.
5. Rodei operações reais dos `services/` (criar usuário, matéria,
   atividade, falta, nota, lembrete, calcular frequência) direto sobre o
   schema criado pela migration — tudo funcionando.

A suíte pytest (SQLite) não usa `main.py`/`seed_db.py` diretamente, então
não foi afetada por essas mudanças.

## Efeito colateral: `requirements.txt` estava em UTF-16

Ao tentar só adicionar a linha do `alembic` em `requirements.txt`, a
ferramenta de edição preservou a codificação original do arquivo — que
sempre esteve em UTF-16 (provavelmente gerado via `pip freeze` no
PowerShell do Windows; por isso `cat`/`grep` sempre mostraram ele
"espaçado" quando alguém olhava o arquivo num terminal Linux/macOS). O
resultado foi um `requirements.txt` em UTF-16 com a linha nova, o que quebra
o `pip` (`ERROR: Invalid requirement` com bytes `\x00` literais no meio do
nome do pacote).

Corrigido reescrevendo o arquivo inteiro via heredoc de shell
(`cat > requirements.txt << 'EOF' ... EOF`), que força UTF-8 independente do
que já estava no arquivo. Esse é o método a usar sempre que precisar
corrigir a codificação de um arquivo não-UTF-8 — editar normalmente
preserva a codificação original.
