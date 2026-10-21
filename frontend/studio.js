'use strict';
const cleanLabels={trim:'Quitar espacios exteriores',collapse_spaces:'Unificar espacios',upper:'MAYÚSCULAS',lower:'minúsculas',strip_accents:'Quitar tildes',null_markers:'Reconocer vacíos',replace:'Sustituir texto',fill_null:'Rellenar vacíos',to_number:'Convertir a número',to_date:'Convertir a fecha',to_boolean:'Convertir a sí / no',to_text:'Convertir a texto',deduplicate:'Quitar duplicados',drop_empty:'Quitar filas vacías',drop_missing:'Quitar filas con vacíos',keep_rows:'Conservar filas por condición'};
const filterLabels={eq:'igual a',ne:'distinto de',in:'uno de',not_in:'ninguno de',contains:'contiene',not_contains:'no contiene',starts_with:'empieza por',ends_with:'termina en',between:'entre',gte:'≥',lte:'≤',gt:'>',lt:'<',is_blank:'vacío',not_blank:'no vacío'};
const C={steps:[],preview:null,table:'',busy:false};
F.filterSelection=new Map();F.distinctValues=[];
const valueLabel=v=>v===null?'(nulo)':v===''?'(texto vacío)':typeof v==='boolean'?(v?'Sí':'No'):String(v);
const shortJson=v=>v===null?'(nulo)':typeof v==='string'?JSON.stringify(v):String(v);
const chartPalette=['#39d5bc','#75adff','#ffca70','#c5a1ff','#ff91aa','#b9d966','#ffac72','#89d9ec'];

function setTheme(theme){
 document.documentElement.dataset.theme=theme;
 document.documentElement.style.colorScheme=theme;
 $('themeToggle').textContent=theme==='dark'?'☀ Tema claro':'☾ Tema oscuro';
 $('themeToggle').setAttribute('aria-label',theme==='dark'?'Cambiar a tema claro':'Cambiar a tema oscuro');
 try{localStorage.setItem('abbi-theme',theme)}catch{}
}
function filterDescription(rule){
 if(rule===null||typeof rule!=='object')return '= '+valueLabel(rule);
 if(['in','not_in'].includes(rule.op))return filterLabels[rule.op]+' '+rule.values.map(valueLabel).join(', ');
 if(rule.op==='between')return 'entre '+valueLabel(rule.value)+' y '+valueLabel(rule.value2);
 return filterLabels[rule.op]+(rule.value!==undefined?' '+valueLabel(rule.value):'');
}
function filterRenderer(){
 const keys=Object.keys(F.filters);
 $('activeFilters').innerHTML=keys.length?keys.map((key,i)=>`<div class="filter-pill"><span><b>${e(key)}</b><br>${e(filterDescription(F.filters[key]))}</span><button data-dropfilter="${i}" aria-label="Quitar filtro ${e(key)}">×</button></div>`).join(''):'<span class="muted small">Sin filtros activos</span>';
 $('activeFilters').querySelectorAll('[data-dropfilter]').forEach(btn=>btn.onclick=()=>{
  const next={...F.filters};delete next[keys[Number(btn.dataset.dropfilter)]];commitFilters(next).catch(err=>toast(err.message,true));
 });
}
async function commitFilters(next=F.filters){
 const result=await post('/api/filters',next);F.filters={...result.filters};F.model=result;
 F.dataPage=0;filterRenderer();
 if(F.view==='data')await renderData();else if(F.view==='measures')await evalDax();else await refreshDashboard();
}
function filterControls(){
 const op=$('filterOp').value,multi=['in','not_in'].includes(op),range=op==='between',empty=['is_blank','not_blank'].includes(op);
 $('filterSingleWrap').hidden=multi||range||empty;
 $('filterMultiWrap').hidden=!multi;$('filterRangeWrap').hidden=!range;$('filterTypeWrap').hidden=empty;
 const kind=$('filterType').value;
 for(const id of ['filterFrom','filterTo']){$(id).type=kind==='date'?'date':'text';$(id).placeholder=kind==='number'?'Número sin separador de miles':'Valor'}
 $('filterCustom').type=kind==='date'?'date':'text';
 $('filterCustom').placeholder=kind==='number'?'Ej. 1234,56, sin miles':'Escribe un valor';
}
let distinctSequence=0;
async function loadDistinct(){
 const field=$('filterDimension').value;if(!field)return;
 const sequence=++distinctSequence,search=$('filterSearch')?.value||'';
 const result=await req(`/api/distinct?field=${encodeURIComponent(field)}&search=${encodeURIComponent(search)}`);
 if(sequence!==distinctSequence||field!==$('filterDimension').value)return;
 F.distinctValues=result.values;
 opts($('filterValue'),result.values.map(v=>[JSON.stringify(v),valueLabel(v)]));
 $('filterChoices').innerHTML=result.values.length?result.values.map((v,i)=>`<label class="check-option"><input type="checkbox" data-choice="${i}" ${F.filterSelection.has(JSON.stringify(v))?'checked':''}><span>${e(valueLabel(v))}</span></label>`).join(''):'<span class="muted small">No hay valores coincidentes.</span>';
 $('filterChoices').querySelectorAll('[data-choice]').forEach(input=>input.onchange=()=>{
  const val=F.distinctValues[Number(input.dataset.choice)],key=JSON.stringify(val);
  if(input.checked)F.filterSelection.set(key,val);else F.filterSelection.delete(key);
  $('filterSelected').textContent=F.filterSelection.size+' valores seleccionados';
 });
 $('filterSelected').textContent=F.filterSelection.size+' valores seleccionados';
 $('filterHint').textContent=result.truncated?`Mostrando 300 de ${fmt(result.total,0)}. Busca para encontrar otros valores.`:`${fmt(result.total,0)} valores disponibles`;
}
async function applyAdvancedFilter(){
 const field=$('filterDimension').value,op=$('filterOp').value,kind=$('filterType').value;
 if(!field)throw Error('Selecciona un campo');
 let rule={op,type:kind};
 if(['in','not_in'].includes(op)){
  rule.values=[...F.filterSelection.values()];if(!rule.values.length)throw Error('Selecciona al menos un valor');
 }else if(op==='between'){
  rule.value=$('filterFrom').value;rule.value2=$('filterTo').value;
 }else if(!['is_blank','not_blank'].includes(op)){
  rule.value=$('filterCustom').value!==''?$('filterCustom').value:($('filterValue').value?JSON.parse($('filterValue').value):'');
  if(rule.value===null){if(op==='eq')rule={op:'is_blank',type:kind};else if(op==='ne')rule={op:'not_blank',type:kind}}
 }
 await commitFilters({...F.filters,[field]:rule});toast('Filtro aplicado al informe y a las tablas');
}

