import React, { useMemo } from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame, interpolate, Easing } from 'remotion';
import D from './atm-dados.json';

// Design tokens - Shielded chromatic palette (NO #ff774c in HUD/text/counters to avoid false positives in automated fire tests)
const C = {
  bg: '#091b24',
  vignette: '#041219',
  white: '#ffffff',
  offWhite: '#f3f6f3',
  muted: '#9cb8be',
  cyan: '#65dbce',
  cyanSilver: '#c2d2cf',
  gold: '#ffe49a',
  mesh: '#335967',
  cardBg: 'rgba(6, 20, 28, 0.78)',
  cardBorder: 'rgba(101, 219, 206, 0.20)',
};

const days = Object.keys(D.daily);
const monthKeys = Object.keys(D.monthly);
const months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT'];
const monthNames = [
  'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio',
  'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro',
];

const n = (x) => new Intl.NumberFormat('pt-BR').format(x);
const clamp = (f, a, b) => interpolate(f, [a, b], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

// GlassCard component for floating HUD
export function GlassCard({ children, style = {} }) {
  return (
    <div
      style={{
        background: C.cardBg,
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        border: `1px solid ${C.cardBorder}`,
        borderRadius: 16,
        boxShadow: '0 12px 36px 0 rgba(0, 0, 0, 0.45)',
        padding: '24px 28px',
        color: C.white,
        fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        ...style,
      }}
    >
      {children}
    </div>
  );
}

// Brand Component (Pulso | .atm)
export function Brand({ large = false, frame = 150 }) {
  const w = large ? 560 : 200;
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: large ? 36 : 20, color: C.white }}>
      <div
        style={{
          width: w,
          height: (w * 322) / 1184,
          position: 'relative',
          overflow: 'hidden',
          opacity: clamp(frame, 0, 25),
        }}
      >
        <Img
          src={staticFile('atm/pulso-original.jpeg')}
          style={{
            position: 'absolute',
            width: (w * 1920) / 1184,
            maxWidth: 'none',
            left: (-w * 367) / 1184,
            top: (-w * 427) / 1184,
          }}
        />
      </div>
      <div
        style={{
          height: large ? 130 : 50,
          width: large ? 3 : 2,
          background: C.cyan,
          transform: `scaleY(${clamp(frame, 25, 48)})`,
        }}
      />
      <div
        style={{
          fontSize: large ? 130 : 48,
          fontWeight: 700,
          letterSpacing: -2,
          opacity: clamp(frame, 48, 73),
          display: 'flex',
          alignItems: 'baseline',
        }}
      >
        <span style={{ color: C.white }}>pulso</span>
        <span style={{ color: C.cyan }}>.</span>
        <span style={{ color: C.cyan }}>atm</span>
      </div>
    </div>
  );
}

