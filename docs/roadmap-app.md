# Roadmap — Site + App Android/iOS

Ver [`ROADMAP.md`](ROADMAP.md) para o índice geral entre frentes, e
[`specs/frontend-web-and-app.md`](specs/frontend-web-and-app.md) para a
decisão completa (stack, autenticação, estimativas, motivo de cada
escolha).

Última atualização: 2026-08-24.

## Status: 🚧 site com paridade completa de CRUD; app ainda não começado

A ideia evoluiu ao longo da conversa em 2026-08-21: começou como "só um
site" → depois "site + widget Android" → decisão final "site + app
completo (React Native), com widget de tela inicial, iOS talvez um dia".
A ordem recomendada original era app Android primeiro — decisão revista
em 2026-08-24: o site foi começado primeiro, por pedido explícito.

## ✅ Feito

1. **Site React** (`web/`, 2026-08-24) — Vite + React + TypeScript,
   React Router, TanStack Query. Paridade completa de CRUD com o bot:
   - Login via Telegram Login Widget (`POST /auth/telegram`, já existia
     no backend) — token guardado em `localStorage`, `401` da API limpa
     a sessão e redireciona pro `/login` (`src/api/client.ts`).
   - Matérias: lista + criar/editar/apagar, com detecção de conflito de
     horário (`409`) exibida no formulário; página de detalhe
     (`/subjects/:id`) com frequência e notas da matéria.
   - Atividades: lista com filtro trabalho/prova, criar/editar/apagar
     (`activity_type` fixo na criação, não editável — mesma regra do
     bot).
   - Faltas: lista, criar/apagar, editar só a quantidade (mesma
     limitação do bot).
   - Notas: lista, criar/editar/apagar.
   - Sem biblioteca de UI — CSS simples e funcional; design autoral fica
     pra uma fase futura separada (ver spec).
   - `api/main.py` ganhou `CORSMiddleware` (não existia — a API nunca
     tinha tido um consumidor de browser); nova env var opcional
     `FRONTEND_ORIGINS` em `bot/core/settings.py`.
   - Validado manualmente ponta a ponta contra a API local (SQLite):
     login/logout, CRUD das 4 entidades, conflito de horário, 401 →
     redirect.
2. **Testes automatizados do site** (2026-08-24) — Vitest + React Testing
   Library + jsdom. Cobertura deliberadamente não-exaustiva: `client.ts`
   (header de auth, 401, parsing de erro, 204), `AuthContext` (login/
   logout/refresh de sessão) e um teste de componente completo
   (list+form+conflito 409+delete) em `Subjects.test.tsx`, que serve de
   referência de padrão pras outras 3 páginas em vez de ser copiado
   1:1 nelas. Detalhes em `CLAUDE.md` → "Web frontend tests".
3. **Redesign visual + navegação mobile** (2026-08-24) — tema escuro
   estilo "dashboard" (Inter + Space Grotesk, acento gradiente roxo/azul,
   `lucide-react` pros ícones), sidebar com navegação por ícone no
   desktop. No mobile (`≤780px`): barra superior fina + barra de
   navegação fixa embaixo (estilo app nativo) em vez da sidebar; as
   tabelas de listagem (`≤720px`) viram uma lista de cards em vez de
   tabela horizontal cortada.
4. **Calculadora "quanto preciso tirar"** (2026-08-24) — em
   `/subjects/:id`, dado as notas já lançadas de uma matéria, calcula a
   média necessária nas notas que faltam pra bater uma média alvo.
   Cálculo 100% client-side (mesma fórmula de `grade_service.get_average`
   — média aritmética simples), sem endpoint novo.
5. **Banner de risco de reprovação por falta no Dashboard** (2026-08-24)
   — `GET /subjects` passou a embutir os mesmos campos computados de
   `GET /subjects/{id}/attendance` (`percent`, `remaining_allowed`,
   `at_risk`, `failed`) direto em `SubjectOut`, pra listar as matérias em
   risco na tela inicial sem precisar de uma chamada extra por matéria.
   Mudança de backend em `api/routers/subjects.py`/`api/schemas.py`
   (`SubjectCreate`/`Update` não mudam), 2 testes novos em
   `tests/test_api.py`.

## 🎯 Próximos passos

- App Android (React Native/Expo) — ver "Ordem recomendada" abaixo.
- Testes de componente das páginas restantes (Atividades/Faltas/Notas),
  se algum bug real aparecer nelas ou se o padrão precisar ser validado
  de novo — não são obrigatórios agora (mesmo shape do `Subjects.test.tsx`).
- Deploy do site (depende de `roadmap-hosting.md`, ainda local/pausado).

## Ordem recomendada (atualizada)

1. ~~API primeiro~~ — **feito**, ver [`roadmap-api.md`](roadmap-api.md).
2. ~~Site (React)~~ — **feito** (paridade completa de CRUD, ver acima).
3. App Android (React Native/Expo) com o essencial (ver/gerenciar grade,
   atividades, faltas, notas) + o widget de tela inicial
   (`react-native-android-widget`) — motivo original da conversa, ainda
   não começado.
4. iOS e unificação de UI (React Native Web) só depois de validar o
   resto.
