# REVIEW — Episódio 4: A comparação

## 1. Decisões criativas e estrutura
- Na cena 2 (`7–19s`), a barra de 2025 (`1.113`, cinza-azulado `#64828a`) cresce primeiro da base zero (`t=7.35s`) e permanece sozinha até `t=13.0s` (confirmado no snapshot `t=10s`), quando após pausa de `0.5s` a barra de 2026 (`3.688`, âmbar `#ffc277`) cresce em `expo.out` (confirmado no snapshot `t=16s`).
- Na cena 3 (`19–26s`), o percentual **`+231%`** pousa fixo após pausa de `0.5s`, sem contagem animada.
- Na cena 4 (`26–37s`), as barras recuam a `25%` de opacidade e os selos `"2025: sem El Niño"`, `"2026: com El Niño"` e `"Isso não prova a causa."` entram em sequência sincronizados à fala.
- Na cena 5 (`37–47s`), o texto literal do art. 41 da Lei 9.605/1998 entra com *blur* por palavra e permanece completamente parado por mais de `8s` (acima do mínimo de `3s`).
- Na cena 6 (`47–60s`), a transição `T3` (único recuo da série) pousa na captura GovBR com o bloco de prevenção realçado em âmbar e a frase final `"Acompanhe os alertas. Evite provocar incêndios."` parada pelos últimos `8s`.

## 2. O que foi medido e verificado
- `npx hyperframes check --json`: **0 erros e 0 avisos** em `lint`, `runtime`, `layout` e `contrast`.
- `npx hyperframes snapshot`: 8 quadros inspecionados (`3s, 10s, 16s, 22s, 32s, 42s, 55s, 58.2s`).
- O áudio (`narracao.wav`, `60.00s` exatos) foi medido, não ouvido diretamente.

## 3. Ponto de atenção
- As penas previstas na Lei 9.605/1998 foram mantidas exclusivamente para a legenda/material de apoio da publicação, conforme determinado no `STORYBOARD-V2.md`.

