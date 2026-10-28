# REVIEW — Episódio 3: Os picos

## 1. Decisões criativas e estrutura
- A cena 1 (`0–7s`) recebe a costura `T1` do Episódio 2 pousando nos 10 municípios da Região de Integração Xingu com proporções geográficas preservadas.
- Na cena 2 (`7–15s`), o mapa recua à esquerda (`40%`) e o gráfico diário de 56 barras (`01/09` a `26/10/2026 • UTC`, base zero) se constrói na ordem de leitura: eixo -> linhas de referência -> barras da esquerda para a direita (`expo.out`).
- As cenas 3 (`21/09 = 149`) e 5 (`09/10 = 336`) aplicam pausa de `0.5s` antes de pousar o número-clímax fixo (sem contagem intermediária), mantendo as demais barras a `25%` de opacidade e separadas por um respiro sem locução na cena 4 (`26–31s`, `"Outubro: 1–26"` via `T2`).
- Na cena 6 (`42–50s`), Altamira é realçada em `09/10` (`"104 dos 336"`, `"Foco ≠ área queimada"`) com os outros 9 municípios a `25%`.
- Na cena 7 (`50–60s`), os outros 4 dias do top-3 de cada mês (`13/09 · 101`, `26/09 · 108`, `12/10 · 314`, `25/10 · 297`) recebem marcas finas em ordem cronológica (`0.4s` cada).

## 2. O que foi medido e verificado
- `npx hyperframes check --json`: **0 erros e 0 avisos** em `lint`, `runtime`, `layout` e `contrast`.
- `npx hyperframes snapshot`: 8 quadros inspecionados (`3s, 11s, 20s, 28.5s, 36s, 46s, 56s, 58.2s`), confirmando que o respiro silencioso em `28.5s` não exibe legenda órfã e que todos os números batem com o snapshot `xingu-74d0fdff5980abae3d40`.
- O áudio (`narracao.wav`, `60.00s` exatos) foi medido, não ouvido diretamente.

## 3. Ponto de atenção
- As hastes das 4 marcas na cena 7 usam alturas alternadas para evitar qualquer colisão visual entre barras próximas (`09/10` e `12/10`).

