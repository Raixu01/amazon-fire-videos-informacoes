# Base importada — Amazônia Legal e Xingu

A ingestão foi executada em 27/10/2026 a partir do manifesto da coleta online de 42 arquivos. Foram gerados a base SQLite, os agregados e os dados geográficos necessários à próxima etapa do vídeo.

## Resultado desta execução

- **475.012 focos únicos** dentro da Amazônia Legal em setembro/outubro de 2018–2026, com 2026 limitado ao corte abaixo.
- **32.054 repetições entre fontes** removidas antes da espacialização, preservando a relação de cada observação com seus arquivos de origem.
- **Zero divergências** entre as assinaturas AQUA_M-T dos arquivos mensais e diários nas datas sobrepostas.
- **13.914 linhas** no histórico municipal: 773 municípios × 9 anos × 2 meses.
- **610 linhas** no diário do Xingu: 10 municípios × 61 datas planejadas; datas fora do corte permanecem nulas.
- **3.688 focos no Xingu em 2026** para setembro completo e 1–26 de outubro.

O corte é `2026-10-27T00:00:00Z`, **fim exclusivo**. Não inclui as observações parciais de 27/10. Elas permanecem nos arquivos coletados e poderão entrar em outro snapshot após o fechamento e a validação do dia. Não se usou o horário do último foco como prova de completude.

| Janela do Xingu, UTC | 2025 | 2026 | Diferença | Variação |
|---|---:|---:|---:|---:|
| Setembro completo | 527 | 1.006 | +479 | +90,89% |
| Outubro, dias 1–26 | 586 | 2.682 | +2.096 | +357,68% |
| Soma das duas janelas | 1.113 | 3.688 | +2.575 | +231,36% |

Os números são focos de calor detectados, não incêndios únicos nem área queimada. Os dois anos usam a mesma malha, série e definição temporal. O detalhamento por município está em `comparativo.json` e no recibo.

## Arquivos disponíveis

O [recibo da última ingestão](ingestao/ultima_ingestao.json) identifica o diretório do snapshot, a base SQLite, os resultados e os hashes. A [verificação independente](ingestao/ultima_verificacao.json) registra a reconciliação dos produtos com a base.

Snapshot inicial: `xingu-74d0fdff5980abae3d40`, em `entregas/amazonia-xingu/snapshots/`.

| Arquivo no snapshot | Uso |
|---|---|
| `base.sqlite` | Base efetivamente importada, com detecções únicas, dimensões, cobertura e linhagem |
| `historico_municipal.parquet` / `.csv` | Setembro/outubro por município e ano; estado de cobertura e contagem observada |
| `historico_video.json` | Dezoito estados de mapa e uma única escala de cores para os dois painéis históricos |
| `xingu_diario.parquet` / `.csv` | Datas, municípios, contagens e estados para a evolução diária |
| `xingu_pontos.json` | Pontos por dia, apenas no Xingu, sem persistência entre datas |
| `comparativo.json` | Janelas equivalentes 2025/2026, totais e resultados por município |
| `municipios_amazonia.geojson` | Todos os 773 municípios para os painéis históricos |
| `municipios_xingu.geojson` | Somente os dez municípios confirmados, para a cena após o zoom |
| `auditoria.json` | Fontes, duplicatas, recorte espacial, ambiguidades, cobertura e reconciliação |
| `manifesto.json` | Identidade dos insumos, corte e hashes dos produtos |
| `recibo.json` | Identidade do snapshot e hashes finais, incluindo a base SQLite |

Os snapshots e arquivos grandes ficam fora do Git. A base `preparado/base_planejada.sqlite` continua sendo a estrutura inicial; a base com observações está no snapshot identificado pelo recibo. Não confundir as duas.

## Repetir o processamento

Da raiz do repositório, usando o ambiente e dependências existentes:

```powershell
.venv/Scripts/python.exe scripts/ingerir_xingu.py
.venv/Scripts/python.exe scripts/verificar_ingestao_xingu.py
```

O importador usa `coleta/ultima_coleta_ok.json`. O padrão inclui apenas dias encerrados antes do dia UTC em que aquela coleta começou. Um novo corte explícito deve estar à meia-noite UTC e não ultrapassar os dias fechados daquela coleta:

```powershell
.venv/Scripts/python.exe scripts/ingerir_xingu.py --corte-utc 2026-10-27T00:00:00Z
```

