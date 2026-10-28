# REVIEW — Episódio 2: A época

## 1. Decisões criativas e estrutura
- A montagem histórica 2020–2026 foi retirada do Vídeo 2 (conforme decisão aprovada no `STORYBOARD-V2.md`), reduzindo a carga cognitiva e dedicando a cena 3 (`18–32s`) a ensinar a leitura do mapa: primeiro 1 ponto âmbar ampliado (`"1 ponto = 1 foco de calor detectado"`), seguido dos lotes mensais de setembro e de outubro (`1–26/10/2026 • UTC`) via transição `T2` (*blur swap* de `8px` no mesmo palco).
- Na cena 2 (`7–18s`), a gota de chuva encolhe e recua a `25%` enquanto a folha muda de verde (`#abd5bd`) para âmbar seco (`#ffc277`) em `1.2s` (`power2.inOut`), com a seta entrando somente após a transformação.
- Na cena 4 (`32–44s`), o diagrama do Pacífico Equatorial colore em `0.8s` e exibe a seta curta para a Amazônia depois, com fonte explícita `"NOAA, 08/10/2026"`.

## 2. O que foi medido e verificado
- `npx hyperframes check --json`: **0 erros e 0 avisos** em `lint`, `runtime`, `layout` e `contrast`.
- `npx hyperframes snapshot`: 9 quadros inspecionados (`2s, 11s, 20s, 26s, 31s, 37s, 48s, 56s, 58.2s`), verificando os três estados da cena 3 (`20s` ponto didático, `26s` lote de setembro, `31s` lote de outubro 1–26) e a costura `T1` para o Xingu (`56s–58.2s`).
- O áudio (`narracao.wav`, `60.00s` exatos) foi medido por `WordBoundary` e `volumedetect`, não ouvido diretamente.

## 3. Ponto de atenção
- Os pontos da Amazônia Legal em setembro/outubro são representados em lote estático sem rastro acumulado, preservando a leitura em telas pequenas.

