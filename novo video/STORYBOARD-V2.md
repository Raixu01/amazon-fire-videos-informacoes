# Fogo no Xingu — Storyboard V2 (4 × 60 s)

Versão focada em **baixa carga cognitiva** e **narrativa contínua**. Substitui, como guia de edição, o [STORYBOARD-4-VIDEOS.md](STORYBOARD-4-VIDEOS.md), que permanece como registro. Público: moradores do Xingu, sem conhecimento técnico. Formato 1920 × 1080, sem música, voz brasileira, legendas embutidas.

Decisões aprovadas: a montagem 2020–2026 sai do vídeo 2 (vai para o material de apoio da publicação); sem música.

## Correções factuais (inalteradas)

Valem integralmente as seis correções do storyboard original:

1. Captura `aviso_queimadas_gov.png`: conversa GovBR de **11/10/2026**, nome da destinatária oculto. Não atribuir o envio a nenhum limiar ou número deste estudo.
2. Recorte: mapas de **Amazônia Legal**; detalhe regional = **Região de Integração Xingu, 10 municípios do Pará**.
3. El Niño: **em curso** (boletim NOAA de 08/10/2026). Em 2025, sem El Niño no período.
4. Causa: o clima aumenta o risco; **não prova** a causa do aumento nem aponta autores.
5. Medida: **focos de calor detectados (AQUA_M-T)**, não incêndios únicos, área queimada, desmatamento ou qualidade do ar.
6. Período: setembro completo e **1–26/10**, em **UTC**. Outubro parcial; comparações usam os mesmos dias.

## Princípios

1. Uma pergunta por vídeo; uma ideia por cena.
2. Um número principal por tela, o maior elemento.
3. Fala ≤ 19 palavras por cena; a tela complementa, não repete.
4. Revelação progressiva: nada aparece antes de a voz nomear.
5. Foco por contraste: o resto fica a 25% de opacidade.
6. Cor fixa: âmbar = 2026; cinza-azulado = 2025; marfim = texto; verde-claro = apoio.
7. O mapa é ensinado uma vez (vídeo 2).
8. Pausa de 0,5 s antes de cada número-clímax.
9. Cada vídeo fecha com uma frase em tela.

## Fio narrativo: o ponto âmbar

Aviso (V1) → foco no mapa (V2) → pico no Xingu (V3) → comparação e volta ao celular (V4).

- **Corrente:** zoom para frente (aproximar). **Chegada:** recuo (Z para trás), só no fim do V4.
- **Carrier:** o ponto âmbar atravessa cada corte na mesma posição e velocidade. Sem crossfade.

### Transições (apenas três)

| # | Nome | Uso | Parâmetros |
|---|---|---|---|
| T1 | Zoom-through pelo ponto | Mudança de escala | ~0,6 s; saída `power3.in`, entrada `power3.out` |
| T2 | Troca com desfoque no mesmo palco | Mudança de conteúdo no mesmo mundo | saída 0,2 s blur 8 px; entrada 0,13 s |
| T3 | Recuo de chegada | Final do V4 | scale 1 → 0,6, blur máx. 6 px |

### Movimento

- Títulos: blur por palavra (6 px → 0, 0,13 s, defasagem 0,07 s); depois, parados.
- Barras: crescem da base zero, 0,6–0,8 s, `expo.out`; valores fixos, sem contagem intermediária.
- Pontos do mapa: lote por data, sem rastro acumulado.
- Destaque: halo âmbar fixo; resto a 25%. Sem pulso, sirene, chama, partículas, bounce ou três cartões em fileira.

### Visual

Fundo `#10282d`, marfim `#f5f1e8`, âmbar `#ffc277`, verde-claro `#abd5bd`; Segoe UI 700. Título 72–104 px; apoio 40–48 px; legenda 38–42 px. Conteúdo y=160–850; legenda y=900–1008. Selo fixo "Parte n de 4". Fonte e corte em rodapé: "Focos de calor detectados — INPE / AQUA_M-T • Setembro e 1–26/10/2026 • UTC".

---

## Vídeo 1 — O alerta
**Pergunta:** o que esse aviso está me dizendo? **Frase final:** "O aviso é sobre a fumaça."