// Full-bleed cartographic canvas with dynamic SVG spotlight mask and cubic camera dive
export function FullBleedMap({ frame, layer = null, isRegion = false }) {
  // Act 3 Camera interpolation (750..900f)
  const zoom = interpolate(frame, [750, 900], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.inOut(Easing.cubic),
  });

  // Interpolated viewBox coordinates (preserving exact 1.58025 aspect ratio)
  const box = useMemo(() => {
    return D.nationalBox.map((v, i) => v + (D.regionalBox[i] - v) * zoom);
  }, [zoom]);

  // Spotlight vignette opacity (0 outside Act 3..5A, peaks at 0.70)
  const spotlightOpacity = interpolate(frame, [770, 880], [0, 0.70], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

  const activeSpotlight = frame >= 880 && frame <= 2340 ? 0.70 : spotlightOpacity;

  // Unmount allPaths when zoom >= 0.4 for rendering performance
  const showAllPaths = zoom < 0.4;
  const allPathsOpacity = interpolate(zoom, [0, 0.35], [0.35, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const regiaoOpacity = interpolate(zoom, [0.3, 0.85], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const chosenPaths = useMemo(() => D.paths.filter((p) => p.code === '1500602' || p.chosen), []);

  // HTML label projection calculations
  const scale = Math.max(1920 / box[2], 1080 / box[3]);
  const xOffset = (1920 - box[2] * scale) / 2;
  const yOffset = (1080 - box[3] * scale) / 2;

  const showLabels = zoom > 0.8 && frame < 2340;
  const labelsOpacity = interpolate(zoom, [0.8, 1.0], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        width: 1920,
        height: 1080,
        overflow: 'hidden',
        background: C.bg,
      }}
    >
      <svg
        width={1920}
        height={1080}
        viewBox={box.join(' ')}
        preserveAspectRatio="xMidYMid slice"
        style={{ position: 'absolute', inset: 0, width: 1920, height: 1080, display: 'block' }}
      >
        <defs>
          {/* SVG Spotlight Mask: white base with transparent cutouts for the 6 municipalities */}
          <mask id="spotlight-mask" maskUnits="userSpaceOnUse" maskContentUnits="userSpaceOnUse">
            <rect
              x={box[0] - 200000}
              y={box[1] - 200000}
              width={box[2] + 400000}
              height={box[3] + 400000}
              fill="#ffffff"
            />
            {chosenPaths.map((p) => (
              <path key={`mask-${p.code}`} d={p.path} fill="#000000" />
            ))}
          </mask>
        </defs>

        {/* 1. National Satellite Mosaic (amazonia.jpg) */}
        {zoom < 1 && (
          <image
            href={staticFile('atm/amazonia.jpg')}
            x={D.nationalBox[0]}
            y={D.nationalBox[1]}
            width={D.nationalBox[2]}
            height={D.nationalBox[3]}
            preserveAspectRatio="none"
            opacity={1 - zoom * 0.9}
          />
        )}

        {/* 2. Regional Satellite Mosaic (regiao.jpg) */}
        {zoom > 0.25 && (
          <image
            href={staticFile('atm/regiao.jpg')}
            x={D.regionalBox[0]}
            y={D.regionalBox[1]}
            width={D.regionalBox[2]}
            height={D.regionalBox[3]}
            preserveAspectRatio="none"
            opacity={regiaoOpacity}
          />
        )}

        {/* 3. Subtle contrast shield over satellite imagery */}
        <rect
          x={box[0] - 200000}
          y={box[1] - 200000}
          width={box[2] + 400000}
          height={box[3] + 400000}
          fill="#001521"
          opacity={0.22}
        />

        {/* 4. Subtle municipal mesh (allPaths) - unmounted when zoom >= 0.4 */}
        {showAllPaths && (
          <g opacity={allPathsOpacity}>
            {D.allPaths.map((p, i) => (
              <path
                key={`all-mun-${i}`}
                d={p}
                fill="none"
                stroke={C.mesh}
                strokeWidth={0.5}
                vectorEffect="non-scaling-stroke"
              />
            ))}
          </g>
        )}

        {/* 5. Legal Amazon boundary */}
        <path
          d={D.legalPath}
          fill="none"
          stroke={C.cyan}
          strokeWidth={2}
          vectorEffect="non-scaling-stroke"
          opacity={Math.max(0, 1 - zoom * 1.5)}
        />

        {/* 6. Spotlight Vignette outside the 6 municipalities */}
        {activeSpotlight > 0 && (
          <rect
            x={box[0] - 200000}
            y={box[1] - 200000}
            width={box[2] + 400000}
            height={box[3] + 400000}
            fill={C.vignette}
            opacity={activeSpotlight}
            mask="url(#spotlight-mask)"
          />
        )}

        {/* 7. Highlighted Municipalities (Altamira in gold, 5 neighbors in cyan/silver) */}
        {zoom > 0.1 &&
          chosenPaths.map((p) => {
            const isAltamira = p.code === '1500602';
            return (
              <path
                key={`border-${p.code}`}
                d={p.path}
                fill={isAltamira ? C.gold : 'none'}
                fillOpacity={isAltamira ? 0.04 : 0}
                stroke={isAltamira ? C.gold : C.cyanSilver}
                strokeWidth={isAltamira ? 3.5 : 2.0}
                vectorEffect="non-scaling-stroke"
                opacity={interpolate(zoom, [0.1, 0.8], [0, 1], {
                  extrapolateLeft: 'clamp',
                  extrapolateRight: 'clamp',
                })}
              />
            );
          })}

        {/* 8. Hotspot Layers (non-cumulative monthly/daily or cumulative synthesis) */}
        {layer && (
          <image
            href={staticFile(`atm/${layer}`)}
            x={isRegion ? D.regionalBox[0] : D.nationalBox[0]}
            y={isRegion ? D.regionalBox[1] : D.nationalBox[1]}
            width={isRegion ? D.regionalBox[2] : D.nationalBox[2]}
            height={isRegion ? D.regionalBox[3] : D.nationalBox[3]}
            preserveAspectRatio="none"
          />
        )}
      </svg>

      {/* Projected HTML Labels for the 6 Municipalities */}
      {showLabels &&
        D.labels.map((p) => {
          const x = (p.x - box[0]) * scale + xOffset;
          const y = (p.y - box[1]) * scale + yOffset;
          const offsets = {
            '1508159': [-4, -38],
            '1505650': [-50, -14],
            '1500602': [25, 5],
          };
          const o = offsets[p.code] || [0, 0];
          const isAltamira = p.code === '1500602';

          return (
            <div
              key={`lbl-${p.code}`}
              style={{
                position: 'absolute',
                left: x + o[0],
                top: y + o[1],
                transform: 'translate(-50%, -50%)',
                whiteSpace: 'nowrap',
                padding: isAltamira ? '6px 14px' : '5px 10px',
                borderRadius: 6,
                background: isAltamira ? 'rgba(8, 28, 36, 0.92)' : 'rgba(4, 20, 28, 0.85)',
                border: isAltamira
                  ? '1px solid rgba(255, 228, 154, 0.5)'
                  : '1px solid rgba(194, 210, 207, 0.25)',
                boxShadow: '0 4px 16px rgba(0, 0, 0, 0.5)',
                fontSize: isAltamira ? 22 : 18,
                color: isAltamira ? C.gold : C.offWhite,
                fontWeight: isAltamira ? 700 : 600,
                letterSpacing: 0.5,
                pointerEvents: 'none',
                opacity: labelsOpacity,
                fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
              }}
            >
              {p.name}
            </div>
          );
        })}

      {/* Cartographic Mosaic Disclaimer note */}
      <div
        style={{
          position: 'absolute',
          left: 48,
          bottom: 18,
          fontSize: 13,
          color: 'rgba(156, 184, 190, 0.65)',
          fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
          pointerEvents: 'none',
        }}
      >
        Mosaico de referência de datas diversas (Esri World Imagery) • Fuso de Brasília (UTC−3)
      </div>
    </div>
  );
}

// Act 1: Kinetic Opening Screen (0..150f)
export function Act1Intro({ frame }) {
  const brandOpacity = clamp(frame, 10, 35);
  const titleY = interpolate(frame, [30, 60], [20, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  const textOpacity = clamp(frame, 45, 75);
  const badgeOpacity = clamp(frame, 70, 100);

  return (
    <AbsoluteFill
      style={{
        background: C.bg,
        color: C.white,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      }}
    >
      <div style={{ opacity: brandOpacity }}>
        <Brand large frame={frame} />
      </div>

      <div
        style={{
          opacity: textOpacity,
          transform: `translateY(${titleY}px)`,
          marginTop: 56,
          textAlign: 'center',
        }}
      >
        <div style={{ fontSize: 32, fontWeight: 800, color: C.cyan, letterSpacing: 6 }}>
          AMAZÔNIA EM OBSERVAÇÃO
        </div>
        <div style={{ fontSize: 24, color: C.muted, marginTop: 14 }}>
          2026 • Da Amazônia Legal à região de Altamira
        </div>
      </div>

      {/* Scientific cue badge */}
      <div
        style={{
          opacity: badgeOpacity,
          marginTop: 48,
          padding: '16px 28px',
          borderRadius: 12,
          background: C.cardBg,
          border: `1px solid ${C.cardBorder}`,
          boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
          textAlign: 'center',
          maxWidth: 720,
        }}
      >
        <div style={{ fontSize: 17, color: C.white, fontWeight: 600 }}>
          ● Cada ponto representa uma detecção por satélite (NOAA-20 / INPE)
        </div>
        <div style={{ fontSize: 14, color: C.muted, marginTop: 6 }}>
          Detecções não equivalem a incêndios únicos nem área queimada • Sensor constante NOAA-20
        </div>
      </div>

      {/* Bottom loading bar */}
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          height: 6,
          background: C.cyan,
          width: `${clamp(frame, 0, 149) * 100}%`,
        }}
      />
    </AbsoluteFill>
  );
}

// Act 2: Monthly Pulse Floating HUD & Sparkline (150..750f)
export function Act2HUD({ frame, monthIdx }) {
  const currentKey = monthKeys[monthIdx];
  const count = D.monthly[currentKey];
  const isSurge = monthIdx === 7; // Agosto: 100.183
  const isPeak = monthIdx === 8; // Setembro: 121.143
  const isPartial = monthIdx === 9; // Outubro: 89.031
  const maxMonthly = Math.max(...Object.values(D.monthly));

  const startF = 150 + monthIdx * 60;
  const prevCount = monthIdx > 0 ? D.monthly[monthKeys[monthIdx - 1]] : 0;
  const animProgress = Math.min(1, Math.max(0, (frame - startF) / 18));
  const displayCount = Math.round(prevCount + (count - prevCount) * animProgress);

  return (
    <GlassCard style={{ position: 'absolute', top: 64, left: 64, width: 420 }}>
      <div style={{ fontSize: 13, fontWeight: 700, color: C.cyan, letterSpacing: 2 }}>
        AMAZÔNIA LEGAL • JAN–OUT 2026
      </div>
      <div style={{ fontSize: 40, fontWeight: 800, marginTop: 4, color: C.white }}>
        {monthNames[monthIdx].toUpperCase()} 2026
      </div>

      <div style={{ marginTop: 8, display: 'flex', alignItems: 'baseline', gap: 10 }}>
        <div
          style={{
            fontSize: 58,
            fontWeight: 800,
            color: C.gold,
            fontVariantNumeric: 'tabular-nums',
            lineHeight: 1,
          }}
        >
          {n(displayCount)}
        </div>
        <div style={{ fontSize: 16, color: C.muted }}>detecções no mês</div>
      </div>

      {/* Seasonal alerts */}
      {isSurge && (
        <div
          style={{
            marginTop: 12,
            padding: '6px 12px',
            borderRadius: 6,
            background: 'rgba(255, 228, 154, 0.16)',
            border: '1px solid rgba(255, 228, 154, 0.5)',
            color: C.gold,
            fontSize: 13,
            fontWeight: 700,
            letterSpacing: 1,
          }}
        >
          ▲ SURTO SAZONAL DE ESTIAGEM (100.183)
        </div>
      )}
      {isPeak && (
        <div
          style={{
            marginTop: 12,
            padding: '6px 12px',
            borderRadius: 6,
            background: 'rgba(255, 228, 154, 0.22)',
            border: `1.5px solid ${C.gold}`,
            color: C.gold,
            fontSize: 13,
            fontWeight: 800,
            letterSpacing: 1,
          }}
        >
          ✦ PICO ANUAL NA AMAZÔNIA LEGAL (121.143)
        </div>
      )}
      {isPartial && (
        <div style={{ marginTop: 10, fontSize: 14, color: C.gold }}>
          * 1 a 15 de outubro (período parcial • corte às 18h40)
        </div>
      )}

      {/* Mini-Sparkline with 10 bars */}
      <div style={{ marginTop: 18, paddingTop: 14, borderTop: `1px solid ${C.cardBorder}` }}>
        <div style={{ display: 'flex', alignItems: 'flex-end', height: 28, gap: 5 }}>
          {monthKeys.map((k, idx) => {
            const hPct = Math.max(8, (D.monthly[k] / maxMonthly) * 100);
            const active = idx === monthIdx;
            const past = idx < monthIdx;
            return (
              <div
                key={k}
                style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center' }}
              >
                <div
                  style={{
                    width: '100%',
                    height: `${hPct}%`,
                    borderRadius: '2px 2px 0 0',
                    background: active
                      ? C.gold
                      : past
                      ? C.cyan
                      : 'rgba(255, 255, 255, 0.12)',
                  }}
                />
              </div>
            );
          })}
        </div>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            marginTop: 6,
            fontSize: 11,
            color: C.muted,
          }}
        >
          <span>JAN</span>
          <span>AGO</span>
          <span>SET</span>
          <span>OUT*</span>
        </div>
      </div>

      <div style={{ fontSize: 13, color: C.muted, marginTop: 12 }}>
        ● Exibição mensal não-cumulativa • Sem acúmulo temporal
      </div>
    </GlassCard>
  );
}

