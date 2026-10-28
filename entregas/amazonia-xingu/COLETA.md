# Coletor INPE — Amazônia Legal e Xingu

Implementado em `scripts/coletar_xingu.py`, para o contrato de `projeto.json`. Esta etapa coleta e valida os arquivos nacionais originais. Não publica a aplicação, não importa detecções na base planejada e não renderiza vídeos.

## Primeira execução — 27/10/2026

A coleta online inicial terminou com **42 fontes e zero falhas**: oito ZIPs anuais, dois CSVs mensais e 32 CSVs diários. O arquivo local preserva 44 versões, incluindo as cópias anteriores do mensal de outubro e do diário de 15/10.

O mensal de outubro atualizado contém 817.859 linhas nacionais multissatélite e observações até `2026-10-26T23:50:00Z`. O diário de 27/10 chega a `2026-10-27T11:40:00Z` e é parcial. Esses horários descrevem observações presentes, não um corte científico já validado para o vídeo.

O resultado está em [coleta/ultima_coleta_ok.json](coleta/ultima_coleta_ok.json). As 36 verificações Python passaram; para os testes de vídeo existentes, foi usada a cópia de `ffprobe.exe` já instalada em `remotion/node_modules/@remotion/compositor-win32-x64-msvc`, adicionada ao PATH somente no processo de teste.

## Executar

Na raiz do repositório, com as dependências de `requirements.txt` já instaladas:

```powershell
# Coleta online até a data UTC da execução
.venv/Scripts/python.exe scripts/coletar_xingu.py

# Limita o relatório e a seleção de arquivos diários ao dia informado
.venv/Scripts/python.exe scripts/coletar_xingu.py --ate 2026-10-27

# Arquiva e valida somente os arquivos locais; não declara consulta online
.venv/Scripts/python.exe scripts/coletar_xingu.py --local --ate 2026-10-27

# Testes do coletor e da estrutura
.venv/Scripts/python.exe -m unittest tests.test_coletar_xingu tests.test_estrutura_xingu -v
```

`--ate` é uma data UTC inclusiva. Não aceita datas futuras. Os arquivos mensais/anuais são preservados integralmente, mesmo que contenham observações posteriores ao corte solicitado. O corte não modifica os arquivos originais e não representa certificação de cobertura até aquele dia.

O coletor pode ser executado novamente para buscar atualizações. Não há agendamento automático nesta entrega. Após o fim de outubro, repetir a coleta quando o INPE disponibilizar arquivos atualizados/consolidados.

## Fontes e escopo

Os endereços são fixos e pertencem ao [repositório oficial do INPE](https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/):

| Conjunto | Arquivos selecionados |
|---|---|
| `anual/Brasil_sat_ref/` | Oito ZIPs de referência, 2018–2025 |
| `mensal/Brasil/` | Setembro e outubro de 2026, quando o início do mês já estiver dentro do corte |
| `diario/Brasil/` | CSVs de setembro/outubro de 2026 presentes no catálogo diário e até o corte |

O catálogo diário pode não manter o mês inteiro. Os arquivos mensais são coletados mesmo quando há diários; eles não são somados. O relatório identifica a sobreposição, preservando a conciliação para a etapa de ingestão.

Não são baixados lotes de dez minutos. A coleta mantém todos os satélites dos arquivos operacionais para preservar a fonte; o relatório registra separadamente as linhas AQUA_M-T. Filtragem definitiva, deduplicação, atribuição municipal e totais do vídeo serão feitos na ingestão.

## Arquivos produzidos

```text
dados-brutos/amazonia-xingu/       arquivo local de fontes; fora do Git
  objetos/<sha256>/<nome>         conteúdos imutáveis; versões anteriores preservadas
  catalogo.json                  última versão estruturalmente válida de cada fonte
  coleta.lock                    bloqueio temporário de execução simultânea

entregas/amazonia-xingu/coleta/
  execucoes/<id>.json             relatório de cada tentativa
  ultima_tentativa.json           resultado mais recente, inclusive falhas
  ultima_coleta_ok.json           última tentativa online sem falhas de aquisição
  ultima_coleta_local.json        última validação local sem falhas
```

Guardar `objetos/` junto com os relatórios: os hashes identificam os conteúdos exatos que a ingestão deverá consumir. Os relatórios não contêm as detecções completas. O arquivo de fontes não deve ser apagado como se fosse um cache descartável.

Parâmetros opcionais:

- `--raiz-fontes`: diretório dos arquivos originais já existentes, usado no modo local ou como recuperação após falha online; padrão: raiz do repositório.
- `--saida`: diretório do arquivo de fontes; padrão: `dados-brutos/amazonia-xingu`.
- `--relatorios`: diretório dos relatórios; padrão: `entregas/amazonia-xingu/coleta`.
- `--config`: configuração da edição; padrão: `entregas/amazonia-xingu/projeto.json`.

