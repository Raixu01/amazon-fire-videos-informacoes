# SPEC — Episódio 2: A época

```text
GOAL:    O morador entende por que o risco aumenta na estiagem, o que significa um foco de calor no mapa de satélite e que o El Niño em curso (NOAA 08/10/2026) aumenta o risco mas não explica tudo.
OUTPUT:  HyperFrames, 1920 x 1080, 30 fps
TIME:    60 s x 30 fps = 1800 frames; sem música
LOOK:    ground #10282d, ink #f5f1e8, accent #ffc277 (2026 / focos / El Niño), support #abd5bd (vegetação / apoio), muted #c0d0c8;
         display face Pulso 700 (72–104 px), body face Pulso 400/700 (40–48 px), captions 40 px em y=900–1008;
         foco por contraste (elemento ativo a 100%, resto a 25% de opacidade)
OBJECTS: 1. Mapa da Amazônia Legal vazio (c1) e ensinado passo a passo (c3) com lote de setembro e lote de 1–26/10/2026 em UTC;
         2. Ilustração de folha que muda de verde (#abd5bd) para seco (#ffc277) e gota de chuva que diminui (c2);
         3. Diagrama do Pacífico Equatorial mais quente com seta curta para a Amazônia e selo "NOAA, 08/10/2026" (c4);
         4. Ponto âmbar / recorte do Xingu para transição T1 no final (c6)
MOTION:  títulos por palavra: blur(6px) -> blur(0px) em 0.13s, stagger 0.07s, depois parados;
         mudança de cor da folha em 1.2s power2.inOut, seta entra depois;
         T2 (blur swap 8px, saída 0.2s, entrada 0.13s) para os lotes de pontos no mapa;
         T1 (zoom-through 0.6s power3.in/out) do mapa geral ao recorte do Xingu
SHOTS:
  0000–0210 (0–7s, e2-s0):   Mapa da Amazônia Legal vazio; título "Por que agora?" com blur por palavra.
  0210–0540 (7–18s, e2-s1):  Gota de chuva diminui e folha muda de verde (#abd5bd) para seco (#ffc277) em 1.2s power2.inOut; seta entra depois; "Menos chuva → vegetação mais seca".
  0540–0960 (18–32s, e2-s2): Aula do mapa: primeiro ponto âmbar ampliado com legenda "1 ponto = 1 foco de calor detectado"; depois entram em lote (T2) os pontos de setembro e de outubro (1–26/10/2026 • UTC).
  0960–1320 (32–44s, e2-s3): Faixa do Pacífico Equatorial colore em 0.8s, seta curta aponta para a Amazônia depois; "El Niño em curso" · "NOAA, 08/10/2026".
  1320–1590 (44–53s, e2-s4): Fundo limpo; pausa 0.5s; linha 1 "O clima aumenta o risco.", depois linha 2 "Não explica tudo.".
  1590–1800 (53–60s, e2-s5): T1 aproximando do mapa da Amazônia Legal ao recorte do Xingu; "E no Xingu?" · selo "Parte 3".
BANNED:  montagem histórica 2020–2026 (movida para material de apoio); rastro acumulado contínuo; três cartões em fileira; atribuir causalidade exclusiva ao El Niño.
QA:      t=3s (mapa vazio + "Por que agora?"), t=12s (folha seca + seta), t=21s (legenda 1 ponto = 1 foco), t=28s (lotes setembro e outubro 2026 UTC), t=38s (El Niño NOAA 08/10/2026), t=49s (duas linhas em fundo limpo), t=57s (T1 para o Xingu).
```