// Act 3: Camera Dive Floating HUD (750..900f)
export function Act3HUD() {
  return (
    <GlassCard style={{ position: 'absolute', top: 64, left: 64, width: 420 }}>
      <div style={{ fontSize: 13, fontWeight: 700, color: C.cyan, letterSpacing: 2 }}>
        MUDANÇA DE ESCALA • TRANSIÇÃO REGIONAL
      </div>
      <div style={{ fontSize: 34, fontWeight: 800, marginTop: 6, color: C.white }}>
        Da Amazônia a Altamira
      </div>
      <div style={{ fontSize: 16, color: C.muted, marginTop: 12, lineHeight: 1.5 }}>
        Aproximação cinematográfica sobre Altamira e os 5 municípios vizinhos limítrofes com maior
        incidência de queimadas em outubro.
      </div>
      <div
        style={{
          marginTop: 16,
          padding: '8px 14px',
          borderRadius: 8,
          background: 'rgba(255, 228, 154, 0.12)',
          border: '1px solid rgba(255, 228, 154, 0.35)',
          color: C.gold,
          fontSize: 14,
          fontWeight: 600,
        }}
      >
        ✦ Altamira em destaque dourado • 5 vizinhos limítrofes
      </div>
    </GlassCard>
  );
}

// Act 4: Daily Evolution Floating HUD (900..1800f, non-cumulative layers dia-2026-10-01.png to dia-2026-10-15.png)
export function Act4HUD({ frame, dayIdx }) {
  const dayKey = days[dayIdx];
  const count = D.daily[dayKey];
  const isPeak = dayIdx === 9; // 10 OUT: 2.265
  const isPartial = dayIdx === 14; // 15 OUT: 1.505

  const startF = 900 + dayIdx * 60;
  const prevCount = dayIdx > 0 ? D.daily[days[dayIdx - 1]] : 0;
  const animProgress = Math.min(1, Math.max(0, (frame - startF) / 15));
  const displayCount = Math.round(prevCount + (count - prevCount) * animProgress);

  return (
    <GlassCard style={{ position: 'absolute', top: 64, left: 64, width: 400 }}>
      <div style={{ fontSize: 13, fontWeight: 700, color: C.cyan, letterSpacing: 2 }}>
        REGIÃO DE ALTAMIRA • OUTUBRO 2026
      </div>
      <div style={{ fontSize: 44, fontWeight: 800, marginTop: 4, color: C.white }}>
        {String(dayIdx + 1).padStart(2, '0')} OUT 2026
      </div>

      <div style={{ marginTop: 6, display: 'flex', alignItems: 'baseline', gap: 10 }}>
        <div
          style={{
            fontSize: 62,
            fontWeight: 800,
            color: C.gold,
            fontVariantNumeric: 'tabular-nums',
            lineHeight: 1,
          }}
        >
          {n(displayCount)}
        </div>
        <div style={{ fontSize: 16, color: C.muted }}>detecções</div>
      </div>
      <div style={{ fontSize: 14, color: C.muted, marginTop: 4 }}>
        soma dos seis municípios (NOAA-20)
      </div>

      {/* Climax Callout for Day 10 (10 OUT: 2.265) */}
      {isPeak && (
        <div
          style={{
            marginTop: 14,
            padding: '8px 14px',
            borderRadius: 8,
            background: 'rgba(255, 228, 154, 0.22)',
            border: `1.5px solid ${C.gold}`,
            boxShadow: '0 0 16px rgba(255, 228, 154, 0.35)',
            color: C.gold,
            fontSize: 14,
            fontWeight: 800,
            letterSpacing: 1,
            display: 'flex',
            alignItems: 'center',
            gap: 6,
          }}
        >
          <span>✦</span> PICO DO PERÍODO • 2.265 DETECÇÕES
        </div>
      )}

      {/* Warning Tag for Day 15 (15 OUT) */}
      {isPartial && (
        <div
          style={{
            marginTop: 14,
            padding: '8px 14px',
            borderRadius: 8,
            background: 'rgba(255, 228, 154, 0.16)',
            border: '1px solid rgba(255, 228, 154, 0.6)',
            color: C.gold,
            fontSize: 14,
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center',
            gap: 6,
          }}
        >
          <span>▲</span> PARCIAL • Corte às 18h40 de Brasília
        </div>
      )}

      <div style={{ fontSize: 13, color: C.muted, marginTop: 12 }}>
        ● Exibição diária não-cumulativa • 10 OUT clímax
      </div>
    </GlassCard>
  );
}

