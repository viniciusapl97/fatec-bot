# Spec: Frontend web + app Android/iOS

Discutido e decidido em 2026-08-21. Ver [`roadmap-app.md`](../roadmap-app.md)
para o status/próximos passos, e [`roadmap-api.md`](../roadmap-api.md) para
o backend que sustenta os dois.

A ideia evoluiu ao longo da conversa: começou como "só um site" → depois
"site + widget Android" → decisão final "site + app completo (React
Native), com widget de tela inicial, iOS talvez um dia".

## A base: API por cima de `bot/services/`

Toda a regra de negócio já está isolada em `bot/services/`, sem nenhuma
dependência do Telegram — dá pra expor esses mesmos services por trás de
uma API (FastAPI, `api/`) sem reescrever a lógica. **Isso é o que o site e
o app têm em comum** — a UI de cada um é separada (ver stack abaixo), só a
API é compartilhada. Ver [`specs/api-design.md`](api-design.md).

## Stack decidida

- **Site**: React.
- **App**: React Native, via Expo (facilita o build local/sideload sem
  conta de desenvolvedor). Android primeiro; iOS "um dia" fica bem mais
  barato de adicionar depois por já estar no React Native, em vez de
  começar do zero em Swift futuramente.
- **React Native Web** é uma opção pra unificar o código de UI entre site e
  app (usado em produção por apps grandes, ex. o X/Twitter novo) — mas não
  é o ponto de partida recomendado. Começar com React puro no site e React
  Native no app (compartilhando só os tipos/chamadas de API) é mais
  simples; migrar pra RN Web depois é uma opção, não um requisito.

## Widget de tela inicial (o motivo original de cogitar um app nativo)

O motor JS do React Native roda dentro do processo do app — um widget é
renderizado pelo *sistema operacional* fora desse processo, então **sempre
vai precisar de uma peça nativa**, mesmo com React Native:
- **Android**: lib
  [`react-native-android-widget`](https://github.com/sAleksovski/react-native-android-widget)
  — desenha o layout do widget em JSX, ela compila pra views nativas em
  build time. É a melhor opção atual pra esse cenário — não é "rodar JS
  dentro do widget".
- **iOS** (se um dia acontecer): a Apple exige SwiftUI pra widgets, sem
  exceção — não existe bridge de React Native pra isso. Não tem como fugir
  de Swift nessa parte específica, mesmo com o app todo em React Native.

## Autenticação — diferente pro site e pro app

- **Site**: como o bot serve qualquer usuário do Telegram (não é só de uso
  pessoal), o caminho certo é o **Telegram Login Widget** — usuário clica
  "Entrar com Telegram", o Telegram autentica e devolve um payload
  assinado (`user_id`, nome, username, foto) pro backend validar o hash.
  Zero senha nova pra gerenciar, e o `user_id` já bate com `User.user_id`
  no banco. **Já implementado no backend** (`POST /auth/telegram`, ver
  [`specs/api-design.md`](api-design.md)) — adiantado antes do site
  existir; falta só o botão/fluxo no frontend quando o site começar.
- **App/widget**: como esse app é só pra uso pessoal (sideload, sem loja),
  não vale a pena replicar o fluxo de Login Widget — mais simples é o
  **token de acesso pessoal** vinculado ao `user_id`, colado uma vez na
  configuração do app. **Já implementado** — ver
  [`specs/api-design.md`](api-design.md).

## Estimativa por nível de ambição

- MVP somente-leitura (login + ver grade/notas/faltas/frequência/calendário),
  só no site: alguns fins de semana.
- Paridade completa (criar/editar/apagar tudo, igual ao bot) no site e/ou
  no app: várias semanas, part-time — o app soma tempo extra se React
  Native/Expo for novidade.
- Widget Android funcionando (`react-native-android-widget`): escopo
  pequeno uma vez que a API já existe — não precisa esperar o app inteiro
  ficar pronto pra fazer o widget.
- Design autoral + gráficos de evolução + iOS + tempo real ("muito foda"):
  meses — a parte mais aberta, sem teto.

## Ordem recomendada

1. API primeiro (FastAPI sobre `bot/services/`) — **em andamento**, ver
   [`roadmap-api.md`](../roadmap-api.md).
2. App Android (React Native/Expo) com o essencial (ver/gerenciar grade,
   atividades, faltas, notas) + o widget — é o que motivou a conversa,
   então é o que traz retorno mais rápido.
3. Site como consumidor adicional da mesma API, quando fizer sentido.
4. iOS e unificação de UI (React Native Web) só depois de validar o resto.
