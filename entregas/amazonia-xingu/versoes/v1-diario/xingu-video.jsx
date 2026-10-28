import React, {memo} from 'react';
import {AbsoluteFill, useCurrentFrame, interpolateColors, Easing, delayRender, continueRender} from 'remotion';
import D from './xingu-dados.json';
import {COLORS, stateAtFrame, fitCamera, colorFor, labelPositions, previewFrame, dateLabel, windowDates} from './xingu-model.cjs';

const C={bg:'#071c22',surface:'#0c282e',line:'#315155',text:'#f3f1e7',muted:'#9bb7b5',teal:'#83c2b3',fire:'#ffb469',quiet:'#193a3e'};
const n=x=>x===null||x===undefined?'—':new Intl.NumberFormat('pt-BR').format(x);
const pct=x=>x===null?'—':`${x>=0?'+':''}${x.toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2})}%`;
const clamp=x=>Math.max(0,Math.min(1,x));
const ease=x=>Easing.inOut(Easing.cubic)(clamp(x));
const lerp=(a,b,t)=>a+(b-a)*t;
const region=D.municipios.filter(m=>m.xingu);
const BOX={x:90,y:190,w:1030,h:650};
const HIST={y:340,w:800,h:520,left:98,right:1022};
const FULL=fitCamera(D.map_bounds,HIST.w,HIST.h,.025);
const CLOSE=fitCamera(D.xingu_bounds,BOX.w,BOX.h,.08);
const LABELS=labelPositions(region,CLOSE,BOX);
const CHART_MAX=Math.ceil(Math.max(...D.dias.map(d=>d.focos||0))/50)*50;
const FONT="'Segoe UI', Arial, sans-serif";
const lastClosed=new Date(Date.parse(D.corte_exclusivo_utc)-1).toISOString();
const cutLabel=dateLabel(lastClosed);
const missingDays=D.dias.filter(d=>d.focos===null);
const partialOctober=D.historico.some(m=>m.ano===2026&&m.mes===10&&m.estado!=='validado');

const Text=({children,x,y,size=24,color=C.text,style={},...props})=><div data-xingu-text {...props} style={{position:'absolute',left:x,top:y,fontSize:size,color,lineHeight:1.15,...style}}>{children}</div>;
const Micro=({children,...props})=><Text size={16} color={C.muted} style={{letterSpacing:2,fontWeight:600}} {...props}>{children}</Text>;

const Map=memo(function Map({box,camera=FULL,values=null,scope='all',restOpacity=1,zoom=0,points=[],labels=false,id='map'}) {
  const visible=scope==='xingu'?region:D.municipios;
  const localPattern=`missing-${id}`;
  return <>
    <svg data-map={id} data-municipalities={visible.length} data-points={points.length} style={{position:'absolute',left:box.x,top:box.y,width:box.w,height:box.h,overflow:'hidden'}} viewBox={camera.join(' ')}>
      <defs><pattern id={localPattern} width="6" height="6" patternUnits="userSpaceOnUse"><rect width="6" height="6" fill={C.quiet}/><path d="M0 6L6 0" stroke={C.muted} strokeWidth=".5"/></pattern></defs>
      {visible.map(m=>{
        const historical=values?colorFor(values[m.codigo_ibge],D.escala).replace('#missing',`#${localPattern}`):C.quiet;
        const fill=scope==='xingu'?C.quiet:(m.xingu && zoom>0?interpolateColors(zoom,[0,1],[historical,C.quiet]):historical);
        return <path key={m.codigo_ibge} data-ibge={m.codigo_ibge} data-xingu={m.xingu?'true':'false'} d={m.path} fill={fill} fillRule="evenodd"
          stroke={scope==='xingu'||m.xingu&&zoom>0?C.teal:'#55706d'} strokeWidth={scope==='xingu'?1.15:m.xingu&&zoom>0?lerp(.65,1.15,zoom):.65}
          vectorEffect="non-scaling-stroke" strokeLinejoin="round" opacity={m.xingu?1:restOpacity}/>;
      })}
      {points.map(([x,y,code],i)=><g key={`${x}-${y}-${i}`} data-point-municipality={code}>
        <circle cx={x} cy={y} r={5.4*camera[2]/box.w} fill={C.fire} opacity={.12}/>
        <circle cx={x} cy={y} r={2.65*camera[2]/box.w} fill={C.fire} stroke="#ffe2b4" strokeWidth={.4} vectorEffect="non-scaling-stroke"/>
      </g>)}
    </svg>
    {labels&&<svg style={{position:'absolute',inset:0,width:1920,height:1080,pointerEvents:'none'}}>
      {LABELS.map(m=><g key={m.codigo_ibge}>
        <path d={`M${m.ax},${m.ay}L${m.side==='left'?m.x+16:m.x-16},${m.y}L${m.x},${m.y}`} fill="none" stroke={C.muted} strokeOpacity=".65" strokeWidth=".8"/>
        <circle cx={m.ax} cy={m.ay} r="2" fill={C.teal}/>
        <text x={m.x+(m.side==='left'?-6:6)} y={m.y-8} textAnchor={m.side==='left'?'end':'start'} fill={C.text} fontFamily={FONT} fontSize="18">{m.nome}</text>
      </g>)}
    </svg>}
  </>;
});