| # | Tempo | Tela | Texto em tela | Motion | Fala |
|---|---|---|---|---|---|
| 1 | 0–6 | Frame 0 já é a captura real, com data 11/10/2026; aproxima o trecho do alerta, resto a 25%. | "Você também recebeu?" | Push 100→118%; blur por palavra. | "Você recebeu este aviso no celular? Sua região está sob alerta de incêndios." |
| 2 | 6–16 | Foco passa à frase sobre fumaça. | "A fumaça pode causar problemas respiratórios" | Pan vertical curto; destaque âmbar estático. | "O recado é sobre a fumaça. Ela pode chegar até a nossa casa." |
| 3 | 16–28 | Ícone do alerta solta um ponto âmbar; T1 revela a Amazônia Legal e marca o Xingu. | "Amazônia Legal" · "Xingu" | Zoom-through; contorno se desenha em 0,8 s. | "Mas de onde vem a fumaça? Do fogo. E, na estiagem, ele se espalha com mais facilidade." |
| 4 | 28–42 | Três passos, um por vez, mesma posição: folha seca → fogo → fumaça sobre casa. Rótulo "Ilustração". | "Seca · fogo · fumaça" | Cada ícone entra quando a voz o nomeia; o anterior recua a 25%. Sem trajetória real de fumaça. | "Vegetação seca, fogo, fumaça. Ela afeta a respiração, principalmente de crianças e idosos." |
| 5 | 42–52 | Fundo limpo, uma linha. | "Acompanhe os avisos oficiais" | Pausa 0,5 s; blur por palavra; parado. | "Por isso, vale acompanhar os avisos oficiais." |
| 6 | 52–60 | Ponto âmbar cresce sobre o mapa; selo "Parte 2". | "E os satélites, o que mostram?" | T1, saindo em movimento. | "E aqui na região, o que os satélites mostram? No próximo vídeo, o mapa." |

## Vídeo 2 — A época
**Pergunta:** por que o fogo preocupa agora? **Frase final:** "O clima aumenta o risco. Não explica tudo."

| # | Tempo | Tela | Texto em tela | Motion | Fala |
|---|---|---|---|---|---|
| 1 | 0–7 | Mapa da Amazônia Legal vazio. | "Por que agora?" | Blur por palavra. | "Por que o alerta chegou agora? Estamos na época de menos chuva." |
| 2 | 7–18 | Folha verde que seca; gota de chuva diminui. | "Menos chuva → vegetação mais seca" | Cor muda em 1,2 s `power2.inOut`; seta entra depois. | "Com menos chuva, a vegetação fica mais seca. O fogo encontra mais condições para se espalhar." |
| 3 | 18–32 | Aula do mapa: ponto ampliado com legenda; depois pontos de setembro e de outubro (até 26/10) de 2026. | "1 ponto = 1 foco de calor detectado" · "Setembro e outubro 2026 • UTC" | Legenda primeiro; pontos em lote por mês (T2). | "Os satélites registram pontos de calor. Cada ponto é um foco detectado, não um incêndio contado um a um." |
| 4 | 32–44 | Pacífico mais quente com seta curta para a Amazônia; selo com a fonte. | "El Niño em curso" · "NOAA, 08/10/2026" | Faixa colore em 0,8 s; seta depois; nada contínuo. | "Em dois mil e vinte e seis há El Niño. Ele pode reduzir as chuvas e favorecer o fogo." |
| 5 | 44–53 | Fundo limpo, duas linhas. | "O clima aumenta o risco." / "Não explica tudo." | Pausa 0,5 s; linha 1, depois linha 2. | "Mas o clima não explica tudo. A origem do fogo também importa." |
| 6 | 53–60 | T1 do mapa ao recorte do Xingu; selo "Parte 3". | "E no Xingu?" | Zoom-through na mesma direção. | "Agora, vamos aproximar o mapa e olhar o Xingu." |

## Vídeo 3 — Os picos
**Pergunta:** quando o fogo apareceu mais? **Frase final:** "Poucos dias concentraram muitos focos."