let dashboardSequence=0;
async function refreshDashboard(){
 if(!F.model)return;filterRenderer();const sequence=++dashboardSequence;
 $('visualGrid').setAttribute('aria-busy','true');
 try{
  const result=await post('/api/dashboard',{filters:F.filters});if(sequence!==dashboardSequence)return;
  F.lastVisuals=result.visuals;
  $('kpiRow').innerHTML=result.visuals.filter(v=>v.type==='kpi').map(v=>`<div class="kpi"><div class="kpi-name">${e(v.title)}</div><strong>${v.error?'Error':e(fmt(v.result?.value,2))}</strong><div class="kpi-foot">MEDIDA SEMÁNTICA <button class="mini-btn" data-edit="${e(v.id)}" aria-label="Editar ${e(v.title)}">✎</button></div>${v.error?`<span class="small">${e(v.error)}</span>`:''}</div>`).join('');
  $('visualGrid').innerHTML=result.visuals.filter(v=>v.type!=='kpi').map(renderVisual).join('')||'<div class="empty">Crea una visualización para empezar.</div>';
  document.querySelectorAll('[data-edit]').forEach(b=>b.onclick=()=>editVisual(b.dataset.edit));
  document.querySelectorAll('[data-delete]').forEach(b=>b.onclick=()=>removeVisual(b.dataset.delete));bindChartActions();
 }catch(err){toast(err.message,true)}finally{if(sequence===dashboardSequence)$('visualGrid').setAttribute('aria-busy','false')}
}
function renderVisual(v){
 return `<article class="viz-card" data-visual-id="${e(v.id)}"><div class="viz-titlebar"><div><h3>${e(v.title)}</h3><div class="meta">${e(v.measure)} · ${e(v.dimension||'Global')}</div></div><div class="viz-actions"><button class="mini-btn" data-chart-export aria-label="Descargar gráfico SVG" title="Descargar SVG">⇩</button><button class="mini-btn" data-edit="${e(v.id)}" aria-label="Editar visualización">✎</button><button class="mini-btn" data-delete="${e(v.id)}" aria-label="Eliminar visualización">✕</button></div></div><div class="chart-area">${v.error?`<div class="viz-error">${e(v.error)}</div>`:chart(v.type,v.result?.data||[])}</div>${v.result?.truncated?'<p class="chart-note">Vista parcial: se muestran las categorías seleccionadas por el límite del gráfico (hasta 200 evaluadas). Amplía el límite o aplica filtros.</p>':''}${v.type==='donut'?'<p class="chart-note">Porcentajes de las categorías visibles. Pulsa un segmento o su leyenda para filtrar.</p>':''}</article>`;
}
function chart(type,data){
 if(!data.length)return '<div class="empty">No hay registros para los filtros seleccionados.</div>';
 if(type==='table')return `<div class="table-viz"><table><thead><tr><th>Dimensión</th><th>Valor</th></tr></thead><tbody>${data.map((d,i)=>`<tr><td><button class="text-button" data-group="${i}">${e(d.label)}</button></td><td>${e(fmt(d.value,2))}</td></tr>`).join('')}</tbody></table></div>`;
 const vals=data.map(d=>Number(d.value)||0),high=Math.max(0,...vals),low=Math.min(0,...vals),max=high===low?1:high,min=low;
 const title=(d)=>e(`${valueLabel(d.label)}: ${fmt(d.value,2)}`);
 if(type==='donut'){
  if(vals.some(v=>v<0))return '<div class="empty">El donut requiere valores no negativos. Usa barras o líneas para mostrar valores negativos.</div>';
  const total=vals.reduce((a,b)=>a+b,0);if(total<=0)return '<div class="empty">No hay valores positivos para formar el donut.</div>';
  const circumference=2*Math.PI*50;let cursor=0;
  const paths=vals.map((n,i)=>{const fraction=n/total,start=cursor;cursor+=fraction;return n>0?`<circle class="donut-segment" data-group="${i}" tabindex="0" role="button" aria-label="Filtrar ${title(data[i])}, ${fmt(fraction*100,1)} por ciento" cx="80" cy="80" r="50" fill="none" stroke="${chartPalette[i%chartPalette.length]}" stroke-width="25" stroke-dasharray="${fraction*circumference} ${circumference}" stroke-dashoffset="${-start*circumference}" transform="rotate(-90 80 80)"><title>${title(data[i])} (${fmt(fraction*100,1)}%)</title></circle>`:''}).join('');
  return `<div class="donut-wrap"><svg class="donut-svg" viewBox="0 0 160 160" aria-label="Distribución por categorías"><circle class="donut-track" cx="80" cy="80" r="50" fill="none" stroke-width="25"/>${paths}<text class="donut-total" x="80" y="77" text-anchor="middle">${data.length}</text><text class="donut-caption" x="80" y="95" text-anchor="middle">GRUPOS</text></svg><div class="donut-legend">${data.map((d,i)=>`<button class="legend-row legend-button" data-group="${i}" title="Filtrar ${e(d.label)}"><span><i class="legend-color" style="background:${chartPalette[i%chartPalette.length]}"></i><span class="legend-label">${e(d.label)}</span></span><span class="legend-value"><b>${e(fmt(d.value,1))}</b><small>${fmt(vals[i]/total*100,1)} %</small></span></button>`).join('')}</div></div>`;
 }
 const control=(i,d)=>`data-group="${i}" tabindex="0" role="button" aria-label="Filtrar ${title(d)}"`;
 if(type==='hbar'){
  const W=480,H=Math.max(190,data.length*29),left=105,right=65,iw=W-left-right,rowH=(H-8)/data.length,x=n=>left+(n-min)/(max-min)*iw,zero=x(0);
  return `<svg viewBox="0 0 ${W} ${H}" aria-label="Barras horizontales"><line class="gridline zero-line" x1="${zero}" x2="${zero}" y1="0" y2="${H}"/>${data.map((d,i)=>{const y=i*rowH+5,end=x(vals[i]);return `<g ${control(i,d)}><text x="${left-8}" y="${y+rowH*.5}" text-anchor="end">${e(String(d.label).slice(0,16))}<title>${e(d.label)}</title></text><rect class="bar ${vals[i]<0?'negative':''}" x="${Math.min(zero,end)}" y="${y}" width="${Math.abs(end-zero)}" height="${Math.max(4,rowH-9)}" rx="3"><title>${title(d)}</title></rect><text x="${W-4}" y="${y+rowH*.5}" text-anchor="end">${fmt(d.value,0)}</text></g>`}).join('')}</svg>`;
 }
 const W=470,H=235,l=52,r=15,t=15,b=44,ih=H-t-b,iw=W-l-r,y=n=>t+ih-(n-min)/(max-min)*ih,zero=y(0);
 const axes=Array.from({length:5},(_,i)=>{const value=max-(max-min)*i/4,yy=y(value);return `<line class="gridline" x1="${l}" y1="${yy}" x2="${W-r}" y2="${yy}"/><text x="${l-8}" y="${yy+4}" text-anchor="end">${fmt(value,0)}</text>`}).join('')+`<line class="gridline zero-line" x1="${l}" x2="${W-r}" y1="${zero}" y2="${zero}"/>`;
 const labels=data.map((d,i)=>i%Math.ceil(data.length/7)===0?`<text x="${l+(i+.5)*iw/data.length}" y="${H-15}" text-anchor="middle">${e(String(d.label).slice(0,11))}<title>${e(d.label)}</title></text>`:'').join('');
 if(type==='bar')return `<svg viewBox="0 0 ${W} ${H}" aria-label="Barras verticales">${axes}${data.map((d,i)=>{const step=iw/data.length,point=y(vals[i]);return `<rect ${control(i,d)} class="bar ${vals[i]<0?'negative':''}" x="${l+i*step+step*.15}" y="${Math.min(point,zero)}" width="${step*.7}" height="${Math.abs(zero-point)}" rx="2"><title>${title(d)}</title></rect>`}).join('')}${labels}</svg>`;
 if(type==='line'||type==='area'){
  const points=data.map((d,i)=>[l+(i+.5)*iw/data.length,y(vals[i])]);const path=points.map((p,i)=>`${i?'L':'M'}${p[0]},${p[1]}`).join(' ');
  return `<svg viewBox="0 0 ${W} ${H}" aria-label="Serie de datos">${axes}${type==='area'?`<path class="area-shape" d="${path} L${points.at(-1)[0]},${zero} L${points[0][0]},${zero} Z"/>`:''}<path class="linepath" d="${path}"/>${points.map((p,i)=>`<circle ${control(i,data[i])} class="line-point" cx="${p[0]}" cy="${p[1]}" r="4"><title>${title(data[i])}</title></circle>`).join('')}${labels}</svg>`;
 }
 return '<div class="empty">Tipo de gráfico no admitido.</div>';
}
function bindChartActions(){
 document.querySelectorAll('[data-group]').forEach(node=>{
  const activate=async()=>{
   const card=node.closest('[data-visual-id]'),visual=F.lastVisuals.find(v=>v.id===card.dataset.visualId),datum=visual?.result?.data?.[Number(node.dataset.group)];
   if(!datum)return;try{await commitFilters({...F.filters,[visual.dimension]:datum.key});toast('Categoría aplicada como filtro')}catch(err){toast(err.message,true)}
  };
  node.onclick=activate;node.onkeydown=event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();activate()}};
 });
 document.querySelectorAll('[data-chart-export]').forEach(node=>node.onclick=()=>{
  const card=node.closest('[data-visual-id]'),svg=card.querySelector('svg');if(!svg)return toast('Esta vista se exporta desde Tablas de datos',true);
  const clone=svg.cloneNode(true),source=[svg,...svg.querySelectorAll('*')],target=[clone,...clone.querySelectorAll('*')];
  source.forEach((el,i)=>{const style=getComputedStyle(el);for(const property of ['fill','stroke','stroke-width','stroke-dasharray','stroke-dashoffset','font-family','font-size','font-weight','opacity'])target[i].style.setProperty(property,style.getPropertyValue(property))});
  clone.setAttribute('xmlns','http://www.w3.org/2000/svg');clone.setAttribute('width','900');clone.setAttribute('height',svg.classList.contains('donut-svg')?'900':'450');clone.style.background=getComputedStyle(card).backgroundColor;
  const name=card.querySelector('h3').textContent.replace(/[^\wáéíóúñ .-]/gi,'_');downloadBlob(new Blob([new XMLSerializer().serializeToString(clone)],{type:'image/svg+xml'}),name+'.svg');
 });
}