function Frame({children,stage,preview,canvasRef}) {
  return <AbsoluteFill ref={canvasRef} data-xingu-canvas style={{width:1920,height:1080,background:C.bg,color:C.text,fontFamily:FONT,fontVariantNumeric:'tabular-nums',overflow:'hidden'}}>
    <div style={{position:'absolute',inset:0,background:'radial-gradient(ellipse at 45% 45%, #11363b44 0%, transparent 72%)'}}/>
    {children}
    <Text x={72} y={39} size={36} style={{fontWeight:750,letterSpacing:-1.5}}>pulso<span style={{color:C.fire}}>.</span></Text>
    <Micro x={230} y={53}>AMAZÔNIA LEGAL / XINGU</Micro>
    <Micro x={1370} y={53} style={{width:478,textAlign:'right'}}>{preview?'PRÉVIA ACELERADA':stage}</Micro>
    <div style={{position:'absolute',left:72,right:72,bottom:51,height:1,background:C.line}}/>
    <Text x={72} y={1043} size={15} color={C.muted}>INPE · AQUA_M-T · Limites IBGE 2024</Text>
    <Text x={1160} y={1043} size={15} color={C.muted} style={{width:688,textAlign:'right'}}>Dados de 2026 até {cutLabel} · UTC{partialOctober?' · Outubro parcial':''}</Text>
  </AbsoluteFill>;
}

function Opening({frame}) {
  const camera=fitCamera(D.map_bounds,1030,770,.04);
  return <>
    <div style={{opacity:.65}}><Map box={{x:850,y:160,w:1030,h:770}} camera={camera} scope="all" id="opening"/></div>
    <svg style={{position:'absolute',left:850,top:160,width:1030,height:770}} viewBox={camera.join(' ')}>
      {region.map(m=><path key={m.codigo_ibge} d={m.path} fill="#7eb6a46a" stroke={C.teal} strokeWidth="1" vectorEffect="non-scaling-stroke"/>)}
    </svg>
    <Micro x={74} y={210} color={C.fire}>SETEMBRO E OUTUBRO · 2018–2026</Micro>
    {['Um território.','Nove anos.','Dia a dia.'].map((line,i)=><Text key={line} x={72+20*(1-ease((frame-i*12)/32))} y={275+i*115} size={100}
      style={{fontWeight:650,letterSpacing:-4,opacity:ease((frame-i*12)/30)}}>{line}</Text>)}
    <Text x={77} y={687} size={27} color={C.muted} style={{lineHeight:1.5}}>Amazônia Legal, em perspectiva.<br/>Região do Xingu, em detalhe.</Text>
    <Text x={77} y={842} size={21} color={C.fire}>Focos de calor detectados por satélite</Text>
    <div style={{position:'absolute',left:77,top:897,width:420*ease(frame/140),height:3,background:C.fire}}/>
  </>;
}

