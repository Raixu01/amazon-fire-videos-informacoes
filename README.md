# Informações de produção dos vídeos — Pulso / Amazon Fire

Acervo preparado em 28/10/2026 a partir dos arquivos locais de `amazon-fire`. Reúne dados utilizados, fontes, metodologia, roteiros, legendas, composições e relatórios de produção. Os caminhos foram preservados para facilitar a consulta cruzada. Originais: https://github.com/Raixu01/amazon-fire.

## Índice das edições

| Edição | Informações principais | Dados e composição |
| --- | --- | --- |
| Altamira, 8–14/10/2026 | [Nota técnica, roteiro e créditos](entregas/altamira/LEIA-ME.md) | [Camadas](entregas/altamira/camadas/), [auditoria](entregas/altamira/auditoria.json), [Remotion](remotion/src/video.jsx) |
| Pulso .atm, janeiro–outubro/2026 | [Nota técnica, recortes e reprodução](entregas/atm-2026/LEIA-ME.md) | [Contagens](entregas/atm-2026/contagens_diarias_municipios.csv), [camadas](entregas/atm-2026/camadas/), [Remotion](remotion/src/atm-video.jsx) |
| Amazônia Legal e Xingu, 2018–2026 | [Proposta](entregas/amazonia-xingu/PROPOSTA.md), [coleta](entregas/amazonia-xingu/COLETA.md), [ingestão](entregas/amazonia-xingu/INGESTAO.md), [composição](entregas/amazonia-xingu/COMPOSICAO.md) | [Snapshot auditado](entregas/amazonia-xingu/snapshots/xingu-74d0fdff5980abae3d40/), [dados gráficos](remotion/src/xingu-dados.json), [Remotion](remotion/src/xingu-video.jsx) |
| Fogo no Xingu — quatro vídeos de 60 segundos (V2) | [Storyboard V2](novo%20video/STORYBOARD-V2.md), [Storyboard V1](novo%20video/STORYBOARD-4-VIDEOS.md), [guia](novo%20video/serie-4-videos/LEIA-ME.md), [falas adaptadas](novo%20video/serie-4-videos/script.json) | Cada pasta de episódio contém SPEC, REVIEW, ledger, roteiro, storyboard, legendas, cenas HTML, mapas SVG e relatórios (`check.json` com 0 erros e 0 avisos) |

Os quatro episódios (V2) são: [O alerta](novo%20video/serie-4-videos/episodio-1/SCRIPT.md), [A época](novo%20video/serie-4-videos/episodio-2/SCRIPT.md), [Os picos](novo%20video/serie-4-videos/episodio-3/SCRIPT.md) e [A comparação](novo%20video/serie-4-videos/episodio-4/SCRIPT.md).

## Fontes, recortes e interpretação

As fontes e URLs registradas nos documentos originais estão em [FONTES.md](FONTES.md). As datas de consulta, hashes e disponibilidades constam das auditorias e manifestos de cada edição. Este acervo preserva o registro da produção; os conteúdos externos não foram consultados novamente durante o empacotamento.

- Focos de calor: INPE / Programa Queimadas. Limites municipais: IBGE / Amazônia Legal 2024.
- Altamira usa dias de Brasília e múltiplos sensores. A edição .atm seleciona NOAA-20. O Xingu usa AQUA_M-T e dias UTC; outubro está limitado a 1–26 nos comparativos de 2025/2026. Essas séries têm recortes diferentes.
- Detecções não representam incêndios únicos, área queimada, qualidade do ar ou identificação de responsáveis. Ausência de arquivo não equivale a zero.
- A série de quatro episódios usa o snapshot `xingu-74d0fdff5980abae3d40`. Os relatórios e especificações em `novo video/serie-4-videos/` registram a versão V2 renderizada com HyperFrames (0 erros e 0 avisos no `hyperframes check`).

## Integridade e rastreabilidade

[manifesto-arquivos.csv](manifesto-arquivos.csv) registra caminho, tamanho e SHA-256 de todos os arquivos do acervo, exceto o próprio manifesto. [videos-locais.csv](videos-locais.csv) identifica os MP4 encontrados, com tamanho e hash, sem duplicar os vídeos no Git. [ORGANIZACAO.json](ORGANIZACAO.json) registra escopo e omissões.

## Reprodução e limites do pacote

Os scripts e dependências declaradas foram preservados. Veja [Remotion](remotion/README.md), os guias de cada edição e os arquivos `requirements*.txt`. É um acervo de informações e insumos selecionados; não é uma distribuição completa de renderização offline.

Ficaram fora os MP4, ZIPs redundantes, bancos SQLite, bases nacionais completas das demais edições, caches, executáveis, ambientes virtuais, áudio WAV, quadros de revisão e fontes proprietárias Segoe UI. A captura original do alerta e suas cópias não foram publicadas: o nome da destinatária estava oculto somente na composição. Para reproduzir as cenas, use uma captura anonimizada, fontes com permissão de uso e regenere a narração conforme o guia. Os HTMLs e scripts originais ainda referenciam esses insumos ausentes.

Os oito CSVs diários de origem de Altamira estão preservados em `entregas/altamira/fontes/`. As malhas completas e os demais downloads de origem devem ser obtidos pelas fontes documentadas; os agregados, pontos e geometrias do snapshot foram incluídos. O sobrevoo MP4 de Altamira também deve ser recuperado ou reconstruído no projeto original. Notas antigas podem mencionar arquivos locais que não integram este pacote. O inventário é a referência do que foi publicado.

## Créditos e direitos

Preservam-se os créditos INPE, IBGE, Esri, Cesium, NASA e das bibliotecas nas notas originais. A publicação não atribui uma nova licença aos materiais de terceiros. Consulte as condições das fontes antes de redistribuir imagens, marcas ou bibliotecas.
