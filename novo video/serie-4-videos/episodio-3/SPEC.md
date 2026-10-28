# SPEC — Episódio 3: Os picos

```text
GOAL:    O morador enxerga que os focos no Xingu se concentraram em poucos dias críticos (com picos de 149 em 21/09 e 336 em 09/10, sendo 104 em Altamira) e que foco detectado não mede área queimada.
OUTPUT:  HyperFrames, 1920 x 1080, 30 fps
TIME:    60 s x 30 fps = 1800 frames; sem música (cena 4 de 26–31s é respiro silencioso)
LOOK:    ground #10282d, ink #f5f1e8, accent #ffc277 (barra e pontos do dia de pico), support #abd5bd, muted #c0d0c8;
         display face Pulso 700 (72–104 px; números-clímax 156 px tabular-nums), body face Pulso 400/700 (40–48 px);
         foco por contraste: barra do pico e município em destaque a 100% em âmbar, demais barras/municípios a 25% de opacidade
OBJECTS: 1. Mapa da Região de Integração Xingu (10 municípios do Pará, tamanhos relativos preservados);
         2. Gráfico diário de barras (01/09 a 26/10/2026, 56 dias validados, base zero, escala fixa 0–336);
         3. Pontos de calor diários em lote sem acúmulo (21/09 com 149 pontos; 09/10 com 336 pontos, sendo 104 em Altamira);
         4. Marcas finas nos outros 4 dias do top-3 de cada mês (13/09·101, 26/09·108, 12/10·314, 25/10·297)
MOTION:  títulos por palavra: blur(6px) -> blur(0px) em 0.13s, stagger 0.07s;
         c1 continua T1 do V2 (power3.out);
         c2 constrói gráfico na ordem: eixo -> linha de referência -> barras crescendo da base zero (0.7s expo.out);
         pausa de 0.5s antes dos números-clímax 149 (c3) e 336 (c5), valores fixos sem contagem intermediária;
         T2 (blur swap 8px, saída 0.2s, entrada 0.13s) entre setembro (c3), respiro de outubro (c4) e pico de outubro (c5);
         c7 revela as 4 marcas em ordem cronológica, 0.4s cada
SHOTS:
  0000–0210 (0–7s, e3-s0):   Continua T1 do V2 pousando nos 10 municípios; "Região de Integração Xingu — 10 municípios".
  0210–0450 (7–15s, e3-s1):  Mapa recua à esquerda (40%); gráfico diário (1/9–26/10, base zero) desenha eixo -> referência -> barras da esquerda para a direita; "Cada barra = 1 dia".
  0450–0780 (15–26s, e3-s2): Barra de 21/09 sobe em âmbar, resto a 25%; mapa mostra só os 149 pontos de 21/09; pausa 0.5s e pousa "149" · "21 de setembro".
  0780–0930 (26–31s, e3-s3): Respiro sem fala; mapa limpa pontos via T2; gráfico segura e destaca a janela "Outubro: 1–26".
  0930–1260 (31–42s, e3-s4): Barra de 09/10 sobe em âmbar, resto a 25%; mapa mostra os 336 pontos de 09/10; pausa 0.5s e pousa "336" · "9 de outubro".
  1260–1500 (42–50s, e3-s5): Zoom em Altamira no mapa de 09/10 (Altamira a 100% com contorno âmbar, demais 9 municípios a 25%); "104 dos 336" · "Foco ≠ área queimada".
  1500–1800 (50–60s, e3-s6): Gráfico completo; 4 barras ganham marca fina em ordem cronológica (0.4s cada): "13/09 · 101", "26/09 · 108", "12/10 · 314", "25/10 · 297"; selo "3 maiores dias de cada mês", "E em 2025?", "Parte 4" e frase final "Poucos dias concentraram muitos focos.".
BANNED:  contagem intermediária (count-up) nos números; acumular pontos entre dias; normalizar por área municipal; misturar total do dia com total mensal.
QA:      t=3s (10 municípios), t=11s (gráfico diário base zero), t=20s (21/09 = 149), t=28.5s (respiro Outubro: 1–26 sem legenda órfã), t=36s (09/10 = 336), t=46s (Altamira 104 dos 336), t=56s (4 marcas + frase final).
```

