# Composição visual — Pulso / Amazônia Legal e Xingu

Composição Remotion `PulsoAmazoniaXingu`, edição 2, 1920×1080, 30 fps, 8.160 quadros e duração de **4min32s**, sem áudio. Há também `PulsoAmazoniaXinguPrevia`, uma prévia acelerada de 25 segundos. Para avaliar o novo ritmo de leitura, usar o vídeo completo ou o trecho em velocidade normal.

## Entregas

- [Vídeo completo revisado em MP4](pulso-amazonia-xingu-totais-diarios.mp4).
- [Trecho do Xingu em velocidade normal — 18 segundos](trecho-xingu-totais-diarios.mp4).
- [Prévia acelerada em MP4](previa-amazonia-xingu-totais-diarios.mp4).
- [Prancha de seis quadros](visual-v2/storyboard.jpg).
- [QA visual e medições no navegador](visual-v2/render-qa.json).
- [Verificação dos arquivos MP4](visual-v2/video-qa.json).

A [versão anterior de 2min30s](pulso-amazonia-xingu-2018-2026.mp4) foi preservada. A revisão atende ao pedido de exibir o **total fechado de focos por dia e por município**, com todas as bolinhas daquele dia no território. Cada data permanece três segundos, em vez de um. O total municipal aparece também junto ao nome no mapa; o contador acumulado do mês foi retirado.

Esta edição usa o snapshot `xingu-74d0fdff5980abae3d40`, com corte exclusivo em 27/10/2026 às 00h UTC. A existência do calendário completo não implica observações de todo o mês: 27/10 está fora do corte, e 28–31/10 ainda eram futuros na coleta. Essas datas aparecem com traço, sem pontos ou totais zero. Os comparativos de outubro usam 1–26/10 em ambos os anos.

## Leitura visual

Fundo azul escuro, tipografia clara e acentos em verde e âmbar. Os dois mapas históricos usam a mesma projeção, enquadramento e escala de cores. Todos os 773 municípios permanecem delineados; preenchimentos representam focos por município no mês, não área queimada.

Uma régua contínua acompanha a troca de anos, de 2018 a 2026. Cada ano dura cinco segundos e os dois meses mudam juntos. O ano e os totais não são interpolados: são os valores efetivamente observados, com outubro de 2026 identificado como parcial.

A câmera parte do painel de outubro de 2026. O painel se amplia, aproxima o Xingu e retira progressivamente os demais limites. Ao concluir, somente as dez geometrias do Xingu estão na camada do mapa. A escala geográfica permanece proporcional ao longo do movimento.

No diário, o enquadramento fica fixo, com rótulos dos dez municípios e o total diário junto a cada nome. Todas as detecções do dia são representadas simultaneamente por bolinhas, sem simular uma evolução por horário. Os pontos e totais permanecem completos durante os três segundos de leitura e são substituídos na mudança de data. Não há acúmulo entre dias. O total regional e a tabela mostram exclusivamente a data selecionada.

As bolinhas foram ampliadas para legibilidade. Posições coincidentes ou próximas podem se sobrepor: os números contam todas as detecções, mesmo quando duas bolinhas ocupam o mesmo lugar. O gráfico inferior mantém o contexto dos totais diários na mesma escala e distingue datas desconhecidas com retângulos tracejados.

Os três cartões finais mostram setembro, outubro parcial e o conjunto das duas janelas. As barras têm uma base comum dentro de cada cartão, com totais fixos, diferença absoluta, variação percentual e período explícito. Bases anteriores iguais a zero mantêm o percentual indisponível.

## Sequência

| Intervalo | Cena |
|---|---|
| 00:00–00:06 | Abertura: território, nove anos e detalhe diário |
| 00:06–00:51 | Setembro/outubro lado a lado, 2018–2026 |
| 00:51–00:57 | Aproximação para o Xingu e retirada dos demais contornos |
| 00:57–01:01 | Apresentação do diário de setembro |
| 01:01–02:31 | 01–30/09, três segundos por data, total fechado do dia |
| 02:31–02:35 | Apresentação do diário de outubro |
| 02:35–04:08 | 01–31/10, três segundos por data; estados sem dados sinalizados |
| 04:08–04:26 | Três comparativos com 2025 |
| 04:26–04:32 | Fontes, corte e interpretação dos focos |

