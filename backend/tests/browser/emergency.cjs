'use strict';
const fs=require('fs'),path=require('path'),R=process.env.Y3_BROWSER_RUN;
const checks={},required=JSON.parse(fs.readFileSync(path.join(R,'required-checks.json')));
let stage='start';
(async()=>{let browser,context,anonymous;try{
 const {chromium}=require(path.join(R,'playwright-core'));
 const cfg=JSON.parse(fs.readFileSync(path.join(R,'input.json')));
 browser=await chromium.launch({executablePath:path.join(R,'browser-binaries/chrome'),
 headless:true,chromiumSandbox:true,args:['--no-proxy-server','--disable-background-networking']});
 context=await browser.newContext({ignoreHTTPSErrors:false});const p=await context.newPage();
 const tokens=[];let leaked=false;
 const watch=r=>{if(tokens.some(t=>r.url().includes(t)))leaked=true;};
 context.on('request',watch);
 async function post(route,body,page=p){return page.evaluate(async({route,body})=>{
 const c=await(await fetch('/api/v1/auth/csrf',{headers:{'X-Y3-Client':'browser'}})).json();
 const r=await fetch('/api/v1'+route,{method:'POST',headers:{'Content-Type':'application/json',
 'X-CSRF-Token':c.csrf_token},body:JSON.stringify(body)});return r.status;},{route,body});}
 async function login(password){await p.goto(cfg.origin+'/login');
 await p.locator('#identifier').fill('master.test');await p.locator('#password').fill(password);
 const response=p.waitForResponse(r=>r.url().endsWith('/auth/login'));
 await p.locator('#password-form button').click();return (await response).status()===204;}
 async function me(){return p.evaluate(async()=> (await fetch('/api/v1/auth/me')).status);}
 stage='login';checks.actual_initial_password_login=await login(cfg.masterPassword);
 checks.trusted_secure_context=await p.evaluate(()=>isSecureContext);
 const old=(await context.cookies()).find(c=>c.name==='__Host-y3-auth')?.value;
 if(!old)throw Error();
 fs.writeFileSync(path.join(R,'emergency-issue-ready-0'),'ready',{mode:0o600});
 stage='operator';const deadline=Date.now()+70000;
 while(!fs.existsSync(path.join(R,'emergency-issued-ready-0'))&&Date.now()<deadline)
 await new Promise(r=>setTimeout(r,100));
 if(!fs.existsSync(path.join(R,'emergency-issued-ready-0')))throw Error();
 const link=fs.readFileSync(path.join(R,'emergency-delivery-0'),'utf8').trim();
 const raw=link.split('#token=')[1];tokens.push(raw);
 stage='recipient';await p.goto(link);
 checks.fragment_removed=await p.evaluate(()=>location.hash==='');
 checks.password_target_session_revoked=(await me())===401;
 checks.password_stale_cookie_retained=(await context.cookies()).find(c=>c.name==='__Host-y3-auth')?.value===old;
 checks.recipient_inspect=(await post('/auth/emergency-recovery/inspect',{emergency_token:raw}))===200;
 const currentPassword=cfg.branchPassword+' emergency';await p.locator('#password').fill(currentPassword);
 const completed=p.waitForResponse(r=>r.url().endsWith('/auth/emergency-recovery/password/complete'));
 await p.locator('#password-form button').click();
 checks.password_completion_form=(await completed).status()===204;
 checks.password_completion_no_auto_login=(await me())===401&&!(await context.cookies()).some(c=>c.name==='__Host-y3-auth');
 checks.old_password_denied=(await post('/auth/login',{login_id:'master.test',password:cfg.masterPassword}))===401;
 checks.password_actual_relogin=await login(currentPassword)&&(await me())===200;
 const cookie=(await context.cookies()).find(c=>c.name==='__Host-y3-auth');
 checks.cookie_flags=!!cookie&&cookie.value!==old&&cookie.secure&&cookie.httpOnly&&cookie.sameSite==='Lax'&&cookie.path==='/'&&cookie.domain==='localhost';
 checks.cookie_js_hidden=await p.evaluate(()=>!document.cookie.includes('__Host-y3'));
 checks.signed_in_replay_requires_logout=(await post('/auth/emergency-recovery/password/complete',{emergency_token:raw,new_password:currentPassword}))===409;
 checks.replay_preserves_session=(await me())===200&&(await context.cookies()).find(c=>c.name==='__Host-y3-auth')?.value===cookie?.value;
 anonymous=await browser.newContext({ignoreHTTPSErrors:false});anonymous.on('request',watch);
 const recipient=await anonymous.newPage();await recipient.goto(cfg.origin+'/login');
 checks.replay_denied=(await post('/auth/emergency-recovery/password/complete',{emergency_token:raw,new_password:currentPassword},recipient))===401;
 checks.replay_preserves_session=checks.replay_preserves_session&&(await me())===200&&(await context.cookies()).find(c=>c.name==='__Host-y3-auth')?.value===cookie?.value;
 checks.no_token_request_url=!leaked;
 fs.writeFileSync(path.join(R,'browser-results.json'),JSON.stringify({checks,browser:browser.version()}));
 if(Object.keys(checks).length!==required.length||!required.every(k=>checks[k]===true))throw Error();
 }catch{process.stderr.write('EMERGENCY_BROWSER_FAILED stage='+stage+'\n');
 process.stderr.write('EMERGENCY_DIAGNOSTIC='+JSON.stringify(checks)+'\n');process.exitCode=1;}
 finally{try{if(anonymous)await anonymous.close();}finally{try{if(context)await context.close();}finally{if(browser)await browser.close();}}}})();
