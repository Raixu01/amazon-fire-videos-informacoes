---
workflow: general-video
flow: automation
storyboard: no
length: 4 x 60s
format: 1920x1080
---

Executar o storyboard aprovado em `../STORYBOARD-4-VIDEOS.md` e entregar quatro MP4 independentes. Pedido explícito de construção e exportação recebido em 27/10/2026. A renderização está autorizada pelo pedido do usuário.

Público: moradores do Xingu. Linguagem cotidiana, uma ideia por cena, fontes grandes, locução brasileira e legendas embutidas. Usar mapa e dados locais do snapshot validado, sem novos números. Outubro parcial até dia 26, UTC. Captura de aviso de 11/10, nome oculto. Não atribuir os registros posteriores como motivo do envio anterior.

## Design

Fundo azul-petróleo #10282d, texto marfim #f5f1e8, âmbar #ffc277 e verde claro #abd5bd. Segoe UI local, títulos em peso 700. Título 72–104px, texto 40–48px, legendas 38–42px. Conteúdo principal entre y=160 e y=850; legendas entre y=900 e y=1008. Fonte e corte temporal em rodapé. Mapas em escala constante. Gráficos com base zero. Datas explícitas.

## Motion

Entradas curtas por opacidade e deslocamento de 18px. Números fixos, sem contagem intermediária inventada. Barras crescem a partir da base com `stat-bars-and-fills`. Aproximação regional segue `coordinate-target-zoom` ou mudança determinística de enquadramento do SVG. Nada pisca. Planos mantidos para leitura. Sem efeitos de sirene.

## Assets

- `../../aviso_queimadas_gov.png`, captura fornecida pelo usuário.
- `../../../remotion/src/xingu-dados.json`, geometrias projetadas e contagens existentes.
- Voz sintética brasileira; tentar Francisca Neural, com Microsoft Maria local como recuperação se o serviço estiver indisponível. Sem música para priorizar a inteligibilidade.
- GSAP 3.14.2 baixado do CDN oficial do pacote, congelado localmente.

## Validation

Conferir soma e seleção dos picos contra o CSV validado. Conferir telas em navegador real, continuidade de legendas, enquadramento, final das falas e metadados dos MP4: 1920x1080, 60s, vídeo H.264 e áudio AAC. Preservar assets e arquivos editáveis.
