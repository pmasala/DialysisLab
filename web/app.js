'use strict';
const assetVersion=new URL(document.currentScript.src).search;
const $=id=>document.getElementById(id);
let ui,worker,running=false,ready=false,generation=0,lastState=null;
function download(content,name){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([content],{type:'application/json'}));a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);}
function disconnect(){if(ui)ui.ccall('browser_disconnected',null,[],[]);}
function fail(message){ready=running=false;$('run').disabled=true;$('error').textContent=message;$('status').textContent='Simulazione arrestata: creare una nuova sessione.';disconnect();if(worker)worker.terminate();}
function setRunning(value){running=value;worker.postMessage({type:'run',running,auto:$('auto').checked,speed:Number($('speed').value)});$('run').textContent=running?'Ferma tempo':'Riprendi tempo';}
function resize(){if(!ui)return;const width=Math.max(800,Math.min(1100,window.innerWidth));ui.ccall("browser_resize",null,["number"],[width]);$("canvas").style.width=width+"px";}
window.addEventListener("resize",resize);
async function reset(){
    const current=++generation;ready=running=false;lastState=null;$("patient").textContent="";if(worker)worker.terminate();disconnect();$('run').disabled=$('export').disabled=true;$('error').textContent='';$('status').textContent='Caricamento motore e paziente nel browser…';
    const config=await (await fetch('scenario.json'+assetVersion)).json();config.workflow=[];config.treatment.mode=$('mode').value;config.treatment.replacement_mL_min=$('mode').value==='HD'?0:60;
    const epoch=Array.from(crypto.getRandomValues(new Uint8Array(16)),x=>x.toString(16).padStart(2,'0')).join('');
    worker=new Worker('worker.js'+assetVersion);worker.onerror=e=>fail(e.message);
    worker.onmessage=({data})=>{
        if(current!==generation)return;
        if(data.type==='error')return fail(data.message);
        if(data.type==='ready'){ready=true;$('run').disabled=$('export').disabled=false;$('run').textContent='Avvia tempo';$('status').textContent='Pronto. Avvia il tempo; usa i comandi LVGL o il ciclo automatico.';}
        if(data.type==='running'){running=data.running;$('run').textContent=running?'Ferma tempo':'Riprendi tempo';}
        if(data.type==='state'){
            lastState=data;ui.ccall('browser_view',null,['string','string','string'],[data.epoch,...data.views]);
            $('status').textContent=`${data.stage} · ${data.ticks} passi · ${running?'tempo in avanzamento':'tempo fermo'} · allarmi ${data.alarm}`;
            if(data.patient){const residual=Math.max(...data.patient.mass_residual_mmol.map(Math.abs));$('patient').textContent=`Paziente accoppiato · residuo massimo soluti ${residual.toExponential(2)} mmol`;}
        }
        if(data.type==='result')ui.ccall('browser_result',null,['string'],[data.result]);
        if(data.type==='export')download(data.content,'DialysisLab-browser-state.json');
    };
    worker.postMessage({type:'init',config,epoch});
}
$('run').onclick=()=>setRunning(!running);
$('reset').onclick=()=>reset().catch(e=>fail(String(e)));
$('export').onclick=()=>worker.postMessage({type:'export'});
for(const id of ['speed','auto'])$(id).onchange=()=>{if(ready)setRunning(running);};
document.addEventListener('visibilitychange',()=>{if(document.hidden&&worker){setRunning(false);disconnect();}});
(async()=>{
    ui=await createUI({canvas:$('canvas'),onCommand:job=>{if(ready)worker.postMessage({type:'command',...job});},print:()=>{},printErr:message=>console.error(message),onAbort:message=>fail(String(message))});
    const identity=await (await fetch('build-identity.json'+assetVersion)).json();$('identity').textContent=`Build ${identity.source_revision.slice(0,12)} · ${identity.source_input_sha256.slice(0,16)} · Emscripten ${identity.emscripten} · Pyodide ${identity.pyodide}`;
    resize();await reset();
})().catch(e=>fail(String(e)));
// Read-only browser-test observation; no test-only actuator path.
window.dialysisBrowserStatus=()=>({ready,running,lastState,page:ui?ui.ccall('browser_page','number',[],[]):null});
