# SPEC — Episódio 4: A comparação

```text
GOAL:    O morador compara o mesmo período de 2025 e 2026 no Xingu (1.113 -> 3.688, +231%), compreende a distinção entre risco climático e causa, conhece o art. 41 da Lei 9.605/1998 e volta ao alerta no celular com orientação preventiva.
OUTPUT:  HyperFrames, 1920 x 1080, 30 fps
TIME:    60 s x 30 fps = 1800 frames; sem música
LOOK:    ground #10282d, ink #f5f1e8, accent #ffc277 (2026), compare_2025 #64828a (cinza-azulado = 2025), support #abd5bd;
         display face Pulso 700 (72–104 px; números-clímax 156 px tabular-nums), body face Pulso 400/700 (40–48 px);
         foco por contraste (elemento ativo a 100%, fundo contextual a 25% de opacidade)
OBJECTS: 1. Gráfico comparativo de base zero com barra 2025 (1.113, cinza-azulado #64828a) e barra 2026 (3.688, âmbar #ffc277);
         2. Destaque percentual "+231%" entre as barras;
         3. Dois selos climáticos ("2025: sem El Niño", "2026: com El Niño") e ressalva "Isso não prova a causa.";
         4. Quadro tipográfico limpo da Lei 9.605/1998 — art. 41;
         5. Captura do celular GovBR (11/10/2026, nome oculto) destacando prevenção e assinatura Pulso
MOTION:  títulos por palavra: blur(6px) -> blur(0px) em 0.13s, stagger 0.07s, depois parados;
         c2: barra de 2025 cresce da base zero (0.7s expo.out); pausa de 0.5s; barra de 2026 cresce (0.8s expo.out);
         c3: pausa de 0.5s antes de "+231%" pousar fixo (sem count-up);
         c4: barras recuam a 25% de opacidade; selos entram em sequência sincronizados à fala;
         c5: blur por palavra e texto da lei parado por >= 3s;
         c6: T3 (recuo de chegada: scale 1 -> 0.6 com blur máx. 6px no meio da transição) pousando na captura do celular; frase final parada por >= 2s
SHOTS:
  0000–0210 (0–7s, e4-s0):   Título "Xingu: 2025 × 2026" e chip "Setembro + 1–26/10 • UTC".
  0210–0570 (7–19s, e4-s1):  Eixo base zero; barra 2025 (cinza-azulado, 1.113) cresce e fica; após pausa de 0.5s (t=13.0s), barra 2026 (âmbar, 3.688) cresce.
  0570–0780 (19–26s, e4-s2): Foco entre as barras; pausa de 0.5s e pousa fixo "+231%".
  0780–1110 (26–37s, e4-s3): Barras a 25%; entram em sequência "2025: sem El Niño", "2026: com El Niño" e "Isso não prova a causa.".
  1110–1410 (37–47s, e4-s4): Fundo limpo; "Lei 9.605/1998 — art. 41" e "Provocar incêndio em floresta ou em demais formas de vegetação", parado >= 3s.
  1410–1800 (47–60s, e4-s5): T3 recua do quadro anterior para a captura do aviso GovBR destacando prevenção; frase final "Acompanhe os alertas. Evite provocar incêndios." parada >= 2s; assinatura Pulso.
BANNED:  três gráficos mensais concorrendo na tela; contagem animada nos números; penas da lei na tela/narração (ficam na legenda da publicação); atribuir autoria penal por ponto no mapa.
QA:      t=3s (título + chip), t=10s (apenas barra 2025 = 1.113), t=16s (barra 2026 = 3.688), t=22s (+231% fixo), t=32s (barras a 25% + selos El Niño), t=42s (Lei 9.605/1998 art. 41 parada), t=55s (chegada T3 na captura + frase final parada).
```