## Editar e renderizar

Na raiz, para regenerar os dados visuais a partir da última ingestão validada:

```powershell
.venv/Scripts/python.exe scripts/preparar_visual_xingu.py
```

Na pasta `remotion`:

```powershell
npm run studio
# Selecionar PulsoAmazoniaXingu ou PulsoAmazoniaXinguPrevia
npm run render:xingu:previa
npm run render:xingu
```

Para repetir a inspeção dos 29 quadros no navegador, incluindo início, meio e fim de uma mesma data:

```powershell
node xingu-qa.cjs
```

Da raiz, para conferir codecs, duração, contagem de quadros, decodificação e hashes:

```powershell
.venv/Scripts/python.exe scripts/verificar_video_xingu.py
```

O render usa H.264/yuv420p, BT.709 explícito e concorrência 2. Todos os dados, geometrias e textos são locais; não há downloads de mapas ou consulta online durante a renderização. Tipografia: Segoe UI, com alternativas Arial/sans-serif. As composições anteriores foram preservadas.

Os scripts npm incluem `--color-space bt709`. A edição 2 é renderizada diretamente em BT.709/yuv420p. Na primeira edição, foi necessária uma conversão de faixa; seu registro permanece em [cor-normalizada.json](visual/cor-normalizada.json).

## Fontes editáveis e reprodução

- `remotion/src/xingu-video.jsx`: cenas, elementos, legenda, textos e transições.
- `remotion/src/xingu-model.cjs`: relógio, seleção de dia, câmera, cores e posicionamento de rótulos.
- `remotion/src/xingu-dados.json`: dados visuais congelados, geometrias SVG e pontos projetados; SHA-256 em `visual-v2/dados.json`.
- `edicao.json`: ritmo, duração e nomes dos arquivos da edição 2; mantém separado o contrato analítico usado na ingestão.
- `scripts/preparar_visual_xingu.py`: projeção Mercator EPSG:3857 e conversão dos produtos do snapshot.
- `remotion/xingu-qa.cjs`: captura de quadros e medições de elementos realmente montados no navegador.

As coordenadas geográficas não são alteradas na base analítica. A projeção e a precisão de duas casas decimais nos caminhos SVG são tratamentos de visualização. Anéis internos e ilhas são preservados; o preenchimento usa a regra par/ímpar.

A animação depende exclusivamente do número do quadro, conforme o modelo de [useCurrentFrame do Remotion](https://www.remotion.dev/docs/use-current-frame). Não há relógio de parede, aleatoriedade ou transições CSS que mudem o resultado conforme o momento de captura.

Os testes da nova composição cobrem os nove anos, virada de mês, substituição dos pontos, datas ausentes/futuras, conjunto territorial, janelas equivalentes, cores, câmeras, rótulos e prévia. Para as 61 datas, verificam a permanência do total completo no início, meio e fim dos três segundos. As medições no navegador conferem o total regional, os dez totais escritos no mapa, a quantidade de bolinhas, os limites municipais e a ausência de texto fora do quadro.

Verificação da edição 2: **47 testes Python e 137 testes JavaScript passaram**. Os 29 quadros revisados não tiveram erros de navegador ou texto fora do quadro. O verificador de MP4 confere codec, pixel format, resolução, taxa de quadros, duração, quantidade de quadros e decodificação integral.

Uma conferência independente preservada em [revisao.json](visual-v2/revisao.json) confirmou que todos os dados analíticos e comparativos permanecem iguais e que 12 quadros amostrados do panorama e do zoom são idênticos, pixel a pixel, aos da edição anterior. Os fontes anteriores foram guardados em `versoes/v1-diario/`; os MP4s anteriores permanecem com seus nomes originais.

O teste antigo que conferia oito casos de `test_data.py` foi limitado a esse arquivo, conforme seu título, preservando suas oito verificações. A suíte Python completa foi executada separadamente, com todos os 47 testes. O `ffprobe` já instalado junto ao Remotion foi adicionado somente ao PATH do processo de testes.