function Legend() {
  const labels=D.escala.map((v,i)=>i===0?'0':`${n(D.escala[i-1]+1)}–${n(v)}`);
  return <div style={{position:'absolute',left:112,top:881,display:'flex',alignItems:'center',gap:14,fontSize:16,color:C.muted}}>
    <span style={{marginRight:8}}>FOCOS / MUNICÍPIO</span>{labels.map((label,i)=><div key={label} style={{display:'flex',alignItems:'center',gap:7}}><span style={{width:19,height:12,background:COLORS[i],border:`1px solid ${C.line}`}}/>{label}</div>)}
    <span style={{marginLeft:15,color:C.teal}}>mesma escala nos dois mapas</span>
  </div>;
}

function History({state,frame,hideOctober=false,opacity=1}) {
  const year=state.ano;
  const elapsed=clamp((frame-180)/1350);
  return <div style={{opacity}} data-year={year}>
    <Text x={72} y={111} size={44} style={{fontWeight:600,letterSpacing:-1}}>Setembro e outubro, ano a ano</Text>
    <Text x={74} y={171} size={22} color={C.muted}>Amazônia Legal · 773 municípios delineados</Text>
    <Text x={1380} y={109} size={104} style={{width:468,textAlign:'right',fontWeight:650,letterSpacing:-5}}>{year}</Text>
    {[9,10].map(month=>{
      const data=D.historico.find(m=>m.ano===year&&m.mes===month);
      const x=month===9?72:996;
      return <React.Fragment key={month}>
        <div style={{position:'absolute',left:x,top:265,width:852,height:596,borderTop:`1px solid ${C.line}`,borderBottom:`1px solid ${C.line}`}}/>
        <Micro x={x+25} y={289} size={22} color={C.text}>{month===9?'SETEMBRO':'OUTUBRO'}</Micro>
        <Text x={x+390} y={278} size={43} style={{width:432,textAlign:'right',fontWeight:600}}>{n(data.focos_observados)}<span style={{fontSize:17,color:C.muted,marginLeft:10}}>focos</span></Text>
        {data.estado==='parcial'&&<Text x={x+24} y={824} size={18} color={C.fire}>PARCIAL · ATÉ {cutLabel}</Text>}
        {!(hideOctober&&month===10)&&<Map id={`history-${month}`} box={{x:month===9?HIST.left:HIST.right,y:HIST.y,w:HIST.w,h:HIST.h}} values={data.municipios}/>}
      </React.Fragment>;
    })}
    <Legend/>
    <div style={{position:'absolute',left:111,top:960,width:1698,height:2,background:C.line}}/>
    <div style={{position:'absolute',left:111,top:960,width:1698*elapsed,height:2,background:C.fire}}/>
    {D.video.cenas&&Array.from({length:9},(_,i)=>2018+i).map((y,i)=><React.Fragment key={y}>
      <div style={{position:'absolute',left:111+i*1698/8-4,top:957,width:8,height:8,borderRadius:'50%',background:y<=year?C.fire:C.line}}/>
      <Text x={78+i*1698/8} y={980} size={y===year?25:20} color={y===year?C.text:C.muted} style={{width:68,textAlign:'center',fontWeight:y===year?700:400}}>{y}</Text>
    </React.Fragment>)}
  </div>;
}

function Zoom({state}) {
  const t=ease(state.zoom);
  const october=D.historico.find(m=>m.ano===2026&&m.mes===10);
  const box={x:lerp(HIST.right,BOX.x,t),y:lerp(HIST.y,BOX.y,t),w:lerp(HIST.w,BOX.w,t),h:lerp(HIST.h,BOX.h,t)};
  const camera=FULL.map((value,i)=>lerp(value,CLOSE[i],t));
  return <>
    <History state={{ano:2026}} frame={1529} hideOctober opacity={1-ease(state.local/55)}/>
    <Map id="zoom" box={box} camera={camera} values={october.municipios} scope={state.zoom===1?'xingu':'all'} restOpacity={(1-t)**2} zoom={t}/>
    <div style={{opacity:ease((state.local-100)/60)}}>
      <Text x={72} y={111} size={46} style={{fontWeight:600}}>Aproximando o olhar: Xingu</Text>
      <Text x={1230} y={330} size={72} color={C.teal} style={{fontWeight:600}}>10</Text>
      <Text x={1233} y={418} size={27}>municípios em destaque</Text>
      <Text x={1233} y={478} size={23} color={C.muted} style={{lineHeight:1.6}}>Região de Integração Xingu<br/>Agora, o tempo avança por dia.</Text>
      <Micro x={1233} y={680}>SETEMBRO + OUTUBRO / 2026</Micro>
    </div>
  </>;
}