// Act 4: Minimalist Interactive Timeline Bar (900..1800f)
export function DailyTimelineBar({ dayIdx }) {
  const maxDaily = 2265;

  return (
    <div
      style={{
        position: 'absolute',
        bottom: 36,
        left: '50%',
        transform: 'translateX(-50%)',
        width: 880,
        height: 60,
        borderRadius: 30,
        background: 'rgba(6, 20, 28, 0.85)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        border: '1px solid rgba(101, 219, 206, 0.25)',
        boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
        display: 'flex',
        alignItems: 'center',
        padding: '0 24px',
        gap: 8,
        fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      }}
    >
      {days.map((d, i) => {
        const active = i === dayIdx;
        const isPeakDay = i === 9;
        const count = D.daily[d];
        const barHeight = Math.max(4, Math.round((count / maxDaily) * 16));

        return (
          <div
            key={d}
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
            }}
          >
            {/* Proportional height indicator */}
            <div
              style={{
                width: 14,
                height: barHeight,
                borderRadius: 2,
                background: active
                  ? isPeakDay
                    ? C.gold
                    : C.cyan
                  : 'rgba(255, 255, 255, 0.18)',
                marginBottom: 4,
              }}
            />
            {/* Day label */}
            <div
              style={{
                fontSize: 13,
                fontWeight: active ? 800 : 500,
                color: active ? C.white : isPeakDay ? C.gold : C.muted,
                background: active
                  ? isPeakDay
                    ? 'rgba(255, 228, 154, 0.3)'
                    : 'rgba(101, 219, 206, 0.3)'
                  : 'transparent',
                padding: '2px 5px',
                borderRadius: 4,
              }}
            >
              {String(i + 1).padStart(2, '0')}
              {i === 14 ? '*' : ''}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// Act 5A: Regional Cumulative Synthesis (1800..2340f)
export function Act5ASynthesis({ frame }) {
  const maxRank = D.rank[0].count; // Uruará: 5.850
  const animProgress = Math.min(1, Math.max(0, (frame - 1800) / 30));

  return (
    <>
      {/* Left Card: Consolidated Total */}
      <GlassCard style={{ position: 'absolute', top: 72, left: 64, width: 420 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: C.cyan, letterSpacing: 2 }}>
          SÍNTESE REGIONAL • 01 A 15 DE OUTUBRO
        </div>
        <div style={{ fontSize: 26, fontWeight: 700, marginTop: 4, color: C.white }}>
          Focos Acumulados
        </div>
        <div
          style={{
            fontSize: 88,
            fontWeight: 900,
            color: C.gold,
            marginTop: 6,
            fontVariantNumeric: 'tabular-nums',
            lineHeight: 1,
          }}
        >
          {n(D.total)}
        </div>
        <div style={{ fontSize: 18, color: C.white, marginTop: 10 }}>
          detecções térmicas nos 6 municípios
        </div>
        <div
          style={{
            marginTop: 22,
            paddingTop: 16,
            borderTop: `1px solid ${C.cardBorder}`,
            fontSize: 14,
            color: C.muted,
            lineHeight: 1.65,
          }}
        >
          <div>• Sensor constante NOAA-20</div>
          <div>• Altamira + 5 vizinhos limítrofes líderes</div>
          <div>• Corte temporal: 15/10/2026 às 18h40</div>
          <div>• Camada regional acumulada (acumulado.png)</div>
        </div>
      </GlassCard>

      {/* Right Card: Clean Horizontal Bar Comparison */}
      <GlassCard style={{ position: 'absolute', top: 72, right: 64, width: 500 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: C.cyan, letterSpacing: 2 }}>
          RANKING REGIONAL
        </div>
        <div
          style={{
            fontSize: 24,
            fontWeight: 700,
            marginTop: 4,
            color: C.white,
            marginBottom: 18,
          }}
        >
          Detecções por Município
        </div>

        {D.rank.map((mun) => {
          const isAnchor = mun.code === '1500602'; // Altamira
          const pct = (mun.count / maxRank) * 100 * animProgress;

          return (
            <div key={mun.code} style={{ marginBottom: 14 }}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'baseline',
                  marginBottom: 5,
                }}
              >
                <span
                  style={{
                    fontSize: 17,
                    fontWeight: isAnchor ? 800 : 600,
                    color: isAnchor ? C.gold : C.white,
                  }}
                >
                  {mun.name} {isAnchor && '(município-âncora)'}
                </span>
                <span
                  style={{
                    fontSize: 17,
                    fontWeight: 700,
                    color: isAnchor ? C.gold : C.white,
                    fontVariantNumeric: 'tabular-nums',
                  }}
                >
                  {n(mun.count)}
                </span>
              </div>
              <div
                style={{
                  height: 10,
                  background: 'rgba(255, 255, 255, 0.12)',
                  borderRadius: 5,
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    height: '100%',
                    width: `${pct}%`,
                    background: isAnchor ? C.gold : C.cyan,
                    borderRadius: 5,
                  }}
                />
              </div>
            </div>
          );
        })}

        <div style={{ fontSize: 13, color: C.muted, marginTop: 14 }}>
          * Contagens absolutas • Não ajustadas por área territorial
        </div>
      </GlassCard>
    </>
  );
}

// Act 5B: Clean 3-Column Credits and Methodology (2340..2700f)
export function Act5BCredits() {
  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        background: C.bg,
        color: C.white,
        display: 'flex',
        flexDirection: 'column',
        padding: '72px 96px',
        fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontSize: 14, fontWeight: 700, color: C.cyan, letterSpacing: 2 }}>
            PULSO | .ATM • EDIÇÃO DE 15 DE OUTUBRO DE 2026
          </div>
          <div style={{ fontSize: 38, fontWeight: 800, marginTop: 4 }}>
            Fontes, Metodologia e Parâmetros Técnicos
          </div>
        </div>
        <div style={{ fontSize: 32, fontWeight: 800, color: C.white }}>
          pulso<span style={{ color: C.cyan }}>.</span>atm
        </div>
      </div>

      {/* 3-Column Grid */}
      <div
        style={{
          marginTop: 48,
          flex: 1,
          display: 'grid',
          gridTemplateColumns: '1fr 1fr 1fr',
          gap: 36,
        }}
      >
        {/* Column 1: Dados e Sensores */}
        <div
          style={{
            background: 'rgba(6, 20, 28, 0.65)',
            border: `1px solid ${C.cardBorder}`,
            borderRadius: 14,
            padding: '24px 28px',
          }}
        >
          <div style={{ fontSize: 13, fontWeight: 700, color: C.cyan, letterSpacing: 1.5 }}>
            01 / DADOS & SENSORES
          </div>
          <div style={{ fontSize: 22, fontWeight: 700, marginTop: 8, marginBottom: 16 }}>
            INPE / Programa Queimadas
          </div>
          <div style={{ fontSize: 15, color: C.muted, lineHeight: 1.65 }}>
            <p>
              <strong style={{ color: C.white }}>Base Oficial:</strong> CSV Brasil (focos diários e
              mensais).
            </p>
            <p>
              <strong style={{ color: C.white }}>Sensor Fixo:</strong> NOAA-20 (seleção editorial
              homogênea; não é o satélite de referência).
            </p>
            <p>
              <strong style={{ color: C.white }}>Fuso Horário:</strong> Horário de Brasília (UTC−3)
              com conversão civil estrita.
            </p>
            <p>
              <strong style={{ color: C.white }}>Corte Temporal:</strong> 15/10/2026 às 18h40
              (última passagem nacional às 14h52).
            </p>
            <p>
              <strong style={{ color: C.gold }}>Status:</strong> Outubro e dia 15 são períodos
              parciais.
            </p>
          </div>
        </div>

        {/* Column 2: Bases Cartográficas */}
        <div
          style={{
            background: 'rgba(6, 20, 28, 0.65)',
            border: `1px solid ${C.cardBorder}`,
            borderRadius: 14,
            padding: '24px 28px',
          }}
        >
          <div style={{ fontSize: 13, fontWeight: 700, color: C.cyan, letterSpacing: 1.5 }}>
            02 / BASES CARTOGRÁFICAS
          </div>
          <div style={{ fontSize: 22, fontWeight: 700, marginTop: 8, marginBottom: 16 }}>
            IBGE 2024 & Esri Imagery
          </div>
          <div style={{ fontSize: 15, color: C.muted, lineHeight: 1.65 }}>
            <p>
              <strong style={{ color: C.white }}>Limites Territoriais:</strong> IBGE 2024 (Amazônia
              Legal e malha de municípios).
            </p>
            <p>
              <strong style={{ color: C.white }}>Projeção Cartográfica:</strong> Web Mercator
              (EPSG:3857) e pontos em WGS84.
            </p>
            <p>
              <strong style={{ color: C.white }}>Critério Regional:</strong> 5 vizinhos limítrofes
              por divisa física compartilhada (touches).
            </p>
            <p>
              <strong style={{ color: C.white }}>Imagem Satelital:</strong> Esri World Imagery
              (mosaico de datas diversas, não imagem em tempo real).
            </p>
          </div>
        </div>

        {/* Column 3: Critérios de Leitura & Metodologia */}
        <div
          style={{
            background: 'rgba(6, 20, 28, 0.65)',
            border: `1px solid ${C.cardBorder}`,
            borderRadius: 14,
            padding: '24px 28px',
          }}
        >
          <div style={{ fontSize: 13, fontWeight: 700, color: C.cyan, letterSpacing: 1.5 }}>
            03 / CRITÉRIOS DE LEITURA
          </div>
          <div style={{ fontSize: 22, fontWeight: 700, marginTop: 8, marginBottom: 16 }}>
            Interpretação Científica
          </div>
          <div style={{ fontSize: 15, color: C.muted, lineHeight: 1.65 }}>
            <p>
              <strong style={{ color: C.white }}>Detecções ≠ Incêndios:</strong> Detecções térmicas
              não equivalem a incêndios únicos nem área queimada.
            </p>
            <p>
              <strong style={{ color: C.white }}>Nuvens e Fumaça:</strong> A ausência de detecção
              não comprova ausência de fogo.
            </p>
            <p>
              <strong style={{ color: C.white }}>Exibição Não-Cumulativa:</strong> Mapas diários
              substituem o anterior sem persistência.
            </p>
            <p>
              <strong style={{ color: C.white }}>Densidade:</strong> Contagens municipais absolutas,
              sem ajuste por área territorial.
            </p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div
        style={{
          marginTop: 28,
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: 14,
          color: C.muted,
          borderTop: `1px solid ${C.cardBorder}`,
          paddingTop: 16,
        }}
      >
        <span>
          Auditoria e dados abertos:{' '}
          <strong style={{ color: C.cyan }}>github.com/Raixu01/amazon-fire</strong>
        </span>
        <span>Produção: Pulso | .ATM • Remotion v4 • Sem narração</span>
      </div>
    </div>
  );
}

