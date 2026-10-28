# Pulso — Amazônia Legal e Xingu: setembro e outubro, 2018–2026

Proposta e estrutura preparadas em 27/10/2026. Recorte do Xingu confirmado pelo usuário: dez municípios da Região de Integração Xingu. A entrega desta etapa é a estrutura da base e do futuro vídeo; ingestão, atualização online, composição visual e renderização do MP4 ficam para execução posterior.

**Atualização:** o [coletor de fontes](COLETA.md) foi implementado após esta proposta e já permite aquisição online, validação estrutural e arquivamento de versões. A ingestão na base, validação científica da cobertura e composição/renderização do vídeo continuam como etapas posteriores. O diagnóstico abaixo descreve os insumos anteriores à nova coleta; consultar os relatórios em `coleta/` para o estado mais recente.

**Atualização seguinte:** a [ingestão da base e os agregados](INGESTAO.md) foram implementados e executados, com corte em 27/10/2026 às 00h UTC, fim exclusivo. Consultar `ingestao/ultima_ingestao.json` e `ingestao/ultima_verificacao.json` para a versão importada. A composição visual e a renderização continuam como etapas posteriores.

## 1. Resultado proposto

Um filme de **2min30s, Full HD, 30 fps**, com dois níveis de leitura:

1. **Amazônia Legal, 2018–2026:** setembro à esquerda e outubro à direita, simultâneos. Os dois painéis avançam juntos, um ano a cada cinco segundos, mantendo todos os limites municipais.
2. **Xingu, setembro e outubro de 2026:** aproximação contínua, desaparecimento dos limites dos demais municípios e evolução de um dia por segundo. Encerramento com totais de 2025 e 2026 para períodos equivalentes.

