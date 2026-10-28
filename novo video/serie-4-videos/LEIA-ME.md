# Fogo no Xingu — Storyboard V2 (4 × 60 s)

Série baseada no storyboard aprovado em [../STORYBOARD-V2.md](../STORYBOARD-V2.md). Cada vídeo tem 60 segundos (`1.800` quadros a `30 fps`), resolução Full HD (`1920 × 1080`), narração brasileira sintetizada offline (`Microsoft Maria Desktop`, pt-BR), sem música e com legendas embutidas em sub-composição dedicada.

## MP4 finais (`renders/`)

1. `renders/01-o-alerta.mp4` — **O alerta** (*"O aviso é sobre a fumaça."*): captura GovBR de 11/10/2026 (nome oculto), relação entre estiagem, fogo, fumaça e saúde respiratória.
2. `renders/02-a-epoca.mp4` — **A época** (*"O clima aumenta o risco. Não explica tudo."*): menos chuva → vegetação mais seca, aula de leitura do mapa (`1 ponto = 1 foco detectado`), lotes de setembro e outubro (1–26/10/2026 • UTC) e El Niño em curso (NOAA, 08/10/2026).
3. `renders/03-os-picos.mp4` — **Os picos** (*"Poucos dias concentraram muitos focos."*): Região de Integração Xingu (10 municípios do Pará), gráfico diário de base zero (`01/09` a `26/10`), picos de `21/09` (`149`), respiro sem fala (`Outubro: 1–26`), `09/10` (`336`, sendo `104` em Altamira) e os 3 maiores dias de cada mês.
4. `renders/04-a-comparacao.mp4` — **A comparação** (*"Acompanhe os alertas. Evite provocar incêndios."*): comparativo `2025 × 2026` no mesmo período (`1.113` → `3.688`, `+231%`), contexto de El Niño sem atribuir causalidade exclusiva, art. 41 da Lei nº 9.605/1998 e retorno em recuo (`T3`) para a captura do celular.

## Arquitetura HyperFrames V2

Cada pasta `episodio-N` contém:
- `SPEC.md`: especificação numérica completa conforme `references/spec.md` da skill `/hyperframes`.
- `ledger.json`: registro de costuras (`T1`, `T2`, `T3`) e do *carrier* (o ponto âmbar `#ffc277`).
- `REVIEW.md`: nota de revisão visual pós-`check` e `snapshot`.
- `index.html`: composição raiz (`data-duration="60"`, `data-fps="30"`), montando cada cena com `data-track-kind="graphics"` e uma sub-composição única de legendas (`compositions/eN-captions.html`) com `data-track-kind="captions"`.
- `check.json`: relatório `npx hyperframes check --json` com **0 erros e 0 avisos** em `lint`, `runtime`, `layout` e `contrast`.

## Reproduzir

Da raiz do repositório:

```powershell
& 'novo video/serie-4-videos/narrate-offline.ps1'
python 'novo video/serie-4-videos/build.py'
```

Para verificar, visualizar quadros e renderizar um episódio:

```powershell
cd 'novo video/serie-4-videos/episodio-1'
npx hyperframes check --json
npx hyperframes snapshot --at 1,3,10,20,30,36,46,56 --json
npx hyperframes render --fps 30 --quality delivery --workers 2 --output ../renders/01-o-alerta.mp4
```

Para auditar os 4 arquivos MP4 finais e gerar as pranchas de verificação:

```powershell
python 'novo video/serie-4-videos/verify.py'
```
