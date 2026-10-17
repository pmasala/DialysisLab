const fs=require('fs'),path=require('path');
(async()=>{
 const root=path.resolve(process.argv[2]),output=fs.openSync(process.argv[3],'wx');
 const e=await require(root+'/engine.js')();
 const py=await require(root+'/vendor/pyodide/pyodide.js').loadPyodide({indexURL:root+'/vendor/pyodide/'});
 py.FS.mkdirTree('/app/dialysislab');for(const [n,s] of Object.entries(JSON.parse(fs.readFileSync(root+'/python-sources.json'))))py.FS.writeFile('/app/dialysislab/'+n,s);
 py.globals.set('transport',e.cwrap('browser_rpc','string',['number','string']));
 py.globals.set('reset_engine',epoch=>e.ccall('browser_reset',null,['string'],[epoch]));
 py.globals.set('emit',value=>fs.writeSync(output,value+'\n'));
 py.globals.set('configuration',fs.readFileSync(root+'/scenario.json','utf8'));
 py.runPython("import sys,json\nsys.path.insert(0,'/app')");
 py.runPython(fs.readFileSync('tests/browser/campaign.py','utf8'));
 py.globals.set('manual_delay_ticks',Number(process.argv[4]||0));
 py.runPython('campaign(json.loads(configuration),transport,reset_engine,emit,manual_delay_ticks)');
 fs.closeSync(output);console.log('Wasm/Pyodide complete HD/PRE/POST campaign passed');
})().catch(e=>{console.error(String(e.stack||e));process.exit(1)});
