# Roadmap — Hospedagem

Ver [`ROADMAP.md`](ROADMAP.md) para o índice geral entre frentes.

Última atualização: 2026-08-21.

## Status: ainda rodando localmente

Decisão em aberto (2026-08-21): o usuário quer aproveitar o assunto pra
estudar AWS, usando o free tier (EC2 t2/t3.micro + RDS Postgres
t3/t4g.micro, ambos elegíveis por 12 meses em conta nova). Ainda não
começou — avisou que "por enquanto não" quando perguntado se queria
seguir com o setup.

## Plano combinado, quando retomar

1. Criar um budget alert primeiro (antes de qualquer recurso).
2. IAM user próprio (não usar a conta root).
3. VPC/Security Groups (pode usar a VPC default pra começar).
4. EC2 — subir o bot como `systemd` service.
5. RDS Postgres — migrar do banco local pra ele (`alembic upgrade head`
   no banco novo, ver [`specs/alembic-migrations.md`](specs/alembic-migrations.md)).
6. CloudWatch pros logs.

## Nota pra quando a API/site/app entrarem em produção

Esse plano cobre só o bot. Quando a API (`api/`) for pra produção
também, ela pode rodar na mesma EC2 (outro processo, ex. via
`systemd`/`nginx` na frente) ou em outro lugar — ainda não decidido, não
é urgente enquanto só o bot está em produção.
