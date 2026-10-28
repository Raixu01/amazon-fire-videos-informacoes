# SPEC — Episódio 1: O alerta

```text
GOAL:    O morador do Xingu reconhece o aviso recebido no celular em 11/10/2026 e entende que o alerta imediato é sobre os riscos da fumaça à saúde respiratória.
OUTPUT:  HyperFrames, 1920 x 1080, 30 fps
TIME:    60 s x 30 fps = 1800 frames; sem música (voz brasileira como relógio)
LOOK:    ground #10282d (azul-petróleo plano, 0% gradiente), ink #f5f1e8 (marfim),
         accent #ffc277 (âmbar = foco/2026), support #abd5bd (verde-claro), muted #c0d0c8;
         display face Pulso (Segoe UI 700, 72–104 px, tracking -2px a -3px),
         body face Pulso (Segoe UI 400/700, 40–48 px), captions 40 px em y=900–1008;
         medium: infografia editorial limpa com foco por contraste (destaque a 100% + halo âmbar 2px, resto a 25% de opacidade)
OBJECTS: 1. Captura do celular GovBR (11/10/2026, nome da destinatária oculto) com trechos de alerta de incêndios e fumaça;
         2. Ponto âmbar (#ffc277, r=14px) que atua como carrier entre escalas;
         3. Mapa da Amazônia Legal (773 municípios) com destaque para a Região de Integração Xingu (10 municípios);
         4. Três ícones ilustrativos na mesma posição central (folha seca, fogo, fumaça sobre casa) com rótulo "Ilustração"
MOTION:  títulos por palavra: blur(6px) -> blur(0px) e opacity 0 -> 1 em 0.13s (4 frames), stagger 0.07s (2 frames), depois 100% parados;
         T1 (zoom-through pelo ponto âmbar): 0.6s (18 frames), saída power3.in, entrada power3.out;
         pausa de 0.5s antes da frase-síntese; revelação progressiva sincronizada à voz
SHOTS:
  0000–0180 (0–6s, e1-s0):   Frame 0 já exibe a captura GovBR de 11/10/2026; push 1.0 -> 1.18 no trecho do alerta ("Sua região está sob alerta de incêndios"), resto a 25%; título "Você também recebeu?".
  0180–0480 (6–16s, e1-s1):  Pan vertical curto na captura para "A fumaça pode causar problemas respiratórios" com destaque âmbar estático; resto a 25%.
  0480–0840 (16–28s, e1-s2): Ícone do alerta solta o ponto âmbar -> T1 revela a Amazônia Legal com contorno desenhando em 0.8s e marca "Xingu".
  0840–1260 (28–42s, e1-s3): Na mesma posição central, entram um por vez conforme a voz nomeia: folha seca -> fogo -> fumaça sobre casa (o anterior recua a 25%); rótulo "Ilustração" e "Seca · fogo · fumaça".
  1260–1560 (42–52s, e1-s4): Fundo limpo; pausa 0.5s; blur por palavra em "Acompanhe os avisos oficiais" e fechamento "O aviso é sobre a fumaça." parado.
  1560–1800 (52–60s, e1-s5): Ponto âmbar cresce sobre o mapa; título "E os satélites, o que mostram?"; selo "Parte 2"; saída em movimento T1.
BANNED:  três cartões em fileira; listas numeradas 01/02/03; entrada genérica fade+slide-up (y:18) em todas as cenas; pulso, sirene, chama animada, partículas, bounce; atribuir o envio do aviso de 11/10 aos números posteriores do estudo.
QA:      frame 0 (captura visível, não vazia), t=3s (push 118% no alerta), t=11s (foco na frase sobre fumaça), t=22s (Amazônia Legal + Xingu), t=31s/34s/37s (revelação progressiva dos 3 ícones na mesma posição), t=47s ("Acompanhe os avisos oficiais"), t=57s (T1 pelo ponto âmbar).
```

