---
workflow: hyperframes
flow: storyboard-v2
storyboard: ../STORYBOARD-V2.md
length: 4 x 60s
format: 1920x1080
fps: 30
---

Executar o storyboard aprovado em `../STORYBOARD-V2.md` usando as skills do HyperFrames (`/hyperframes`, `/hyperframes-cli`, `/hyperframes-registry`, `/media-use`) e entregar quatro MP4 independentes em `renders/`.

Público: moradores do Xingu, sem conhecimento técnico. Baixa carga cognitiva, narrativa contínua guiada pelo ponto âmbar, uma ideia por cena, fala ≤ 19 palavras por cena, locução brasileira offline e legendas embutidas. Snapshot validado `xingu-74d0fdff5980abae3d40` (setembro completo e 1–26/10/2026 em UTC).

## Design

Fundo `#10282d`, marfim `#f5f1e8`, âmbar `#ffc277` (2026 / destaque), cinza-azulado `#64828a` (2025), verde-claro `#abd5bd` (apoio); Segoe UI 700. Título 72–104 px; apoio 40–48 px; legenda 38–42 px. Conteúdo `y=160–850`; legenda `y=900–1008`. Selo fixo `"Parte n de 4"`. Rodapé fixo: `"Focos de calor detectados — INPE / AQUA_M-T • Setembro e 1–26/10/2026 • UTC"`.

## Motion & Transições

- **T1 (Zoom-through pelo ponto âmbar)**: `~0,6 s`, saída `power3.in`, entrada `power3.out`.
- **T2 (Troca com desfoque no mesmo palco)**: saída `0,2 s` `blur(8px)`, entrada `0,13 s`.
- **T3 (Recuo de chegada)**: final do V4 (`scale 1 → 0,6`, blur máx. `6 px`).
- **Títulos**: blur por palavra (`6 px → 0`, `0,13 s`, defasagem `0,07 s`); depois, parados.
- **Barras**: crescem da base zero, `0,6–0,8 s`, `expo.out`; valores fixos com pausa de `0,5 s` antes de cada número-clímax.
- **Foco por contraste**: destaque com halo âmbar fixo; resto a `25%` de opacidade.