function dataQuery(offset=F.dataPage*40,limit=40){return {table:F.dataTable,filters:F.filters,search:$('dataSearch').value,sort_column:$('dataSort').value,sort_type:$('dataSortType').value,sort_direction:$('dataSortDirection').value,offset,limit}}
let tableSequence=0;
async function renderData(){
 const name=$('dataTableSelect').value||F.dataTable;F.dataTable=name;if(!name)return;
 const cols=F.model.tables.find(t=>t.name===name)?.columns||[],old=$('dataSort').value;
 opts($('dataSort'),[['','Orden de origen'],...cols.map(c=>[c,c])],cols.includes(old)?old:'');
 const sequence=++tableSequence;
 try{
  const data=await post('/api/table-query',dataQuery());if(sequence!==tableSequence)return;
  if(F.dataPage>0&&F.dataPage*40>=data.total){F.dataPage=0;return renderData()}
  $('dataInfo').textContent=`${fmt(data.total,0)} de ${fmt(data.source_total,0)} filas · ${cols.length} columnas`;
  $('dataFilterInfo').textContent=Object.keys(F.filters).length?Object.entries(F.filters).map(([key,rule])=>key+' '+filterDescription(rule)).join(' · '):'Sin filtros del informe';
  $('dataHead').innerHTML='<tr>'+cols.map(c=>`<th>${e(c)}</th>`).join('')+'</tr>';
  $('dataBody').innerHTML=data.rows.length?data.rows.map(row=>'<tr>'+cols.map(c=>`<td>${row[c]===null||row[c]===undefined?'<span class="null-value">nulo</span>':e(row[c])}</td>`).join('')+'</tr>').join(''):`<tr><td colspan="${Math.max(1,cols.length)}">No hay filas que cumplan los criterios.</td></tr>`;
  $('dataPage').textContent=`Página ${F.dataPage+1} de ${Math.max(1,Math.ceil(data.total/40))}`;$('prevRows').disabled=F.dataPage===0;$('nextRows').disabled=(F.dataPage+1)*40>=data.total;
 }catch(err){toast(err.message,true)}
}
async function exportCsv(){
 const button=$('exportTableCsv');button.disabled=true;
 try{
  const query=dataQuery(0,500),rows=[];let revision,total,columns;
  do{const data=await post('/api/table-query',{...query,offset:rows.length,revision});revision=data.revision;total=data.total;columns=data.columns;rows.push(...data.rows);if(!data.rows.length)break}while(rows.length<total);
  const raw=[columns.map(csvEscape).join(';'),...rows.map(row=>columns.map(c=>csvEscape(row[c])).join(';'))].join('\r\n');
  downloadBlob(new Blob(['\ufeff',raw],{type:'text/csv;charset=utf-8'}),F.dataTable+'_filtrado.csv');toast(`${fmt(rows.length,0)} filas exportadas`);
 }catch(err){toast(err.message,true)}finally{button.disabled=false}
}
async function renderProfile(){
 const name=$('profileTableSelect').value||F.dataTable;if(!name)return;
 try{
  const profile=await req('/api/profile/'+encodeURIComponent(name));
  $('qualitySummary').innerHTML=[['Filas',profile.rows],['Vacíos',profile.missing_cells],['Filas duplicadas',profile.duplicate_rows],['Celdas con espacios exteriores',profile.whitespace_cells]].map(([label,value])=>`<div class="stat-chip">${e(label)}<strong>${fmt(value,0)}</strong></div>`).join('')+'<button class="btn primary" id="qualityClean">Preparar esta tabla →</button>';
  $('qualityClean').onclick=()=>{C.table=name;show('clean')};
  $('profileCards').innerHTML=profile.columns.map(col=>`<div class="panel quality-card"><div class="section-header"><h3>${e(col.name)}</h3><span class="tag">${e(col.type)}</span></div><div class="quality-bar" aria-label="${fmt(col.count/Math.max(1,profile.rows)*100,1)} por ciento completo"><span style="width:${col.count/Math.max(1,profile.rows)*100}%"></span></div><p class="small muted">${fmt(col.count,0)} valores · ${fmt(col.missing,0)} vacíos · ${fmt(col.distinct,0)} únicos</p>${col.whitespace?`<p class="quality-warning small">${col.whitespace} con espacios al inicio o al final</p>`:''}${col.numeric_candidates&&col.non_numeric?`<p class="quality-warning small">Tipos mezclados: ${col.numeric_candidates} numéricos y ${col.non_numeric} no numéricos</p>`:''}${col.type==='Número'?`<p class="small">Mín. <b>${fmt(col.min,2)}</b> · Máx. <b>${fmt(col.max,2)}</b><br>Media <b>${fmt(col.average,2)}</b></p>`:''}<div class="quality-values">${col.most_common.map(([v,n])=>`<div class="legend-row small"><span>${e(v.slice(0,50))}</span><b>${fmt(n,0)}</b></div>`).join('')}</div></div>`).join('');
 }catch(err){toast(err.message,true)}
}