Arquivos internos usam caminhos relativos ao arquivo de fontes. `arquivo_raiz` no relatório indica onde ele estava na execução. Para mover o acervo a outra máquina, copiar tanto as fontes quanto os relatórios e fornecer o novo `--saida`.

## O que é validado

- Nome permitido e período nominal do arquivo; URLs construídas no domínio oficial.
- HTTPS, timeouts e até duas repetições para falhas transitórias.
- Revalidação condicional por ETag/Last-Modified quando disponíveis.
- Integridade do cache por SHA-256 antes de aceitar respostas HTTP 304; cache corrompido força download integral.
- Download por blocos, limite de tamanho e conferência de Content-Length quando aplicável.
- ZIP com um único CSV, sem extração de arquivos, limite de tamanho descompactado e leitura completa.
- Datas válidas dentro do período declarado; latitude/longitude numéricas e dentro de limites válidos.
- Coluna de satélite obrigatória nos arquivos operacionais, com valores não vazios.
- Datas mínima/máxima observadas, linhas por sensor e contagens brutas diárias nacionais em setembro/outubro.

Os ZIPs históricos locais não possuem coluna de satélite. Isso fica explícito como `serie_referencia_sem_coluna_sensor`: o coletor **não inventa uma contagem AQUA_M-T** para esses arquivos. A confirmação documental de sua referência continua necessária para a série final.

Arquivos diários com cabeçalho válido e zero linhas são aceitos. Anuais/mensais vazios são rejeitados para revisão. HTML de erro, ZIP inválido, datas fora da janela e downloads truncados não substituem fontes válidas.

## Como interpretar o relatório

`consulta_online_ok=true` significa que a tentativa online completou a aquisição/revalidação dos arquivos selecionados e consultou o catálogo diário sem erro. Não significa ausência de nuvens, falhas de passagem do satélite ou lacunas científicas; não significa que todo outubro está disponível.

`cobertura_dias` contém as 549 datas de setembro/outubro de 2018–2026:

| Estado | Interpretação |
|---|---|
| `arquivo_anual_validado` | Há ZIP anual estruturalmente válido; cobertura diária e identidade do sensor ainda precisam de validação |
| `arquivo_diario_validado` | Há arquivo diário estruturalmente válido; não certifica aquisição de todos os focos |
| `somente_mensal` | Há arquivo mensal, sem arquivo diário selecionado para o dia; dias sem registros permanecem desconhecidos |
| `dia_em_andamento` | Dia UTC atual, necessariamente parcial |
| `ausente` | Nenhuma fonte selecionada disponível |
| `fora_do_corte` | Dia posterior ao `--ate`, mas já ocorrido |
| `futuro` | Dia ainda não ocorrido em UTC |

`registros_sensor_alvo` contabiliza linhas **nacionais, brutas, não deduplicadas**, na fonte preferida: diário, depois mensal, depois anual. Não somar registros de fontes sobrepostas. Esses números não são totais da Amazônia Legal ou do Xingu.

Um dia vazio em arquivo diário validado pode ter zero linhas. Ausência de linhas num mensal/anual não certifica dia com zero: permanece `null`. Dias futuros e fora do corte também permanecem `null`. Toda linha do relatório preserva `cobertura_cientifica_validada=false`.

## Falhas e retomada

O processo retorna código `0` para coleta sem falhas de aquisição/validação estrutural e `1` quando há falhas. No modo local, sucesso continua identificado como local.

Em falha online, o coletor tenta preservar uma cópia local válida, registra o erro e marca `consulta_online_ok=false`. `ultima_coleta_ok.json` não é substituído por uma tentativa com erro. Downloads válidos já concluídos continuam arquivados e podem ser revalidados na próxima execução.

Cada relatório em `execucoes/` é preservado. A seleção entre versões de um mesmo arquivo, a reconciliação mensal/diário e o fechamento do corte científico pertencem ao futuro snapshot de ingestão.

O bloqueio impede dois processos de escrever simultaneamente no mesmo arquivo de fontes. Se uma interrupção abrupta deixar `coleta.lock`, verificar primeiro que nenhum coletor está em execução antes de removê-lo.

## Próxima etapa

Consumir os hashes do relatório para importar focos, confirmar a série de referência, deduplicar e espacializar na malha IBGE 2024. Depois, validar cobertura e gerar os agregados e assets descritos em [PROPOSTA.md](PROPOSTA.md). A existência de um relatório de aquisição bem-sucedida não libera, por si só, os comparativos científicos do vídeo.

Essa etapa de ingestão já foi implementada e executada: consultar [INGESTAO.md](INGESTAO.md) para os resultados, o corte e os comandos.