Para atualizar depois: executar novamente o coletor, confirmar que a coleta terminou sem falhas, repetir o importador e executar o verificador. Novas entradas ou código produzem outro ID de snapshot. Repetir exatamente os mesmos insumos reutiliza a versão existente após conferir seus hashes, sem duplicar observações.

Opções adicionais: `--config`, `--coleta`, `--saida`, `--relatorios` e `--fontes` permitem indicar a configuração, o manifesto, o diretório de snapshots, o diretório de recibos e a localização do arquivo de fontes. Não há consultas de rede durante a ingestão.

## Decisões de processamento

1. **Proveniência:** somente manifesto de coleta online sem falhas. Verificar cada SHA-256 antes de ler; selecionar a versão exata de cada fonte, independentemente do catálogo mutável do coletor.
2. **Sensor:** AQUA_M-T nos operacionais. Nos históricos sem coluna de sensor, associação documental restrita ao produto `Brasil_sat_ref` e aos anos permitidos em [referencia_sensor.json](referencia_sensor.json), fundamentada na [FAQ oficial do INPE, seção 7](https://data.inpe.br/queimadas/faq/). A auditoria distingue essa associação da identificação por linha.
3. **Tempo:** timestamp UTC normalizado, setembro/outubro e fim exclusivo. Não converter parte dos anos para horário de Brasília.
4. **Deduplicação:** SHA-256 de timestamp + coordenadas numéricas exatas + satélite; não usar o ID original como assinatura. Formatos numéricos equivalentes geram a mesma assinatura, sem arredondar posições distintas.
5. **Conciliação:** comparar conjuntos nacionais de assinaturas AQUA por dia entre mensal e diário. Divergência bloqueia a validação daquele dia e o comparativo correspondente. Fontes sobrepostas não são somadas.
6. **Espaço:** interseção com a malha analítica IBGE 2024, em EPSG:4326, incluindo pontos nos limites. Se um ponto tocar mais de um município, escolher o menor código IBGE e registrar a ambiguidade. Não aplicar buffer. Limites simplificados são usados somente nos arquivos de visualização.
7. **Linhagem:** guardar detecção canônica e todas as ligações com fontes, inclusive quando a mesma assinatura aparece em mensal e diário.

## Cobertura e significado de “validado”

Neste estágio, “validado” significa integridade e ingestão coerente do **produto de dados**, não certificação de todas as passagens de satélite ou de observações sob nuvens.

Um produto fechado requer nome e período coerentes, leitura de todas as linhas, hash correto, publicação indicada por Last-Modified posterior ao fim nominal, fim nominal dentro do corte e ausência de divergência mensal/diária. Para os dias antigos sem diário retido, um mensal já fechado ou o anual de referência sustenta a cobertura de ingestão.

O mensal de outubro ainda em andamento não certifica sozinho cada dia anterior. Nesta execução, os arquivos diários fechados sustentam 1–26/10. O dia 27 fica `nao_validado` por estar fora do corte; 28–31/10 ficam `futuro`, conforme a data da coleta. Esses estados não viram zero e não recebem pontos no JSON de exibição.

Outubro de 2026 fica marcado como **parcial** nos agregados mensais. O comparativo de 1–26/10 está validado como janela equivalente; isso não transforma o mês inteiro em período completo. O histórico 2025 pode mostrar outubro inteiro no painel anual, enquanto o cartão comparativo usa somente 1–26/10/2025, com rótulo explícito.

## Verificação

Os testes cobrem equivalência de coordenadas, preservação de posições distintas com ID repetido, sensor documental, fronteiras, diário vazio, divergências, janelas equivalentes, base percentual zero, integridade, linhagem, ausência versus zero, reexecução e preservação da versão anterior diante de hash alterado.

```powershell
.venv/Scripts/python.exe -m unittest tests.test_ingerir_xingu -v
```

A suíte Python completa passou com **45 testes**, incluindo os coletores e as verificações existentes. Nos testes antigos de vídeo, foi usada a cópia de `ffprobe` instalada junto ao Remotion, no PATH do processo de teste.

O verificador independente confere os hashes finais, integridade SQLite, unicidade, totais em Parquet, valores municipais em JSON, pontos por dia, recorte geográfico do Xingu e comparativos por consultas SQL.

## Próxima etapa

Implementar a composição visual consumindo **um único snapshot**: os dois mapas históricos, a aproximação para o Xingu, os estados diários e os três cartões comparativos. A base e os produtos de dados estão preparados; a composição nova e o MP4 ainda não foram produzidos nesta etapa.

**Atualização:** a [composição visual](COMPOSICAO.md) foi implementada na etapa seguinte, usando este snapshot.
