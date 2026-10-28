const COLORS = ['#102d30', '#245450', '#477c68', '#a3a166', '#d6a75b', '#f29a50'];
const clamp = (x) => Math.min(1, Math.max(0, x));

function stateAtFrame(frame, data) {
  const fps = data.video.fps;
  const f = Math.max(0, Math.min(data.video.duracao_segundos * fps - 1, frame));
  const scene = data.video.cenas.find(s => f >= s.inicio * fps && f < (s.inicio + s.duracao) * fps);
  const local = f - scene.inicio * fps;
  const state = {cena: scene.id, local, ano: 2026, zoom: scene.id === 'zoom_xingu' ? clamp(local/(scene.duracao*fps-1)) : 1};
  if (scene.id === 'historico_duplo') state.ano = 2018 + Math.floor(local/(scene.segundos_por_ano*fps));
  if (scene.id.includes('setembro')) state.mes = 9;
  if (scene.id.includes('outubro')) state.mes = 10;
  if (scene.id.startsWith('diario_')) state.dia = data.dias.filter(d=>Number(d.dia_utc.slice(5,7))===state.mes)[Math.floor(local/(scene.segundos_por_dia*fps))];
  if (scene.id === 'comparativo') state.comparativo = Math.floor(local/(6*fps));
  return state;
}

function fitCamera([x,y,w,h], width, height, padding=.08) {
  let targetW = w*(1+2*padding), targetH = h*(1+2*padding);
  if (targetW/targetH < width/height) targetW=targetH*width/height;
  else targetH=targetW*height/width;
  return [x+w/2-targetW/2, y+h/2-targetH/2, targetW, targetH];
}

function colorFor(value, thresholds) {
  if (value === null || value === undefined) return 'url(#missing)';
  const index = thresholds.findIndex(limit => value <= limit);
  return COLORS[index < 0 ? COLORS.length-1 : index];
}

function labelPositions(municipalities, camera, box) {
  const anchors = municipalities.map(m=>({...m, ax:box.x+(m.anchor[0]-camera[0])*box.w/camera[2],
    ay:box.y+(m.anchor[1]-camera[1])*box.h/camera[3]}));
  const median = [...anchors].map(m=>m.ax).sort((a,b)=>a-b)[Math.floor(anchors.length/2)];
  const result=[];
  for (const side of ['left','right']) {
    const group=anchors.filter(m=>(m.ax<median?'left':'right')===side).sort((a,b)=>a.ay-b.ay);
    const ys=[];
    group.forEach((m,i)=>ys.push(Math.max(m.ay, box.y+30, i ? ys[i-1]+46 : 0)));
    const overflow=Math.max(0,(ys.at(-1)||0)-(box.y+box.h-30));
    group.forEach((m,i)=>result.push({...m, side, x:side==='left'?box.x+215:box.x+box.w-215, y:ys[i]-overflow}));
  }
  return result;
}

function previewFrame(f,data) {
  const fps=data.video.fps;
  const scene=id=>data.video.cenas.find(s=>s.id===id);
  const seek=(id,ratio)=>{const s=scene(id);return s.inicio*fps+Math.round(ratio*(s.duracao*fps-1));};
  if (f<90) return seek('abertura',f/89);
  if (f<360) {const n=f-90,s=scene('historico_duplo');return s.inicio*fps+Math.floor(n/30)*s.segundos_por_ano*fps+Math.round((n%30)*(s.segundos_por_ano*fps-1)/29);}
  if (f<450) return seek('zoom_xingu',(f-360)/89);
  if (f<540) {const s=scene('diario_setembro');return s.inicio*fps+Math.floor((f-450)*30/90)*s.segundos_por_dia*fps+Math.floor(s.segundos_por_dia*fps/2);}
  if (f<630) {const s=scene('diario_outubro');return s.inicio*fps+Math.floor((f-540)*31/90)*s.segundos_por_dia*fps+Math.floor(s.segundos_por_dia*fps/2);}
  if (f<720) {const n=f-630,s=scene('comparativo');return s.inicio*fps+Math.floor(n/30)*180+30+(n%30)*4;}
  return seek('creditos',Math.min(1,(f-720)/29));
}

function dateLabel(iso) {return `${iso.slice(8,10)}/${iso.slice(5,7)}`;}
function windowDates(comparison) {
  const last=new Date(Date.parse(comparison.fim_atual_exclusivo_utc)-1).toISOString();
  return {start:dateLabel(comparison.inicio_atual_utc),end:dateLabel(last),lastDay:last.slice(8,10)};
}
module.exports={COLORS, stateAtFrame, fitCamera, colorFor, labelPositions, previewFrame, dateLabel, windowDates};
