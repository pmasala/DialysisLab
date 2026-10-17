/* One worker owns one coupled simulation. No remote computation or sockets. */
importScripts('engine.js', 'vendor/pyodide/pyodide.js');
let engine, python, session, epoch, running=false, timer=null, auto=false, speed=20, failed=false,dt=500;
function emit(type, data={}) { postMessage({type,...data}); }
function status() {
    const value=JSON.parse(python.runPython(`json.dumps(dict(views=session.views(), ticks=session.n, stage=session.record['machine']['stage'] if session.record else 'SELF_TEST', patient=session.snapshot, alarm=session.record['machine']['alarm_mask'] if session.record else 0), allow_nan=False)`));
    emit('state',{epoch,...value});
}
function batchSize(){return Math.max(1,Math.floor(speed*100/dt));}
function schedule() {clearTimeout(timer);if(running&&!failed)timer=setTimeout(tick,batchSize()*dt/speed);}
function tick() {
    try {
        const count=batchSize();
        for(let i=0;i<count&&running;i++) {
            if(auto)python.runPython(`
if session.record:
    action={'PREPARATION':'PRIME','CONFIGURATION':'CONNECT','CONNECTED':'START','FINISHED':'RETURN','DISCONNECTING':'DISCONNECT','DISCONNECTED':'CLEAN'}.get(session.record['machine']['stage'])
    if action: session.command(0,action,session.epoch)
`);
            const record=session.step();const m=record.get('machine');const stage=m.get('stage');m.destroy();record.destroy();
            if(stage==='CLEANED'||stage==='STOPPED')running=false;
        }
        status();emit('running',{running});schedule();
    }catch(error){fatal(error);}
}
function fatal(error) {failed=true;running=false;clearTimeout(timer);emit('error',{message:String(error.stack||error)});}
onmessage=async ({data})=>{
    try {
        if(data.type==='init'){
            epoch=data.epoch;dt=data.config.dt_ms;
            [engine,python]=await Promise.all([createEngine(),loadPyodide({indexURL:'vendor/pyodide/'})]);
            engine.ccall('browser_reset',null,['string'],[epoch]);
            const files=await (await fetch('python-sources.json'+self.location.search)).json();python.FS.mkdirTree('/app/dialysislab');
            for(const [name,source] of Object.entries(files))python.FS.writeFile('/app/dialysislab/'+name,source);
            python.globals.set('transport',engine.cwrap('browser_rpc','string',['number','string']));
            python.globals.set('configuration',JSON.stringify(data.config));python.globals.set('epoch',epoch);
            python.runPython("import sys,json\nsys.path.insert(0,'/app')\nfrom dialysislab.browser import BrowserSession\nsession=BrowserSession(json.loads(configuration),transport,epoch,interactive=True)");
            session=python.globals.get('session');emit('ready');status();
        }else if(data.type==='run'){if(failed)throw Error('Reset required');running=data.running;auto=!!data.auto;speed=data.speed||20;schedule();emit('running',{running});}
        else if(data.type==='command'){
            const result=session.command(data.role,data.action,data.epoch,data.values||'');emit('result',{result});status();
        }else if(data.type==='export'){emit('export',{content:session.export()});}
    }catch(error){fatal(error);}
};