function DailyChart({month,day}) {
  const days=D.dias.filter(d=>Number(d.dia_utc.slice(5,7))===month);
  const step=1700/days.length;
  return <>
    <Micro x={90} y={865}>FOCOS POR DIA · {month===9?'SETEMBRO':'OUTUBRO'}</Micro>
    <Text x={1310} y={862} size={17} color={C.muted} style={{width:510,textAlign:'right'}}>Mapa mostra somente a data selecionada · UTC</Text>
    <svg width="1920" height="1080" style={{position:'absolute',inset:0}}>
      <line x1="90" x2="1790" y1="980" y2="980" stroke={C.line}/>
      {days.map((d,i)=>{
        const current=d.dia_utc===day?.dia_utc;
        const h=d.focos===null?72:Math.max(1,(d.focos/CHART_MAX)*72);
        return <g key={d.dia_utc}>
          <rect x={93+i*step} y={980-h} width={step-10} height={h} rx="1" fill={d.focos===null?'none':current?C.fire:C.teal}
            opacity={current?1:.45} stroke={d.focos===null?C.muted:'none'} strokeDasharray={d.focos===null?'3 4':undefined}/>
          <text x={93+i*step+(step-10)/2} y="1006" textAnchor="middle" fontFamily={FONT} fontSize="16" fill={current?C.fire:C.muted}>{i+1}</text>
          {current&&<path d={`M${93+i*step+(step-10)/2-5},1014l5,6l5,-6`} fill={C.fire}/>}
        </g>;
      })}
    </svg>
  </>;
}

function Daily({state,chapter=false}) {
  const month=state.mes;
  const day=chapter?null:state.dia;
  const available=day?.focos!==null&&Boolean(day);
  const cumulative=day?D.dias.filter(d=>d.dia_utc.slice(0,7)===day.dia_utc.slice(0,7)&&d.dia_utc<=day.dia_utc&&d.focos!==null).reduce((sum,d)=>sum+d.focos,0):null;
  const date=day?`${day.dia_utc.slice(8)} / ${month===9?'SET':'OUT'} / 2026`:'2026';
  return <div data-day={day?.dia_utc||'capitulo'} data-coverage={day?.estado||'capitulo'}>
    <Text x={72} y={108} size={46} style={{fontWeight:600}}>Xingu, dia a dia</Text>
    <Text x={74} y={166} size={20} color={C.muted}>Dez municípios · Focos do dia, sem acúmulo no mapa</Text>
    <Text x={1218} y={110} size={38} color={C.teal} style={{width:630,textAlign:'right',fontWeight:600}}>{date}</Text>
    <Map id="daily" box={BOX} camera={CLOSE} scope="xingu" points={available?day.pontos:[]} labels/>
    <div style={{position:'absolute',left:1198,top:222,bottom:257,width:1,background:C.line}}/>
    {chapter?<>
      <Micro x={1250} y={273}>EVOLUÇÃO DIÁRIA</Micro>
      <Text x={1246} y={318} size={64} style={{fontWeight:600,letterSpacing:-2}}>{month===9?'Setembro':'Outubro'}</Text>
      <Text x={1250} y={413} size={34} color={C.teal}>01 → {month===9?'30':'31'}</Text>
      <Text x={1250} y={485} size={25} color={C.muted} style={{lineHeight:1.6}}>Um segundo por dia.<br/>Cada ponto, uma detecção.</Text>
      {month===10&&partialOctober&&<Text x={1250} y={645} size={21} color={C.fire} style={{lineHeight:1.5}}>Dados validados até {cutLabel}.<br/>Demais datas, sem observações exibidas.</Text>}
    </>:<>
      <Micro x={1250} y={225}>FOCOS NESTE DIA</Micro>
      <Text x={1243} y={251} size={104} color={available?C.fire:C.muted} style={{fontWeight:650,letterSpacing:-4}}>{n(day.focos)}</Text>
      {available?<Text x={1250} y={373} size={21} color={C.muted}>Acumulado do mês <span style={{color:C.text,fontWeight:600}}>{n(cumulative)}</span></Text>:
        <Text x={1250} y={372} size={21} color={C.fire}>{day.estado==='futuro'?'Ainda não observado':'Fora do corte validado'}</Text>}
      <Micro x={1250} y={434}>MUNICÍPIOS · FOCOS NO DIA</Micro>
      {region.map((m,i)=>{
        const count=day.municipios[m.codigo_ibge];
        return <React.Fragment key={m.codigo_ibge}>
          <Text x={1250} y={478+i*32} size={21} color={count?C.text:C.muted}>{m.nome}</Text>
          <Text x={1707} y={478+i*32} size={21} color={count?C.fire:C.muted} style={{width:105,textAlign:'right',fontWeight:600}}>{n(count)}</Text>
        </React.Fragment>;
      })}
    </>}
    <DailyChart month={month} day={day}/>
  </div>;
}

