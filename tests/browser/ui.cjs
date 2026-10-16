/* Real Chromium UI, worker and Wasm acceptance. Run after build_browser.py. */
const {chromium}=require('playwright'),fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert');
(async()=>{
 const root=path.resolve('build/browser'),out=path.resolve(process.argv[2]);fs.mkdirSync(out,{recursive:false});
 const server=http.createServer((req,res)=>{const pathname=decodeURIComponent(new URL(req.url,'http://local').pathname);const target=path.resolve(root,'.'+(pathname==='/'?'/index.html':pathname));if(!target.startsWith(root+path.sep)){res.writeHead(403);return res.end();}fs.readFile(target,(err,bytes)=>{if(err){res.writeHead(404);return res.end();}res.setHeader('Content-Type',target.endsWith('.wasm')?'application/wasm':target.endsWith('.js')?'application/javascript':target.endsWith('.json')?'application/json':target.endsWith('.html')?'text/html':'application/octet-stream');res.end(bytes);});});
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const url='http://127.0.0.1:'+server.address().port;
 const report={passed:false,checks:[],browser:null,build:JSON.parse(fs.readFileSync(root+'/build-identity.json'))};let browser;
 try{
 browser=await chromium.launch({executablePath:process.env.DIALYSISLAB_CHROMIUM||undefined,headless:true,args:['--no-sandbox']});report.browser=await browser.version();
 const page=await browser.newPage({viewport:{width:1200,height:1150},hasTouch:true});const errors=[],requests=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>requests.push(r.url()));
 await page.goto(url);await page.waitForFunction(()=>window.dialysisBrowserStatus?.().ready,null,{timeout:60000});
 async function click(x,y,touch=false){const b=await page.locator('#canvas').boundingBox();if(touch)await page.touchscreen.tap(b.x+x,b.y+y);else await page.mouse.click(b.x+x,b.y+y,{delay:60});}
 for(const [x,tab] of [[330,1],[550,2],[100,0]]){await click(x,70,true);await page.waitForFunction(t=>dialysisBrowserStatus().page===t,tab);}
 report.checks.push('actual touch navigation before first sample');
 await page.check('#auto');await page.selectOption('#speed','100');await page.click('#run');
 await page.waitForFunction(()=>dialysisBrowserStatus().lastState?.stage==='TREATMENT',null,{timeout:120000});
 await page.click('#run');await page.uncheck('#auto');await page.selectOption('#speed','1');await page.click('#run');
 await page.waitForTimeout(600);const before=await page.evaluate(()=>dialysisBrowserStatus().lastState.ticks);await page.waitForTimeout(1100);const after=await page.evaluate(()=>dialysisBrowserStatus().lastState.ticks);assert(after-before>=1&&after-before<=3,'1x must advance about two 500ms ticks per second');
 report.checks.push('simulation time independent from frames, 1x pacing');
 await page.evaluate(()=>{Object.defineProperty(document,'hidden',{value:true,configurable:true});document.dispatchEvent(new Event('visibilitychange'));});
 await page.waitForFunction(()=>!dialysisBrowserStatus().running);await page.waitForTimeout(300);const held=await page.evaluate(()=>dialysisBrowserStatus().lastState.ticks);await page.waitForTimeout(800);assert.equal(await page.evaluate(()=>dialysisBrowserStatus().lastState.ticks),held);
 await page.evaluate(()=>{delete document.hidden;document.dispatchEvent(new Event('visibilitychange'));});assert.equal(await page.evaluate(()=>dialysisBrowserStatus().running),false);await page.click('#run');await page.waitForTimeout(600);report.checks.push('injected hidden-page event holds time and requires explicit resume');

 await click(1000,70);await page.waitForFunction(()=>dialysisBrowserStatus().page===4);
 await click(330,325);for(let i=0;i<12;i++)await page.keyboard.press('Backspace');await page.keyboard.type('250',{delay:40});
 await click(140,412);await click(280,458);await page.waitForFunction(()=>Number(dialysisBrowserStatus().lastState.views[0].split(' ')[8])===250,null,{timeout:10000});report.checks.push('LVGL prescription edited with keyboard, reviewed, confirmed and applied');
 await click(100,70);await page.screenshot({path:out+'/treatment.png',fullPage:true});
 await click(150,825);await click(280,458);
 await page.waitForFunction(()=>dialysisBrowserStatus().lastState.stage==='PAUSED',null,{timeout:10000});report.checks.push('LVGL Pause and Confirm reach production state machine');
 await click(150,825);await click(280,458);await page.waitForFunction(()=>dialysisBrowserStatus().lastState.stage==='TREATMENT',null,{timeout:10000});report.checks.push('LVGL resume and confirmation');
 await click(550,70,true);await page.waitForFunction(()=>dialysisBrowserStatus().page===2);await page.screenshot({path:out+'/hydraulics.png',fullPage:true});
 await click(100,70);await click(950,825);await page.waitForFunction(()=>dialysisBrowserStatus().lastState.stage==='STOPPED',null,{timeout:10000});report.checks.push('LVGL STOP applied without confirmation');
 await page.selectOption('#mode','HDF_POST');await page.click('#reset');await page.waitForFunction(()=>dialysisBrowserStatus().ready&&dialysisBrowserStatus().lastState.ticks===0);report.checks.push('new mode resets both models and epoch');
 await page.check('#auto');await page.selectOption('#speed','100');await page.click('#run');await page.waitForFunction(()=>dialysisBrowserStatus().lastState.stage==='TREATMENT',null,{timeout:120000});await page.screenshot({path:out+'/post.png',fullPage:true});
 await page.setViewportSize({width:800,height:1100});await page.waitForTimeout(300);await page.screenshot({path:out+'/narrow.png',fullPage:true});
 await page.waitForFunction(()=>dialysisBrowserStatus().lastState.stage==='CLEANED',null,{timeout:120000});report.checks.push('complete HDF POST cycle in browser');
 const downloadPromise=page.waitForEvent('download');await page.click('#export');const download=await downloadPromise;await download.saveAs(out+'/export.json');const exported=JSON.parse(fs.readFileSync(out+'/export.json'));assert(exported.record.patient.distributed);assert(exported.record.machine.stage==='CLEANED');report.checks.push('export contains real distributed patient and final state');
 assert(errors.length===0,JSON.stringify(errors));assert(requests.every(u=>u.startsWith(url+'/')),'all assets same-origin; no computation backend');report.checks.push('local static assets only; zero browser page errors');
 report.passed=true;report.network_requests=requests.length;
 }catch(e){report.error=String(e.stack||e);throw e;}finally{fs.writeFileSync(out+'/report.json',JSON.stringify(report,null,2));if(browser)await browser.close();await new Promise(r=>server.close(r));}
 console.log(JSON.stringify({passed:report.passed,checks:report.checks,browser:report.browser}));
})().catch(e=>{console.error(e);process.exit(1)});