O título editorial pode mencionar incêndios, mas mapas, legendas e números usarão **“focos de calor detectados”**. Detecções não representam incêndios únicos ou hectares queimados. A [FAQ do INPE](https://data.inpe.br/queimadas/faq/) descreve a interpretação dos focos e as diferenças entre sensores.

O recorte confirmado coincide com os dez municípios listados pelo [MIDR para o PDRS Xingu](https://www.gov.br/mdr/pt-br/assuntos/desenvolvimento-regional/pdrsx/pdrsx). Não é um recorte da bacia hidrográfica inteira do rio Xingu.

## 2. Diagnóstico dos insumos locais

- A malha analítica IBGE 2024 já preparada contém **773 municípios** da Amazônia Legal. As geometrias analíticas e as de visualização estão separadas.
- Há oito ZIPs de referência, de 2018 a 2025; CSVs mensais de setembro/outubro de 2026; e quinze CSVs diários de outubro de 2026. O inventário gerado registra **25 arquivos locais**, com tamanho e SHA-256.
- O CSV mensal de outubro de 2026 tem 507.526 registros multissatélite; os horários vão de `2026-10-01 00:00:00` até `2026-10-14 23:50:00` UTC. Ele inclui AQUA_M-T. Isso descreve o conteúdo do arquivo; não certifica cobertura completa desses dias.
- Existem arquivos diários até 15/10 na raiz, ainda sem conciliação nesta proposta. Não se deve tomar o dia 14 como corte automático, nem supor que os dados locais estejam atualizados até a data desta proposta.
- A edição atual usa NOAA-20. Os ZIPs históricos são de referência e alguns não trazem coluna de satélite. Portanto, concatenar os dados da edição atual aos históricos produziria uma comparação inadequada.

O inventário comprova existência e identidade dos arquivos, não a validade científica ou a completude deles. As datas de modificação locais não serão tratadas como datas de download.

## 3. Contrato da série

| Decisão | Regra proposta |
|---|---|
| Série principal | AQUA_M-T em todos os anos, meses e comparações; confirmar a identificação nos metadados das fontes de referência antes da ingestão |
| Se o sensor não estiver disponível | Registrar ausência e bloquear a comparação afetada; não substituir por NOAA-20 ou somar sensores |
| Tempo | Armazenar timestamps UTC; agregar todo o filme em dias/meses UTC e informar isso nos créditos e nas cenas diárias |
| Intervalos | Início inclusivo, fim exclusivo; setembro = `[01/09, 01/10)`; outubro = `[01/10, 01/11)` |
| Território | Mesma malha IBGE Amazônia Legal 2024 para toda a série; não misturar mudanças anuais de limites |
| Espacialização | Geometria analítica original; associação única por ponto. Nos limites compartilhados, registrar ambiguidade e resolver deterministicamente pelo menor código IBGE, sem duplicar contagens |
| Duplicidade | Timestamp UTC + latitude + longitude + satélite, com coordenadas normalizadas sem arredondamento adicional. Preservar IDs e todas as fontes de origem |
| Dados operacionais | Mensais e diários podem se sobrepor: conciliar, deduplicar e manter linhagem; não somar arquivos como se fossem conjuntos distintos |
| Ausência | `NULL` para dado não validado, ausente ou futuro; zero apenas em período com ingestão validada e nenhuma detecção |
| Parcial | Exibir número observado com etiqueta “parcial até … UTC”; não apresentá-lo como total mensal definitivo |

A escolha de UTC preserva a definição temporal do histórico existente e evita misturar os diferentes fusos da Amazônia Legal. Uma futura edição em horário de Brasília exigirá reprocessar **todos** os anos, inclusive observações das bordas dos meses. Não basta mudar o rótulo.

A FAQ do INPE identifica AQUA_M-T como referência e explica descontinuidades entre sensores, mas contém trechos datados. Por isso a proposta exige verificar os metadados vigentes na execução, em vez de assumir que a referência operacional nunca mudou.

## 4. Organização dos dados

```text
entregas/amazonia-xingu/
  PROPOSTA.md                  decisões, roteiro e execução posterior
  projeto.json                 parâmetros e contrato temporal/visual
  base.sql                     esquema SQLite executável
  preparado/
    base_planejada.sqlite      estrutura local + municípios + inventário
    inventario.json            fontes encontradas e hashes
    calendario_esperado.csv     549 datas esperadas: 9 anos × 61 dias
    timeline.json              76 segmentos; 4.500 frames
    preflight.json             verificações e pendências
  snapshots/<id>/              FUTURO: corte imutável, fontes e auditoria
  assets/<snapshot_id>/        FUTURO: mapas, pontos e gráficos offline
  pulso-amazonia-xingu-2018-2026.mp4   FUTURO: render final
```

Os arquivos brutos existentes podem permanecer na raiz, conforme a convenção atual. Novos downloads devem ser arquivados com hash, URL, instante de obtenção e cabeçalhos disponíveis; cada snapshot referencia exatamente os conteúdos utilizados. Republicações não devem apagar as fontes de versões anteriores.

### Modelo relacional

| Tabela/view | Conteúdo e chave |
|---|---|
| `projeto` | Configuração versionada |
| `municipio` | Código IBGE, nome, UF, malha e referências às duas geometrias |
| `regiao`, `regiao_municipio` | Amazônia Legal e seus 773 municípios; Xingu e seus dez membros |
| `fonte` | Caminho, URL, hash, tamanho, estado de validação e metadados de aquisição |
| `snapshot`, `snapshot_fonte` | Corte UTC, sensor, malha, estado e conjunto exato de fontes |
| `foco` | Uma detecção canônica por snapshot e assinatura de deduplicação |
| `foco_fonte` | Linhagem das detecções em um ou mais arquivos |
| `cobertura_dia`, `cobertura_fonte` | Estado de cada dia/região e fontes que justificam sua cobertura |
| `diario_municipal` | Contagem por dia e município, preservando ausências como `NULL` |
| `mensal_municipal` | Total observado, dias validados/esperados e estado mensal |
| `render` | Snapshot, configuração, revisão do código, caminho/hash do MP4 e relatório visual |

Geometrias ficam nos arquivos geográficos, evitando duplicação em milhares de observações. `#codigo_ibge` nas referências da base é um seletor lógico de feição, não um caminho de arquivo separado.

O preparador inicializa dimensões e inventaria fontes. **Não cria snapshot, não importa focos e não certifica cobertura.** As tabelas de observação permanecem vazias. Isso impede que uma base apenas planejada pareça uma base já atualizada.

### Contrato dos dados que alimentarão a composição

O exportador futuro deverá produzir estes arquivos dentro de um único snapshot:

| Arquivo | Granularidade / campos essenciais |
|---|---|
| `manifesto.json` | ID, gerado UTC, corte UTC, sensor, fuso, malha, hashes, estado das 18 janelas e escala de cores fixa |
| `municipios_amazonia.geojson` | Todas as feições municipais simplificadas com código IBGE |
| `municipios_xingu.geojson` | Somente as dez feições do Xingu; sem limites externos |
| `historico_municipal.parquet` | 773 × 9 × 2 = **13.914 linhas**: município, ano, mês, focos observados, cobertura, corte |
| `historico_video.json` | 18 estados de mapa; totais regionais e valores municipais; ausências explícitas |
| `xingu_diario.parquet` | 10 × 61 = **610 linhas**: município, dia UTC, total, estado de cobertura |
| `xingu_pontos.json` | Partições diárias de pontos `[longitude, latitude, codigo_ibge]`, somente do sensor escolhido e dentro do recorte |
| `comparativo.json` | Setembro, outubro e conjunto; 2025/2026, início/fim de cada janela, totais, diferença absoluta, percentual, estado; também detalhamento municipal |
| `auditoria.json` | Duplicatas, rejeições, pontos ambíguos, fontes, cobertura diária e reconciliação de totais |

Exportar apenas do snapshot validado, com todos os assets resolvidos localmente. O render não deve consultar dados online ou misturar arquivos regenerados durante sua execução.

## 5. Passagem do tempo e roteiro

| Tempo | Cena | Leitura e comportamento |
|---|---|---|
| 00:00–00:06 | Abertura | “Do panorama da Amazônia Legal ao cotidiano do Xingu”; explicar setembro/outubro e focos detectados |
| 00:06–00:51 | Histórico | Nove estados de cinco segundos: 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026; dois mapas simultâneos |
| 00:51–00:57 | Zoom | Partir do painel de outubro/2026; destacar Xingu, expandir o painel e aproximar até enquadrar os dez municípios |
| 00:57–01:01 | Setembro no Xingu | Apresentar calendário diário e legenda dos pontos |
| 01:01–01:31 | Setembro diário | 01–30/09/2026, um segundo por dia |
| 01:31–01:35 | Outubro no Xingu | Reiniciar a régua no primeiro dia do novo mês |
| 01:35–02:06 | Outubro diário | 01–31/10/2026, um segundo por dia |
| 02:06–02:24 | Comparativo | Seis segundos por cartão: setembro, outubro, soma das duas janelas equivalentes |
| 02:24–02:30 | Créditos | INPE, IBGE 2024, corte UTC, sensor, definição territorial e limitações |

### Histórico: dois mapas como um relógio único

- Setembro permanece sempre à esquerda, outubro à direita. Mesmos limites, escala geográfica, tamanho e posição das feições.
- Uma régua central `2018 … 2026` destaca o ano corrente; o marcador percorre cada intervalo durante os cinco segundos e ambos os mapas trocam juntos. Não inverter anos ou alternar os meses em tela cheia.
- Em cada ano: aproximadamente 0,4 s para a mudança de destaque e 4,6 s de leitura. Manter o mapa estável; atualizar preenchimentos e contadores sem misturar detecções de anos diferentes.
- **Todos os municípios delineados em todos os anos.** Linhas finas com contraste suficiente em 1080p. Não esconder limites nos municípios sem focos; esses continuam visíveis.
- Preenchimento por contagem mensal municipal; uma única escala de cores para os 18 mapas, calculada após a validação. Não renormalizar a legenda a cada ano. Reservar um tom neutro para zero e hachura para indisponível.
- Total do mês sob cada painel. Em 2026, outubro recebe o selo de parcial caso necessário. Não animar números interpolados como se fossem observações reais.
- Os meses foram selecionados pelo briefing como período de interesse. Evitar afirmar que são os dois maiores de todos os anos sem validar esse ranking na série anual completa.

### Zoom: selecionar o território enquanto a câmera se aproxima

No início, os dez municípios ganham contorno de destaque nos dois painéis. O painel de outubro ocupa a tela; sua câmera interpola do enquadramento amazônico ao bounding box conjunto do Xingu, com margem. O restante dos limites municipais perde opacidade **simultaneamente** ao zoom. Os dez limites do Xingu permanecem contínuos, sem cortes durante o movimento.

Ao fim, o mapa mostra somente os dez polígonos delineados; áreas externas podem ter um fundo neutro sem divisões municipais. Remover também pontos externos. Os nomes dos dez municípios entram ao terminar o movimento, com rótulos/linhas de chamada posicionados para evitar colisões. A transição deve terminar em um enquadramento fixo, mantido durante os dois meses diários.

### Diário: um dia de cada vez

Uma data grande (`DD/MM/2026 · UTC`), régua de 30/31 dias e contador “focos neste dia” tornam a passagem legível. Ao mudar a data, substituir integralmente os pontos: sem rastros ou persistência que pareçam fogo ainda ativo. Um gráfico diário abaixo do mapa preserva o histórico e destaca a barra corrente; o mapa mostra apenas o dia selecionado.

O acumulado pode aparecer em um contador separado, identificado como “acumulado do mês”. Não confundi-lo com os focos desenhados. Manter tamanho/cor dos pontos e escala do gráfico constantes entre os meses. Dia sem detecção validada = `0`; lacuna = “dados indisponíveis”; futuro = “ainda não observado”, sem pontos e sem contador zero.

Os 61 segundos diários estão reservados para a edição completa. Um render definitivo exige validar todos os dias; eventual prévia parcial precisa declarar o corte e identificar os slots sem dados, sem projetar valores para o futuro.

## 6. Comparação 2025 × 2026

Apresentar dois valores lado a lado, diferença absoluta e variação percentual para cada cartão:

1. **Setembro:** mês completo se ambos estiverem validados; caso contrário, restringir os dois anos ao mesmo intervalo validado.
2. **Outubro:** mês completo apenas após fechamento e validação. Na edição parcial, comparar `01/10/2026 00:00 UTC → corte` com `01/10/2025 00:00 UTC → mesmo dia/hora de 2025`.
3. **Setembro + outubro:** somar exatamente as janelas mostradas nos dois primeiros cartões. Rotular “soma das janelas comparadas” se houver período parcial.

Fórmulas: `diferença = N2026 − N2025`; `% = 100 × (N2026 − N2025) / N2025`. Se N2025 = 0, mostrar “variação percentual não calculável” e manter a diferença absoluta; se algum total for desconhecido, usar “comparação indisponível”. Não apresentar aumento/redução em porcentagem nesses casos.

Não comparar outubro parcial com outubro inteiro de 2025. Havendo lacuna interna em qualquer ano, bloquear a comparação padrão e documentar a lacuna; não removê-la silenciosamente para criar uma janela supostamente contínua. Os somatórios municipais, regionais e os pontos exportados devem reconciliar por dia e período.

## 7. Execução disponível agora

Da raiz do repositório, sem novas dependências:

```powershell
.venv/Scripts/python.exe scripts/preparar_estrutura_xingu.py
.venv/Scripts/python.exe -m unittest tests.test_estrutura_xingu -v
```

O comando cria a base planejada, lê a malha visual existente, cadastra os municípios, calcula hashes dos arquivos locais e gera calendário/timeline. Pode ser repetido com a mesma configuração sem duplicar cadastros. `--raiz-fontes C:/caminho` muda a localização dos CSVs/ZIPs; `--saida C:/caminho` cria outra estrutura. Se a configuração mudar, usar outro diretório de saída para preservar a base anterior.

Os arquivos gerados são planos, não assets prontos para o Remotion. O preflight registra explicitamente as etapas de processamento e render ainda pendentes. As edições publicadas e composições existentes não são alteradas.

## 8. Sequência para executar a atualização e gerar o MP4 depois

1. **Coletar:** verificar/reobter referências de 2018–2025 e mensais/diários de 2026 necessários; arquivar conteúdos e metadados. Revisitar outubro após 31/10 e após a disponibilização do consolidado, sem presumir publicação imediata.
2. **Normalizar:** adaptar schemas antigos/atuais, confirmar AQUA_M-T nos históricos sem campo de satélite, rejeitar datas/coordenadas inválidas, deduplicar, espacializar pela malha analítica e registrar ambiguidades. Usar dados de referência para todos os dias de 2025, incluindo o corte horário equivalente se a versão for parcial.
3. **Validar cobertura:** preencher todas as 549 datas esperadas por região/snapshot, inclusive ausências e dias futuros. Registrar o fim efetivamente coberto; o timestamp do último foco não comprova que o arquivo está completo.
4. **Fechar snapshot:** definir corte, verificar sensor/fuso/malha e reconciliar contagens. Exportar os contratos da seção 4. Se os dois meses estiverem incompletos, impedir o selo de edição definitiva.
5. **Construir a composição:** adicionar futuramente `remotion/src/xingu-video.jsx` e uma composição `PulsoAmazoniaXingu`, preservando as atuais; implementar as cenas de `projeto.json` e consumir os assets do snapshot. Reaproveitar o renderizador Remotion instalado, sem migrar o projeto para outro framework.
6. **Verificar quadros:** selecionar os nove anos, último dia de setembro, primeiro de outubro, dia sem dados, fim do zoom e três cartões comparativos. Confirmar ausência de limites/pontos externos no Xingu, delineamento dos 773 municípios no histórico, legibilidade e ausência de erros de console.
7. **Renderizar:** H.264, yuv420p, 1920×1080, 30 fps, 4.500 frames, concorrência 1 inicialmente. Conferir reprodução, duração, dimensões, texto, mapas e hash final; registrar em `render`.

Comando **futuro**, válido somente após implementar e registrar a composição e seus assets:

```powershell
cd remotion
npx remotion render src/index.jsx PulsoAmazoniaXingu ../entregas/amazonia-xingu/pulso-amazonia-xingu-2018-2026.mp4 --codec h264 --pixel-format yuv420p --concurrency 1
```

Não executar esse comando nesta etapa: a composição nova ainda não existe. Nenhum MP4 foi gerado por esta preparação.

## 9. Critérios de aceite da futura edição

- Exatamente nove anos e dois painéis simultâneos; limites municipais presentes nos 18 mapas.
- Mesma escala, malha, sensor e fuso em toda comparação.
- Ao terminar o zoom, exatamente os dez municípios do Xingu delineados; demais limites e focos removidos.
- Sessenta e um estados diários previstos, com ausência/futuro distintos de zero e sem persistência de focos entre dias.
- Comparações numéricas verificáveis por consultas à base e intervalos explícitos iguais entre os anos.
- MP4 reproduzível a partir de snapshot identificado, sem downloads durante o render; duração de 150 s na edição completa.

A estrutura desta etapa foi verificada com inicialização SQLite, integridade referencial, testes de deduplicação/sensor, preservação de nulos, completude mensal e continuidade dos 4.500 frames. A validação científica dos dados e a inspeção visual pertencem à execução posterior.