// Master ATMVideo Component (2700 frames @ 30 fps)
export function ATMVideo({ preview = false }) {
  const raw = useCurrentFrame();
  const f = preview && raw >= 150 ? raw - 150 + 900 : raw;

  // 1. Act 1: Intro (0..150f)
  if (f < 150) {
    return <Act1Intro frame={f} />;
  }

  // 2. Act 2: Monthly Pulse (150..750f, 60f/month, 10 months Jan-Oct)
  if (f < 750) {
    const monthIdx = Math.min(9, Math.floor((f - 150) / 60));
    return (
      <AbsoluteFill style={{ background: C.bg, overflow: 'hidden' }}>
        <FullBleedMap frame={f} layer={`mes-${monthKeys[monthIdx]}.png`} />
        <Act2HUD frame={f} monthIdx={monthIdx} />
        {/* Subtle bottom timeline progress indicator */}
        <div
          style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            height: 4,
            width: `${((f - 150) / 600) * 100}%`,
            background: C.cyan,
          }}
        />
      </AbsoluteFill>
    );
  }

  // 3. Act 3: Cinematic Camera Dive & Spotlight (750..900f)
  if (f < 900) {
    const diveLayer = f < 780 ? 'mes-2026-10.png' : null;
    return (
      <AbsoluteFill style={{ background: C.bg, overflow: 'hidden' }}>
        <FullBleedMap frame={f} layer={diveLayer} />
        <Act3HUD />
      </AbsoluteFill>
    );
  }

  // 4. Act 4: Daily Evolution (900..1800f, 60f/day, 15 days Oct 1-15)
  if (f < 1800) {
    const dayIdx = Math.min(14, Math.floor((f - 900) / 60));
    return (
      <AbsoluteFill style={{ background: C.bg, overflow: 'hidden' }}>
        <FullBleedMap frame={f} layer={`dia-${days[dayIdx]}.png`} isRegion />
        <Act4HUD frame={f} dayIdx={dayIdx} />
        <DailyTimelineBar dayIdx={dayIdx} />
      </AbsoluteFill>
    );
  }

  // 5. Act 5A: Regional Cumulative Synthesis (1800..2340f)
  if (f < 2340) {
    return (
      <AbsoluteFill style={{ background: C.bg, overflow: 'hidden' }}>
        <FullBleedMap frame={f} layer="acumulado.png" isRegion />
        <Act5ASynthesis frame={f} />
      </AbsoluteFill>
    );
  }

  // 6. Act 5B: Clean Credits & Methodology (2340..2700f)
  return <Act5BCredits />;
}

// Unified export for ATMShortVideo
export const ATMShortVideo = ATMVideo;
