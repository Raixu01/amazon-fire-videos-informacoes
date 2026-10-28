# REVIEW — Episódio 1: O alerta

## 1. Decisões criativas e estrutura
- A abertura (`0–6s`) já inicia no quadro 0 com a captura GovBR (`11/10/2026`, nome da destinatária oculto), aplicando *push* de `100% -> 118%` sobre o bloco `"Sua região está sob alerta de incêndios."` com halo âmbar fixo e restante a `25%` de opacidade.
- Na cena 2 (`6–16s`), um *pan* vertical curto desloca a janela de destaque âmbar para `"A fumaça pode causar problemas respiratórios."`.
- Na cena 4 (`28–42s`), em vez de três cartões em fileira (banidos pelo `STORYBOARD-V2.md` e `spec.md`), os três passos (`1. Vegetação seca`, `2. Fogo`, `3. Fumaça sobre a casa`) ocupam a **mesma posição central** um por vez conforme a voz os nomeia, recuando o passo anterior a `25%` de opacidade nos cantos superiores sob o selo `"ILUSTRAÇÃO"`.
- O ponto âmbar atua como *carrier* nas costuras `T1` (`c2->c3` e `c5->c6`).

## 2. O que foi medido e verificado
- `npx hyperframes check --json`: **0 erros e 0 avisos** em `lint`, `runtime`, `layout` e `contrast` (`65/65` verificações de contraste aprovadas).
- `npx hyperframes snapshot`: 9 quadros inspecionados (`1s, 3s, 10s, 20s, 30s, 36s, 46s, 56s, 58.2s`), confirmando ausência de sobreposição entre legendas (`y=900–1008`) e palco (`y=160–850`).
- O áudio (`narracao.wav`, `60.00s` exatos) foi medido por `WordBoundary` e `volumedetect`, não ouvido diretamente.

## 3. Ponto de atenção
- Na transição `T1` final (`59.4–60.0s`), o ponto âmbar expande rapidamente em `power3.in` para entregar o corte ao Episódio 2; mantido exatamente em `0.6s` conforme o ledger.

