# Fogo no Xingu — quatro episódios

Série baseada no storyboard aprovado em `../STORYBOARD-4-VIDEOS.md`. Cada vídeo tem um minuto, resolução Full HD horizontal, narração brasileira sintetizada offline e legendas incorporadas à imagem.

## MP4 finais

1. `renders/01-o-aviso.mp4` — a mensagem recebida e a relação entre incêndios, fumaça e saúde.
2. `renders/02-o-contexto.mp4` — mapas da Amazônia Legal entre 2020 e 2026, estiagem e El Niño.
3. `renders/03-os-picos-no-xingu.mp4` — seis datas selecionadas pelos maiores totais diários, em ordem cronológica.
4. `renders/04-comparacao-e-responsabilidade.mp4` — períodos equivalentes de 2025/2026 e artigo 41 da Lei de Crimes Ambientais.

## Conteúdo e leitura

Uma informação principal por cena. A data e o total permanecem visíveis durante cada dia selecionado. No episódio 3, cada fala de data/valor foi gravada separadamente para coincidir com a tela. Os números são focos detectados, sem representação de hectares queimados. Outubro está limitado aos dias 1–26 nos dois anos comparados, UTC. A captura de alerta é anterior ao corte dos dados e não se atribui seu envio a registros posteriores.

A saudação com nome da destinatária está coberta por máscara opaca na composição. A captura original foi preservada. A voz é Microsoft Maria Desktop, pt-BR; nenhuma narração depende de conexão externa. Sem música para priorizar a clareza da fala.

## Arquivos editáveis

Cada pasta `episodio-N` contém a composição HyperFrames `index.html`, as cenas, os assets locais, `SCRIPT.md`, as legendas `legendas.srt`, os tempos de palavras e relatórios de áudio e verificação visual. `script.json` contém as adaptações de fala feitas para caber nas cenas. As contagens usam o snapshot local `xingu-74d0fdff5980abae3d40`.

As geometrias históricas foram simplificadas exclusivamente para desenho, com tolerância de 0,24 na projeção gráfica 0–1000. Os dados, limites usados na atribuição municipal e contagens não foram alterados. As cenas regionais mantêm os caminhos originais.

## Reproduzir

Da raiz do repositório:

```powershell
# Usa a voz instalada no Windows; não envia texto à rede.
& 'novo video/serie-4-videos/narrate-offline.ps1'
.venv/Scripts/python.exe 'novo video/serie-4-videos/build.py'
```

Para conferir e renderizar um episódio, dentro da pasta dele, com HyperFrames 0.8.171:

```powershell
$taskSeriesRoot = Split-Path (Get-Location).Path -Parent
$env:PATH = (Join-Path $taskSeriesRoot 'tools') + ';' + $env:PATH
$env:XDG_STATE_HOME = Join-Path $taskSeriesRoot '.runtime/state'
$env:XDG_CACHE_HOME = Join-Path $taskSeriesRoot '.runtime/cache'
hyperframes check
hyperframes render --fps 30 --quality delivery --workers 2 --output ../renders/episodio-revisado.mp4
```

`verify.py` verifica os quatro arquivos finais com FFprobe, decodifica todos os quadros, verifica áudio e gera as pranchas de quadros extraídos dos próprios MP4. O resultado fica em `renders/verificacao.json`.

Os avisos de organização da faixa de legendas no Studio foram revisados: as legendas são elementos separados, por escolha de edição. Os checks de layout e contraste precisam passar sem erros. A consulta de uso e a atualização online de skills estavam indisponíveis; a produção usa a versão local instalada e as referências locais lidas durante a execução.