function Comparison({state}) {
  const comparison=D.comparativos[state.comparativo];
  const dates=windowDates(comparison);
  const monthName=state.comparativo===0?'Setembro':'Outubro';
  const period=state.comparativo===2?'Soma das janelas comparadas':comparison.parcial?`${monthName} · dias 1–${dates.lastDay}`:`${monthName} completo`;
  const progress=Easing.out(Easing.cubic)(clamp((state.local%180)/36));
  const maximum=Math.max(comparison.atual||0,comparison.anterior||0,1);
  return <div data-comparison={comparison.periodo}>
    <Text x={72} y={111} size={47} style={{fontWeight:600}}>Xingu: o que mudou em um ano?</Text>
    <Text x={74} y={174} size={22} color={C.muted}>Mesmo sensor e municípios · Períodos equivalentes em UTC</Text>
    <Micro x={104} y={267} color={C.fire} size={22}>{period.toUpperCase()}</Micro>
    {[{year:2025,value:comparison.anterior,x:104,color:C.teal},{year:2026,value:comparison.atual,x:698,color:C.fire}].map(v=><React.Fragment key={v.year}>
      <Text x={v.x} y={335} size={28} color={C.muted}>{v.year}</Text>
      <Text x={v.x-4} y={385} size={104} style={{fontWeight:650,letterSpacing:-3}}>{n(v.value)}</Text>
      <Text x={v.x+2} y={510} size={21} color={C.muted}>focos detectados</Text>
      <div style={{position:'absolute',left:v.x,top:816-(v.value||0)/maximum*230*progress,width:380,height:(v.value||0)/maximum*230*progress,background:v.color}}/>
      <div style={{position:'absolute',left:v.x,top:817,width:380,height:1,background:C.line}}/>
    </React.Fragment>)}
    <div style={{position:'absolute',left:1260,top:291,width:588,height:559,background:C.surface,borderTop:`2px solid ${C.fire}`}}/>
    <Micro x={1300} y={339}>VARIAÇÃO NOS FOCOS</Micro>
    <Text x={1293} y={400} size={85} color={C.fire} style={{fontWeight:600,letterSpacing:-3}}>{pct(comparison.variacao_pct)}</Text>
    <Text x={1300} y={540} size={38}>{n(Math.abs(comparison.diferenca||0))} {comparison.diferenca>=0?'a mais':'a menos'}</Text>
    <Text x={1300} y={635} size={23} color={C.muted} style={{width:480,lineHeight:1.6}}>{comparison.parcial?`${dates.start} a ${dates.end} nos dois anos. A mesma janela de observação.`:'Mês completo nos dois anos.'}</Text>
    <Text x={106} y={868} size={20} color={C.muted}>{dates.start} a {dates.end} em cada ano</Text>
    {['SETEMBRO',partialOctober?'OUTUBRO PARCIAL':'OUTUBRO','CONJUNTO'].map((label,i)=><React.Fragment key={label}>
      <div style={{position:'absolute',left:104+i*580,top:962,width:520,height:2,background:i===state.comparativo?C.fire:C.line}}/>
      <Micro x={104+i*580} y={985} color={i===state.comparativo?C.text:C.muted}>{label}</Micro>
    </React.Fragment>)}
  </div>;
}

