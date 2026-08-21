# Roadmap — Índice

Mapa de tudo que existe pra manter contexto entre sessões. Cada frente tem
seu próprio arquivo de roadmap (o que já foi feito, o que falta); decisões
de design com alguma ambiguidade real (não mudanças mecânicas) viram um
spec em `specs/`, referenciado pelo roadmap da frente correspondente.

Atualize o roadmap da frente que você tocou ao concluir ou decidir adiar
algo. Crie um spec novo só quando a decisão não for óbvia a partir do
código — coisa tipo "por que essa lib e não aquela", "por que esse modelo
de autenticação", não "adicionei mais um endpoint que só espelha um
service que já existia".

Última reorganização: 2026-08-21 (era um arquivo único até aqui — ver
`git log -- docs/ROADMAP.md` se precisar do histórico anterior).

## Roadmaps por frente

- [`roadmap-bot.md`](roadmap-bot.md) — o bot de Telegram em si. 18 itens
  entregues, 1 pendência de longo prazo (testes de handler/integração).
- [`roadmap-api.md`](roadmap-api.md) — API HTTP (`api/`) sobre
  `bot/services/`. Em andamento: auth por token pessoal + endpoints de
  leitura de matérias/atividades/faltas/notas prontos; faltam
  frequência/média, endpoints de escrita, e o Telegram Login Widget (pro
  site).
- [`roadmap-app.md`](roadmap-app.md) — site (React) e app Android/iOS
  (React Native + widget). Ainda não começados; a API é o que os
  desbloqueia.
- [`roadmap-hosting.md`](roadmap-hosting.md) — deploy. Ainda rodando
  local; plano combinado é AWS free tier (EC2 + RDS), pausado por agora.

## Specs (decisões de design)

- [`specs/alembic-migrations.md`](specs/alembic-migrations.md) — por que
  Alembic, como adotar num banco que já existe, validação feita.
- [`specs/api-design.md`](specs/api-design.md) — autenticação da API
  (token pessoal vs. Login Widget), separação `api/schemas.py` vs.
  `bot/db/models.py`, pegadinhas de teste (SQLite + threads).
- [`specs/frontend-web-and-app.md`](specs/frontend-web-and-app.md) —
  stack decidida (React / React Native / Expo), por que um widget de
  tela inicial sempre precisa de peça nativa, autenticação site vs. app.