| # | Tempo | Tela | Texto em tela | Motion | Fala |
|---|---|---|---|---|---|
| 1 | 0–7 | Dez municípios do Xingu, tamanhos relativos preservados. | "Região de Integração Xingu — 10 municípios" | Continua o T1 do V2. | "No Xingu, o fogo não aparece igual todos os dias." |
| 2 | 7–15 | Mapa recua à esquerda (40%); gráfico diário (1/9–26/10) se desenha à direita, base zero. | "Cada barra = 1 dia" | Eixo → referência → barras da esquerda para a direita. | "Cada barra é um dia. Algumas se destacam bem mais que as outras." |
| 3 | 15–26 | Barra de 21/09 sobe em âmbar; resto a 25%; mapa mostra só os pontos desse dia. | **149** · "21 de setembro" | Pausa 0,5 s; número pousa fixo. | "Em setembro, o maior pico: dia vinte e um, cento e quarenta e nove focos." |
| 4 | 26–31 | Mapa limpa; gráfico segura. | "Outubro: 1–26" | T2 entre datas; sem fala (respiro). | — |
| 5 | 31–42 | Barra de 09/10 em âmbar; número maior que o anterior. | **336** · "9 de outubro" | Mesmo padrão da cena 3. | "Em outubro, até o dia vinte e seis, o maior foi dia nove: trezentos e trinta e seis." |
| 6 | 42–50 | Zoom em Altamira no mapa de 09/10; fração discreta. | "104 dos 336" · "Foco ≠ área queimada" | Município realçado; resto a 25%. | "Só Altamira teve cento e quatro nesse dia. Focos não medem área queimada." |
| 7 | 50–60 | Gráfico completo; quatro outras barras ganham marca fina com data e valor pequeno. Selo "3 maiores dias de cada mês". | "13/09 · 101", "26/09 · 108", "12/10 · 314", "25/10 · 297" · "E em 2025?" · "Parte 4" | Marcas em ordem cronológica, 0,4 s cada. | "Houve outros dias altos. E como isso se compara a dois mil e vinte e cinco?" |

Regras: contagem do dia separada do total mensal; pontos mudam inteiros a cada data; métrica absoluta, sem normalizar por área; outubro parcial sinalizado.

## Vídeo 4 — A comparação
**Pergunta:** o que mudou e o que fazemos com isso? **Frase final:** "Acompanhe os alertas. Evite provocar incêndios."

| # | Tempo | Tela | Texto em tela | Motion | Fala |
|---|---|---|---|---|---|
| 1 | 0–7 | Título e chip do período. | "Xingu: 2025 × 2026" · "Setembro + 1–26/10 • UTC" | Blur por palavra. | "Comparamos o mesmo período nos dois anos: setembro e vinte e seis dias de outubro." |
| 2 | 7–19 | Eixo de base zero; barra de 2025 (cinza-azulado) cresce e fica; depois a de 2026 (âmbar). | **1.113** → **3.688** | Barra de 2026 só começa após pausa de 0,5 s. | "Dois mil e vinte e cinco: mil cento e treze focos. Dois mil e vinte e seis: três mil seiscentos e oitenta e oito." |
| 3 | 19–26 | Foco entre as barras. | **+231%** | Pousa fixo, sem contagem; pausa de 0,5 s antes. | "Um aumento de duzentos e trinta e um por cento." |
| 4 | 26–37 | Barras a 25%; dois selos, um por vez. | "2025: sem El Niño" · "2026: com El Niño" · "Isso não prova a causa." | Selos entram em sequência. | "Em dois mil e vinte e cinco não havia El Niño. Agora há. Ele aumenta o risco, mas não explica sozinho." |
| 5 | 37–47 | Fundo limpo; trecho literal, legível. | "Lei 9.605/1998 — art. 41" · "Provocar incêndio em floresta ou em demais formas de vegetação" | Blur por palavra; parado ≥ 3 s. Penas só na legenda da publicação. | "A lei trata como crime provocar incêndio em floresta ou em outras formas de vegetação." |
| 6 | 47–60 | T3: a câmera recua do número e pousa na captura do aviso (nome oculto), destacando a orientação de prevenção. Assinatura Pulso e fontes. | "Acompanhe os alertas. Evite provocar incêndios." | Único recuo da série; frase final parada ≥ 2 s. | "O alerta merece atenção. Acompanhe as orientações oficiais: prevenir é proteger a floresta, a saúde e quem vive aqui." |

