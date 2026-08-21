# Spec: Design da API (`api/`)

Decisões tomadas em 2026-08-21, ao começar a implementação da API. Ver
[`roadmap-api.md`](../roadmap-api.md) para o status/changelog resumido (o
que já foi construído, o que falta).

## Por que uma API por cima de `bot/services/`

Toda a regra de negócio do bot já vive em `bot/services/`, sem nenhuma
dependência do Telegram (nenhum `import telegram`, nenhum `import dialogs`
— ver `CLAUDE.md`). A API é só mais um "cliente" desses services, do mesmo
jeito que `bot/handlers/` já é — não duplica lógica nenhuma, e o bot
continua funcionando de forma totalmente independente da API existir ou
não.

## Autenticação: token de acesso pessoal (não Telegram Login Widget)

Existem dois consumidores planejados pra API, com necessidades diferentes
(ver [`specs/frontend-web-and-app.md`](frontend-web-and-app.md)):
- **Site**: serve qualquer usuário do bot → precisa de um login de verdade
  → **Telegram Login Widget** é o caminho certo (ainda não implementado).
- **App pessoal (React Native, sideload)**: só uso próprio, sem loja → não
  vale a pena replicar o fluxo OAuth-like do Login Widget.

Pra esse segundo caso, implementado um **token de acesso pessoal**:
- `AccessToken` (`bot/db/models.py`) guarda só o **hash SHA-256** do token
  — nunca o valor em texto puro. Igual senha, só que sem usuário/senha.
- `/tokendeacesso` no bot (`bot/handlers/user_settings_handler.py`) gera um
  token com `secrets.token_urlsafe(32)` e mostra pro usuário **uma única
  vez** — depois disso, só o hash existe, não tem como recuperar o valor
  original (se perder, gera outro).
- `/revogartokens` apaga todos os tokens do usuário de uma vez — pensado
  pro caso de um token vazar.
- A API valida via header `Authorization: Bearer <token>` —
  `api/deps.get_current_user` faz o hash do token recebido e busca no
  banco (`access_token_service.get_user_by_token`), 401 se não achar.

## Separação entre `api/schemas.py` e `bot/db/models.py`

Os modelos Pydantic de resposta (`api/schemas.py`) são deliberadamente um
contrato **separado** dos models do SQLAlchemy, mesmo espelhando os mesmos
campos na maioria dos casos. Isso é intencional: uma mudança de coluna no
banco não vaza sem querer pro contrato público da API. Endpoints que juntam
dado de mais de uma tabela (ex.: `ActivityOut`/`AbsenceOut`/`GradeOut`
embutindo `subject_name`, que não é atributo direto do model) são montados
manualmente no router, não via `from_attributes` automático do Pydantic.

## Pegadinhas de teste descobertas nesse processo

### `StaticPool` pro SQLite dos testes

Testar a API com o `TestClient` do FastAPI contra o SQLite em memória dos
testes dava `sqlite3.OperationalError: no such table: ...` mesmo com a
tabela existindo. Causa: o `TestClient` roda a aplicação ASGI numa thread
separada da thread do teste, e o pool padrão do SQLite (`SingletonThreadPool`)
cria um banco em memória **novo e vazio por thread**.

Corrigido em `bot/db/base.py`: quando `DATABASE_URL` começa com `sqlite`,
força `poolclass=StaticPool` + `connect_args={"check_same_thread": False}`
— todas as threads passam a compartilhar a mesma conexão/banco. Só se aplica
a SQLite; o Postgres de produção não é afetado (continua com o pool padrão
do SQLAlchemy).

### Criação de tabelas precisa ser `autouse`, não só dentro da fixture `db`

Testes de API que não pedem a fixture `db` (ex.: "token inválido → 401", que
não precisa inserir nada no banco) nunca disparavam
`Base.metadata.create_all()`, que vivia só dentro da fixture `db`. Rodando a
suíte inteira isso passava despercebido (outro arquivo de teste, executado
antes, já tinha criado as tabelas), mas rodar só `pytest tests/test_api.py`
sozinho quebrava com `no such table`.

Corrigido movendo a criação de tabelas pra uma fixture `autouse=True`,
`scope="session"`, em `tests/conftest.py` — roda uma vez antes de qualquer
teste, independente de quais/quantos pedem `db`.

## Validação

Cada leva de endpoints foi testada contra um Postgres real (container
Docker `postgres:16-alpine`, descartado ao final) além dos testes
automatizados: gerar token pelo bot → autenticar na API → endpoints
retornando os dados certos, escopados só ao dono do token → token
inválido/ausente rejeitado (401/403) → revogar invalida na hora. Rodado
também com `uvicorn` de verdade (não só `TestClient`), incluindo o `/docs`
(Swagger) que vem de brinde com o FastAPI.