function invalidatePreview(){C.preview=null;$('applyClean').disabled=true;$('cleanPreview').innerHTML='<p class="muted">La receta ha cambiado. Genera otra vista previa para revisar el resultado.</p>'}
function cleanColumns(){
 const names=F.model.tables.find(t=>t.name===$('cleanTable').value)?.columns||[];
 $('cleanColumns').innerHTML=names.map((name,i)=>`<label class="check-option"><input type="checkbox" value="${e(name)}" ${i===0?'checked':''}><span>${e(name)}</span></label>`).join('');
}
function cleanOptions(){
 const op=$('cleanOperation').value;
 $('cleanValueWrap').hidden=!['replace','fill_null','null_markers'].includes(op);$('cleanReplacementWrap').hidden=op!=='replace';$('cleanLocaleWrap').hidden=op!=='to_number';$('cleanDateWrap').hidden=op!=='to_date';$('cleanErrorWrap').hidden=!['to_number','to_date','to_boolean'].includes(op);$('cleanRuleWrap').hidden=op!=='keep_rows';
 $('cleanValueLabel').textContent=op==='null_markers'?'Marcadores separados por ;':op==='replace'?'Buscar texto literal':'Rellenar con este texto';
 const help={deduplicate:'Se conserva la primera fila de cada combinación de las columnas elegidas.',drop_empty:'Se eliminan filas solo si todas las columnas elegidas están vacías.',drop_missing:'Se elimina una fila si alguna de las columnas elegidas está vacía.',keep_rows:'Elige una sola columna y una condición. Este paso elimina las filas que no la cumplen.',null_markers:'Ejemplo: null; N/A; -; sin dato. También se reconoce el texto vacío.',to_date:'La fecha de salida usa AAAA-MM-DD. Elige el formato real de tus datos para evitar confundir días y meses.',to_number:'Elige el separador decimal de los datos de origen. Se informa de cada valor que no se puede convertir.',fill_null:'Los valores se rellenan como texto. Añade después una conversión si necesitas números o fechas.',strip_accents:'Transforma también ñ en n. Revisa las columnas de identificadores antes de aplicar.'};
 $('cleanHelp').textContent=help[op]||'Solo se modifica el contenido de las columnas elegidas. El resto se conserva.';
}
function renderRecipe(){
 document.querySelector('.clean-layout').inert=C.busy;
 $('cleanStepCount').textContent=C.steps.length+' pasos';
 $('cleanSteps').innerHTML=C.steps.length?C.steps.map((step,i)=>`<li><div><b>${e(cleanLabels[step.op]||step.op)}</b><small>${e(step.columns.join(', '))}${step.value!==undefined?' · '+e(shortJson(step.value)):''}${step.rule?' · '+e(filterDescription(step.rule)):''}</small></div><div class="recipe-actions"><button class="mini-btn" data-up="${i}" ${i===0?'disabled':''} aria-label="Subir paso ${i+1}">↑</button><button class="mini-btn" data-down="${i}" ${i===C.steps.length-1?'disabled':''} aria-label="Bajar paso ${i+1}">↓</button><button class="mini-btn" data-remove="${i}" aria-label="Quitar paso ${i+1}">×</button></div></li>`).join(''):'<li class="recipe-empty">Tu receta está vacía. Elige una transformación y pulsa «Añadir paso».</li>';
 $('previewClean').disabled=!C.steps.length||C.busy;$('exportRecipe').disabled=!C.steps.length;
 for(const [attr,delta] of [['up',-1],['down',1]])$('cleanSteps').querySelectorAll(`[data-${attr}]`).forEach(button=>button.onclick=()=>{const i=Number(button.dataset[attr]);[C.steps[i],C.steps[i+delta]]=[C.steps[i+delta],C.steps[i]];invalidatePreview();renderRecipe()});
 $('cleanSteps').querySelectorAll('[data-remove]').forEach(button=>button.onclick=()=>{C.steps.splice(Number(button.dataset.remove),1);invalidatePreview();renderRecipe()});
}
async function renderCleaning(){
 const names=F.model.tables.map(t=>t.name),table=names.includes(C.table)?C.table:(F.dataTable||names[0]);
 if(C.table!==table&&C.steps.length){C.steps=[];invalidatePreview()}
 const changed=$('cleanTable').value!==table;if(changed&&C.steps.length){C.steps=[];invalidatePreview()}C.table=table;opts($('cleanTable'),names.map(n=>[n,n]),table);if(changed||!$('cleanColumns').children.length)cleanColumns();cleanOptions();renderRecipe();
 try{
  const status=await req('/api/cleaning/status');$('undoClean').disabled=!status.can_undo;
  $('cleanHistory').innerHTML='<h3>Historial de preparación</h3>'+(status.history.length?status.history.slice().reverse().slice(0,8).map(entry=>`<div class="history-item"><b>${e(entry.table)}</b><span>${e(new Date(entry.at).toLocaleString('es-ES'))}</span><small>${entry.steps.length} pasos · ${fmt(entry.changed_cells,0)} celdas · ${fmt(entry.before_rows,0)} → ${fmt(entry.after_rows,0)} filas</small></div>`).join(''):'<p class="muted small">Las limpiezas aplicadas aparecerán aquí y se guardarán en el proyecto.</p>');
 }catch(err){toast(err.message,true)}
}
function addCleanStep(){
 if(C.steps.length>=20)throw Error('Máximo 20 pasos por receta');
 const columns=[...$('cleanColumns').querySelectorAll('input:checked')].map(input=>input.value);if(!columns.length)throw Error('Selecciona al menos una columna');
 const op=$('cleanOperation').value,step={op,columns};
 if(['replace','fill_null'].includes(op))step.value=$('cleanValue').value;
 if(op==='replace'){if(!step.value)throw Error('Indica el texto que quieres sustituir');step.replacement=$('cleanReplacement').value}
 if(op==='null_markers')step.markers=($('cleanValue').value||'null;none;n/a;na;-;').split(';').map(x=>x.trim());
 if(op==='to_number')step.locale=$('cleanLocale').value;
 if(op==='to_date')step.format=$('cleanDateFormat').value;
 if(['to_number','to_date','to_boolean'].includes(op))step.on_error=$('cleanOnError').value;
 if(op==='keep_rows'){if(columns.length!==1)throw Error('Para conservar filas selecciona una sola columna');step.rule={op:$('cleanRuleOp').value,type:$('cleanRuleType').value,value:$('cleanRuleValue').value,value2:$('cleanRuleValue2').value}}
 C.steps.push(step);invalidatePreview();renderRecipe();toast('Paso añadido a la receta');
}
function previewMarkup(preview){
 const stats=[['Filas de origen',preview.before_rows],['Filas resultantes',preview.after_rows],['Celdas modificadas',preview.changed_cells],['Filas eliminadas',preview.removed_rows]];
 const diffs=preview.sample.flatMap(row=>row.status==='removed'?[`<tr><td>${row.row}</td><td>Fila eliminada</td><td class="diff-before">${e(JSON.stringify(row.before))}</td><td class="diff-after">—</td></tr>`]:row.columns.map(col=>`<tr><td>${row.row}</td><td>${e(col)}</td><td class="diff-before">${e(shortJson(row.before[col]??null))}</td><td class="diff-after">${e(shortJson(row.after[col]??null))}</td></tr>`)).join('');
 return `<div class="quality-summary">${stats.map(([name,value])=>`<div class="stat-chip">${name}<strong>${fmt(value,0)}</strong></div>`).join('')}</div>${preview.invalid_values?`<div class="notice conversion-warning"><b>${fmt(preview.invalid_values,0)} conversiones no válidas.</b> Se ha aplicado el tratamiento elegido en cada paso. Revisa estos ejemplos:<ul>${preview.issues.map(issue=>`<li>Paso ${issue.step}, fila ${issue.row}, ${e(issue.column)}: ${e(shortJson(issue.value))}</li>`).join('')}</ul></div>`:''}${preview.orphans.length?'<p class="quality-warning small">El modelo ya contiene claves sin correspondencia. Esta receta no aumenta su cantidad.</p>':''}<div class="table-scroll"><table class="diff-table"><thead><tr><th>Fila de origen</th><th>Columna</th><th>Antes</th><th>Después</th></tr></thead><tbody>${diffs||'<tr><td colspan="4">La receta no produce cambios.</td></tr>'}</tbody></table></div><details class="reference"><summary>Resultado de cada paso</summary><ul>${preview.steps.map(step=>`<li>${step.step}. ${e(cleanLabels[step.op])}: ${fmt(step.changed_cells,0)} celdas, ${fmt(step.removed_rows,0)} filas eliminadas, ${fmt(step.invalid_values,0)} conversiones no válidas</li>`).join('')}</ul></details>`;
}
async function previewClean(){
 C.busy=true;renderRecipe();$('applyClean').disabled=true;$('cleanPreview').textContent='Calculando la receta sobre toda la tabla…';
 const steps=JSON.stringify(C.steps),table=C.table;
 try{
  const preview=await post('/api/cleaning/preview',{table,steps:JSON.parse(steps)});
  if(steps!==JSON.stringify(C.steps)||table!==C.table)return;
  C.preview=preview;$('cleanPreview').innerHTML=previewMarkup(preview);$('applyClean').disabled=!(preview.changed_rows||preview.removed_rows);
 }catch(err){C.preview=null;$('cleanPreview').innerHTML=`<div class="viz-error">${e(err.message)}</div>`;toast(err.message,true)}finally{C.busy=false;renderRecipe()}
}
async function applyClean(){
 if(!C.preview||C.busy)return;
 // This is the review step for a real data mutation, including any row removals.
 if(!confirm(`Aplicar ${C.steps.length} pasos a ${C.table}: ${C.preview.changed_cells} celdas modificadas y ${C.preview.removed_rows} filas eliminadas. Se guardará una copia de seguridad. ¿Continuar?`))return;
 C.busy=true;renderRecipe();$('applyClean').disabled=true;
 try{
  await post('/api/cleaning/apply',{table:C.table,steps:C.steps,token:C.preview.token});await loadModel();
  C.preview=null;$('cleanPreview').innerHTML='<div class="notice">Limpieza aplicada y copia de seguridad guardada. Ya puedes revisar los datos y los informes actualizados.</div>';await renderCleaning();toast('Datos preparados. Puedes deshacer la limpieza.');
 }catch(err){invalidatePreview();toast(err.message,true)}finally{C.busy=false;renderRecipe()}
}