Nota legal: Lei nº 9.605/1998, art. 41, redação da Lei nº 14.944/2024. A localização de um foco não permite atribuir responsabilidade penal. Penas (legenda da publicação): reclusão de dois a quatro anos e multa; modalidade culposa, detenção de seis meses a um ano e multa.

---

## Orçamento de carga

| Vídeo | Cenas | Ideias | Números na tela | Máx. palavras/cena |
|---|---:|---:|---|---:|
| 1 | 6 | 1 | 0 (só data 11/10) | 16 |
| 2 | 6 | 1 | 0 | 17 |
| 3 | 7 | 1 | 2 grandes, 1 fração, 4 pequenos | 16 |
| 4 | 6 | 1 | 3, em sequência | 19 |

## Ledger de costuras

| Corte | Saída | Entrada | Carrier |
|---|---|---|---|
| V1 c2→c3 | Z + | Z + | ponto âmbar |
| V1 c5→c6 | Z + | Z + | ponto âmbar |
| V2 c5→c6 | Z + | Z + | ponto âmbar |
| V2→V3 | Z + | Z + | recorte do Xingu |
| V3 c3→c5 | T2 | T2 | barra âmbar |
| V4 c5→c6 | Z − (chegada) | Z − | número → captura do celular |

## Números conferidos (inalterados)

Snapshot `xingu-74d0fdff5980abae3d40`, dez municípios, datas `validado`.

| Janela | 2025 | 2026 | Variação |
|---|---:|---:|---:|
| Setembro completo | 527 | 1.006 | +90,89% |
| Outubro, 1–26 | 586 | 2.682 | +357,68% |
| Soma | 1.113 | 3.688 | +231,36% |

Seis dias selecionados: 13/09 = 101; 21/09 = 149; 26/09 = 108; 09/10 = 336; 12/10 = 314; 25/10 = 297 (soma 1.305, ≈35,4% de 3.688). Altamira em 09/10: 104.

## Material de apoio (fora dos vídeos)

- Histórico 2020–2026 (setembro e outubro): legenda ou carrossel da publicação. Sobre 2014–2016 e 2023–2024, ver as notas do storyboard original.
- Penas da lei e totais mensais (setembro e outubro).

## Fontes

- [Base local](../entregas/amazonia-xingu/INGESTAO.md) e [composição existente](../entregas/amazonia-xingu/COMPOSICAO.md)
- [INPE — FAQ Queimadas](https://data.inpe.br/queimadas/faq/)
- [IBGE — Amazônia Legal](https://www.ibge.gov.br/geociencias/organizacao-do-territorio/estrutura-territorial/15819-amazonia-legal.html)
- [NOAA/CPC — boletim ENSO 08/10/2026](https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso_advisory/ensodisc.shtml)
- [INMET — El Niño](https://portal.inmet.gov.br/noticias/el-ni%C3%B1o)
- [Ministério da Saúde — fumaça das queimadas, 23/10/2026](https://www.gov.br/saude/pt-br/assuntos/noticias-ms/2026/outubro/fumaca-das-queimadas-saiba-como-proteger-a-sua-saude-e-onde-buscar-atendimento)
- [Lei nº 9.605/1998](https://www.planalto.gov.br/ccivil_03/leis/l9605.htm)

## Estado

Storyboard V2 implementado e renderizado em `serie-4-videos/` usando as skills do HyperFrames (`hyperframes`, `hyperframes-cli`, `hyperframes-registry`, `media-use`):
- `SPEC.md`, `ledger.json`, `REVIEW.md` e `check.json` (0 erros e 0 avisos) gerados para os 4 episódios (`episodio-1` a `episodio-4`).
- Locuções e tempos de palavras (`WordBoundary`) atualizados em `script.json` e `speech/`, com trilhas de 60,00 s em `assets/narracao.wav` e legendas em sub-composição dedicada (`compositions/eN-captions.html`).
- Renderizações finais em MP4 (`1920 × 1080`, `30 fps`, H.264/AAC) e pranchas de verificação geradas em `serie-4-videos/renders/`.
