'use strict';
const fs=require('fs'),path=require('path'),R=process.env.Y3_BROWSER_RUN;
const checks={},required=JSON.parse(fs.readFileSync(path.join(R,'required-checks.json')));
let stage='start';
(async()=>{let browser;try{
 const {chromium}=require(path.join(R,'playwright-core'));
 const cfg=JSON.parse(fs.readFileSync(path.join(R,'input.json')));
 browser=await chromium.launch({executablePath:path.join(R,'browser-binaries/chrome'),
 headless:true,chromiumSandbox:true,args:['--no-proxy-server','--disable-background-networking']});
 async function device(){const context=await browser.newContext({ignoreHTTPSErrors:false});
 return {context,page:await context.newPage()};}
 const target=await device(),actor=await device(),p=target.page,a=actor.page;
 const tokens=[];let leaked=false;
 for(const page of [p,a])page.on('request',r=>{if(tokens.some(t=>r.url().includes(t)))leaked=true;});
 async function submit(page,endpoint){const response=page.waitForResponse(r=>r.url().endsWith(endpoint));
 await page.locator('#password-form button').click();return (await response).status();}
 async function login(page,id,password){await page.goto(cfg.origin+'/login');
 await page.locator('#identifier').fill(id);await page.locator('#password').fill(password);
 return await submit(page,'/auth/login');}
 async function get(page,route){return page.evaluate(async route=>{const r=await fetch('/api/v1'+route);
 return {status:r.status,body:await r.json()};},route);}
 async function post(page,route,body){return page.evaluate(async({route,body})=>{
 const csrf=await (await fetch('/api/v1/auth/csrf',{headers:{'X-Y3-Client':'browser'}})).json();
 const r=await fetch('/api/v1'+route,{method:'POST',headers:{'Content-Type':'application/json',
 'X-CSRF-Token':csrf.csrf_token},body:JSON.stringify(body)});
 return {status:r.status,body:r.status===204?null:await r.json()};},{route,body});}
 stage='target-login';checks.target_initial_password=await login(p,'master.test',cfg.masterPassword)===204;
 checks.trusted_https=await p.evaluate(()=>isSecureContext);
 const me=await get(p,'/auth/me'),ident=me.body.account_id;
 const issued=await post(p,'/admin/master-accounts',{login_id:'handoff.master'});
 if(issued.status!==201)throw Error();tokens.push(issued.body.setup_link.split('#token=')[1]);
 await a.goto(issued.body.setup_link);await a.locator('#password').fill(cfg.branchPassword);
 const setup=a.waitForResponse(r=>r.url().endsWith('/auth/credentials/complete'));
 await a.locator('#submit').click();checks.actor_password_setup=(await setup).status()===204;
 checks.actor_setup_no_auto_login=(await get(a,'/auth/me')).status===401;
 checks.actor_normal_password=await login(a,'handoff.master',cfg.branchPassword)===204;
 const actorCookie=(await actor.context.cookies()).find(c=>c.name==='__Host-y3-auth').value;
 stage='operator';fs.writeFileSync(path.join(R,'emergency-issue-ready-0'),'ready',{mode:0o600});
 const deadline=Date.now()+70000;
 while(!fs.existsSync(path.join(R,'emergency-issued-ready-0'))&&Date.now()<deadline)
 await new Promise(r=>setTimeout(r,100));
 if(!fs.existsSync(path.join(R,'emergency-issued-ready-0')))throw Error();
 const route='/admin/master-accounts/'+ident+'/emergency-recovery';
 stage='handoff';const parent=await get(a,route);checks.expired_case_status=parent.status===200&&parent.body.status==='expired';
 async function reissue(current){return await post(a,route+'/handoff',{
 operation_id:await a.evaluate(()=>crypto.randomUUID()),supersedes_case_id:current.body.operation_id,
 expected:current.body.snapshot,identity_confirmed:true});}
 const first=await reissue(parent);checks.authenticated_takeover=first.status===201;
 tokens.push(first.body.recipient_link.split('#token=')[1]);
 const child=await get(a,route),second=await reissue(child);checks.explicit_live_reissue=second.status===201;
 const status=await get(a,route+'/'+first.body.operation_id);
 checks.superseded_status_no_token=status.body.status==='superseded'&&!JSON.stringify(status.body).includes('token');
 const oldRaw=first.body.recipient_link.split('#token=')[1],raw=second.body.recipient_link.split('#token=')[1];
 tokens.push(raw);
 checks.superseded_source_denied=(await post(p,'/auth/emergency-recovery/password/complete',{emergency_token:oldRaw,new_password:cfg.branchPassword})).status===401;
 stage='recipient';await p.goto(second.body.recipient_link);
 checks.fragment_removed=await p.evaluate(()=>location.hash==='');
 checks.target_revoked=(await get(p,'/auth/me')).status===401;
 await p.locator('#password').fill(cfg.branchPassword+' restored');
 checks.password_completion=await submit(p,'/auth/emergency-recovery/password/complete')===204;
 checks.no_auto_login=(await get(p,'/auth/me')).status===401;
 checks.normal_relogin=await login(p,'master.test',cfg.branchPassword+' restored')===204;
 checks.completed_status=(await get(a,route)).body.status==='completed';
 checks.actor_preserved=(await get(a,'/auth/me')).status===200&&(await actor.context.cookies()).find(c=>c.name==='__Host-y3-auth').value===actorCookie;
 checks.no_token_request_url=!leaked;
 fs.writeFileSync(path.join(R,'browser-results.json'),JSON.stringify({checks,browser:browser.version()}));
 if(Object.keys(checks).length!==required.length||!required.every(k=>checks[k]===true))throw Error();
 }catch{process.stderr.write('HANDOFF_BROWSER_FAILED stage='+stage+'\n');
 process.stderr.write('HANDOFF_DIAGNOSTIC='+JSON.stringify(checks)+'\n');process.exitCode=1;}
 finally{if(browser)await browser.close();}})();
