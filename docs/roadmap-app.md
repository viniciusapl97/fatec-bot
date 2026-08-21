# Roadmap — Site + App Android/iOS

Ver [`ROADMAP.md`](ROADMAP.md) para o índice geral entre frentes, e
[`specs/frontend-web-and-app.md`](specs/frontend-web-and-app.md) para a
decisão completa (stack, autenticação, estimativas, motivo de cada
escolha).

Última atualização: 2026-08-21.

## Status: 🚧 base em andamento (API), site/app ainda não começados

A ideia evoluiu ao longo da conversa em 2026-08-21: começou como "só um
site" → depois "site + widget Android" → decisão final "site + app
completo (React Native), com widget de tela inicial, iOS talvez um dia".

O primeiro passo (API por cima de `bot/services/`) já está em andamento —
ver [`roadmap-api.md`](roadmap-api.md). Nem o site nem o app tiveram
código escrito ainda.

## Ordem recomendada

1. ~~API primeiro~~ — **em andamento**, ver
   [`roadmap-api.md`](roadmap-api.md).
2. App Android (React Native/Expo) com o essencial (ver/gerenciar grade,
   atividades, faltas, notas) + o widget de tela inicial
   (`react-native-android-widget`) — é o que motivou a conversa, então é
   o que traz retorno mais rápido. Depende dos endpoints de escrita da
   API estarem prontos pra ter paridade completa com o bot (leitura
   sozinha já dá pra um MVP).
3. Site (React) como consumidor adicional da mesma API — precisa do
   Telegram Login Widget (ver `roadmap-api.md`), que ainda não foi
   implementado.
4. iOS e unificação de UI (React Native Web) só depois de validar o
   resto.

## Quando retomar

Não há nada bloqueando o app começar assim que os endpoints de leitura
básicos existirem na API (já existem: `/subjects`, `/activities`,
`/absences`, `/grades`, `/me`) — dá pra montar as primeiras telas do app
Android e o widget mesmo antes dos endpoints de escrita estarem prontos.