const baseBind=bind,baseSelectors=updateSelectors;
updateSelectors=function(){baseSelectors();if($('dataSort')){const names=F.model.tables.find(t=>t.name===F.dataTable)?.columns||[];const old=$('dataSort').value;opts($('dataSort'),[['','Orden de origen'],...names.map(c=>[c,c])],names.includes(old)?old:'')}};
bind=function(){
 baseBind();let saved='dark';try{saved=localStorage.getItem('abbi-theme')==='light'?'light':'dark'}catch{}setTheme(saved);
 $('themeToggle').onclick=()=>setTheme(document.documentElement.dataset.theme==='dark'?'light':'dark');
 $('filterOp').onchange=filterControls;$('filterType').onchange=filterControls;filterControls();
 $('filterDimension').onchange=()=>{F.filterSelection.clear();$('filterSearch').value='';$('filterCustom').value='';loadDistinct().catch(err=>toast(err.message,true))};
 let searchTimer;$('filterSearch').oninput=()=>{clearTimeout(searchTimer);searchTimer=setTimeout(()=>loadDistinct().catch(err=>toast(err.message,true)),220)};
 $('filterDeselect').onclick=()=>{F.filterSelection.clear();loadDistinct().catch(err=>toast(err.message,true))};
 $('applyFilter').onclick=()=>applyAdvancedFilter().catch(err=>toast(err.message,true));$('clearFilters').onclick=()=>commitFilters({}).catch(err=>toast(err.message,true));
 let tableTimer;$('dataSearch').oninput=()=>{clearTimeout(tableTimer);tableTimer=setTimeout(()=>{F.dataPage=0;renderData()},220)};
 for(const id of ['dataSort','dataSortType','dataSortDirection'])$(id).onchange=()=>{F.dataPage=0;renderData()};
 $('dataTableSelect').onchange=()=>{F.dataPage=0;$('dataSearch').value='';$('dataSort').value='';renderData()};
 $('editDataFilters').onclick=()=>{show('dashboard');$('filterDimension').focus()};$('goClean').onclick=()=>{C.table=F.dataTable;show('clean')};
 $('cleanTable').onchange=()=>{C.table=$('cleanTable').value;C.steps=[];invalidatePreview();cleanColumns();renderRecipe()};
 $('cleanAll').onclick=()=>$('cleanColumns').querySelectorAll('input').forEach(input=>input.checked=true);$('cleanNone').onclick=()=>$('cleanColumns').querySelectorAll('input').forEach(input=>input.checked=false);
 $('cleanOperation').onchange=cleanOptions;$('addCleanStep').onclick=()=>{try{addCleanStep()}catch(err){toast(err.message,true)}};
 $('previewClean').onclick=previewClean;$('applyClean').onclick=applyClean;
 $('clearRecipe').onclick=()=>{C.steps=[];invalidatePreview();renderRecipe()};
 $('exportRecipe').onclick=()=>downloadBlob(new Blob([JSON.stringify({format:'AB-BI Cleaning Recipe',version:1,table:C.table,steps:C.steps},null,2)],{type:'application/json'}),'AB_BI_receta.json');
 $('importRecipe').onclick=()=>$('recipeFile').click();$('recipeFile').onchange=async event=>{
  const file=event.target.files[0];if(!file)return;
  try{if(file.size>100000)throw Error('La receta supera 100 KB');const recipe=JSON.parse(await file.text());if(recipe.format!=='AB-BI Cleaning Recipe'||recipe.version!==1||!Array.isArray(recipe.steps)||!recipe.steps.length||recipe.steps.length>20||recipe.steps.some(step=>!cleanLabels[step.op]||!Array.isArray(step.columns)))throw Error('Formato de receta no válido');C.steps=recipe.steps;invalidatePreview();renderRecipe();toast('Receta cargada en la tabla seleccionada. Revisa la vista previa.')}catch(err){toast(err.message,true)}finally{event.target.value=''}
 };
 $('undoClean').onclick=async()=>{if(!confirm('¿Deshacer la última limpieza y recuperar su copia de seguridad?'))return;try{await post('/api/cleaning/undo',{});await loadModel();invalidatePreview();await renderCleaning();toast('Se ha recuperado el proyecto anterior')}catch(err){toast(err.message,true)}};
};
init();