function Credits() {
  return <>
    <Text x={106} y={222} size={96} style={{fontWeight:650,letterSpacing:-4}}>O tempo muda.<br/>O território permanece.</Text>
    <Text x={111} y={499} size={31} color={C.teal}>Amazônia Legal → Região de Integração Xingu</Text>
    <div style={{position:'absolute',left:111,top:589,width:1698,height:1,background:C.line}}/>
    <Text x={111} y={638} size={26} style={{lineHeight:1.8}}>Dados: INPE · Programa Queimadas<br/>Limites: IBGE · Amazônia Legal 2024<br/>Satélite: AQUA_M-T · Datas e períodos em UTC</Text>
    <Text x={1100} y={649} size={23} color={C.muted} style={{width:680,lineHeight:1.7}}>Corte: {dateLabel(D.corte_exclusivo_utc)}/2026 às 00h UTC, fim exclusivo.<br/>{missingDays.length?`${dateLabel(missingDays[0].dia_utc)}–${dateLabel(missingDays.at(-1).dia_utc)} não entram nas contagens desta edição.`:'Setembro e outubro completos nesta edição.'}<br/><br/>Focos de calor não equivalem a incêndios únicos<br/>ou a uma medida de área queimada.</Text>
    <Text x={111} y={943} size={16} color={C.muted}>Base auditada · {D.snapshot_id}</Text>
  </>;
}

export function XinguVideo({preview=false,qa=false}) {
  const rawFrame=useCurrentFrame();
  const frame=preview?previewFrame(rawFrame):rawFrame;
  const state=stateAtFrame(frame,D);
  const canvasRef=React.useRef(null);
  React.useLayoutEffect(()=>{
    if (!qa) return;
    const handle=delayRender('Conferindo geometria e texto no navegador');
    requestAnimationFrame(()=>{
    const root=canvasRef.current;
    const maps=[...root.querySelectorAll('svg[data-map]')].map(svg=>({id:svg.dataset.map,
      municipalities:svg.querySelectorAll('path[data-ibge]').length,points:svg.querySelectorAll('[data-point-municipality]').length}));
    const canvas=root.getBoundingClientRect();
    const outsideText=[...root.querySelectorAll('[data-xingu-text]')].filter(element=>{
      const rect=element.getBoundingClientRect();
      return rect.left < canvas.left-1 || rect.top < canvas.top-1 || rect.right > canvas.right+1 || rect.bottom > canvas.bottom+1;
    }).map(e=>e.textContent);
    console.info('XINGU_QA:'+JSON.stringify({frame,scene:state.cena,maps,outsideText,canvas:canvas.toJSON()}));
    continueRender(handle);
    });
  },[frame,qa,state.cena]);
  const stage=state.cena==='historico_duplo'||state.cena==='abertura'?'01 / PANORAMA':state.cena==='comparativo'||state.cena==='creditos'?'03 / COMPARAÇÃO':'02 / XINGU';
  return <Frame stage={stage} preview={preview} canvasRef={canvasRef}>
    {state.cena==='abertura'&&<Opening frame={frame}/>}
    {state.cena==='historico_duplo'&&<History state={state} frame={frame}/>}
    {state.cena==='zoom_xingu'&&<Zoom state={state}/>}
    {(state.cena==='titulo_setembro'||state.cena==='titulo_outubro')&&<Daily state={state} chapter/>}
    {state.cena.startsWith('diario_')&&<Daily state={state}/>}
    {state.cena==='comparativo'&&<Comparison state={state}/>}
    {state.cena==='creditos'&&<Credits/>}
  </Frame>;
}
