'use strict';
const fs=require('fs'),path=require('path'),R=process.env.Y3_BROWSER_RUN;
const checks={},required=JSON.parse(fs.readFileSync(path.join(R,'required-checks.json')));
let stage='start';const releaseGates=[];
const networkEvidence={csrf_fetch_complete:false,csrf_status:null,csrf_delivery:'browser_fetch_promise',csrf_return_complete:false,endpoints:{me:{requests:0,statuses:[],failed:0},
 csrf:{requests:0,statuses:[],failed:0},role_change:{requests:0,statuses:[],failed:0}},
 pageerrors:[],message:'other'};
let evidencePage=null;
function safeError(error){
 const allowed=['Error','TypeError','ReferenceError','SyntaxError','RangeError','TimeoutError'];
 const name=allowed.includes(error?.name)?error.name:'Error';
 const locations=[...(String(error?.stack||'').matchAll(/\/(?:browser|trainer)\.cjs:(\d+):(\d+)/g))]
  .map(match=>({line:Number(match[1]),column:Number(match[2])}));
 return {name,locations};
}
(async()=>{let browser;try{
const {chromium}=require(path.join(R,'playwright-core'));
const cfg=JSON.parse(fs.readFileSync(path.join(R,'input.json')));
browser=await chromium.launch({executablePath:path.join(R,'browser-binaries/chrome'),
headless:true,chromiumSandbox:true,args:['--no-proxy-server','--disable-background-networking']});
const admin=await browser.newContext({ignoreHTTPSErrors:false}),p=await admin.newPage();
async function click(page,selector,path){const result=page.waitForResponse(r=>r.url().endsWith(path)&&r.request().method()==='POST');
await page.locator(selector).click();return await result;}
async function get(page,route){return page.evaluate(async route=>{const headers={};
if(route.startsWith('/admin/operator-role'))headers['X-Y3-Expected-Actor']=(await(await fetch('/api/v1/auth/me')).json()).account_id;
const r=await fetch('/api/v1'+route,{headers});
return {status:r.status,body:await r.json()};},route);}
async function post(page,route,body){return page.evaluate(async({route,body})=>{
const c=await(await fetch('/api/v1/auth/csrf',{headers:{'X-Y3-Client':'browser'}})).json();
const headers={'Content-Type':'application/json','X-CSRF-Token':c.csrf_token};
if(route.startsWith('/admin/operator-role'))headers['X-Y3-Expected-Actor']=(await(await fetch('/api/v1/auth/me')).json()).account_id;
const r=await fetch('/api/v1'+route,{method:'POST',headers,body:JSON.stringify(body)});
return {status:r.status,body:r.status===204?null:await r.json()};},{route,body});}
stage='admin';await p.goto(cfg.origin+'/login');
checks.trusted_https=await p.evaluate(()=>isSecureContext);
await p.goto(cfg.origin+'/login');await p.locator('#identifier').fill('master.test');
await p.locator('#password').fill(cfg.masterPassword);
checks.master_password_login=(await click(p,'#password-form button','/auth/login')).status()===204;
const branch=await post(p,'/admin/branches',{code:'I1',name:'가상지점'});
if(branch.status!==201)throw Error();
stage='registration';await p.goto(cfg.origin+'/trainers');
await p.waitForFunction(()=>!document.getElementById('submit').disabled);
for(const [id,value] of Object.entries({name:'가상트레이너',phone:'+99 example',rate_percent:'0',
fixed_amount_won:'0',base_salary_won:'0',base_salary_start_month:'2026-10'}))await p.locator('#'+id).fill(value);
await p.locator('#home_branch_id').selectOption(branch.body.id);
const created=await click(p,'#submit','/api/v1/admin/trainers'),trainer=(await created.json()).trainer;
checks.w0_actual_form=created.status()===201;
const box=p.locator('[data-trainer="'+trainer.id+'"]');
await box.locator('input').fill('trainer.native');
const issued=await click(p,'[data-trainer] form button','/login-account');
const issueData=await issued.json();checks.issue_actual_form=issued.status()===201;
await box.locator('a').waitFor();
checks.one_time_link=await box.locator('a').getAttribute('href')===issueData.setup_link;
await box.getByText('계정 상태 확인',{exact:true}).click();
await box.locator('a').waitFor({state:'detached'});checks.status_no_link=await box.locator('a').count()===0;
const reissued=await click(p,'[data-trainer] button:text-is("초기 설정 링크 재발급")','/initial-setup');
checks.explicit_reissue=reissued.status()===201;const setup=(await reissued.json()).setup_link;
stage='setup';const recipient=await browser.newContext({ignoreHTTPSErrors:false});
const r=await recipient.newPage();await r.goto(setup);
await r.waitForFunction(()=>!location.hash);checks.fragment_cleared=!r.url().includes('#');
await r.locator('#new-password').fill(cfg.branchPassword);
checks.setup_actual_form=(await click(r,'#trainer-setup button','/trainer-credentials/complete')).status()===204;
stage='login';async function login(password){await r.goto(cfg.origin+'/login');
await r.locator('#identifier').fill('trainer.native');await r.locator('#password').fill(password);
const response=await click(r,'#password-form button','/auth/login');
await r.waitForURL('**/account');return response.status();}
checks.password_login=await login(cfg.branchPassword)===204;
const me=await get(r,'/auth/me');checks.trainer_self=me.status===200&&me.body.roles.some(x=>x.role==='TRAINER'&&x.trainer_id===trainer.id)&&me.body.capabilities.length===0;
checks.no_admin=(await get(r,'/branches')).status===401;
const cookies=await recipient.cookies();checks.secure_cookie=cookies.some(c=>c.name.startsWith('__Host-')&&c.httpOnly&&c.secure);
checks.csrf_denied=await r.evaluate(async()=>{const x=await fetch('/api/v1/auth/password',
{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({current_password:'synthetic',new_password:'synthetic'})});return x.status===403;});
const next=cfg.branchPassword+' changed';await r.locator('#current-password').fill(cfg.branchPassword);
await r.locator('#new-password').fill(next);
checks.self_change=(await click(r,'#self-password button','/auth/password')).status()===204;
await r.waitForURL('**/login');checks.old_session_revoked=(await get(r,'/auth/me')).status===401;
checks.new_password_login=await login(next)===204;
checks.logout=(await click(r,'#signout','/auth/logout')).status()===204;
await r.waitForURL('**/login');checks.logged_out=(await get(r,'/auth/me')).status===401;
checks.admin_preserved=(await get(p,'/auth/me')).status===200;
stage='nojs';const off=await browser.newContext({javaScriptEnabled:false,ignoreHTTPSErrors:false});
const n=await off.newPage();await n.goto(setup);checks.nojs_disabled=await n.locator('form button').isDisabled();
checks.nojs_post=await n.locator('form').getAttribute('method')==='post';
stage='operator';
await p.goto(cfg.origin+'/operator-accounts');
await p.locator('#login').fill('operator.native');
await p.locator('#branch').selectOption(branch.body.id);
const operatorIssue=await click(p,'button[value=issue]','/admin/operator-accounts');
const operator=(await operatorIssue.json());
checks.operator_issue=operatorIssue.status()===201;
const opPath='/admin/operator-accounts/'+operator.account_id+'/initial-setup';
await click(p,'button[value=lookup]','/operator-accounts/lookup');
await p.locator('#delivery a').waitFor({state:'detached'});
checks.operator_clear=await p.locator('#delivery a').count()===0;
// Reject an obsolete write and discard an out-of-order read.
await post(p,opPath,{expected_version:operator.version,expected_operator_version:operator.operator_scope.version});
const conflict=await click(p,'button[value=reissue]',opPath);
await p.getByText(/현재 상태입니다/).waitFor();
checks.operator_conflict=conflict.status()===409&&await p.locator('#delivery a').count()===0;
let unblock,entered;
const blocked=new Promise(resolve=>{unblock=resolve;});
const reached=new Promise(resolve=>{entered=resolve;});
await p.route('**/operator-accounts/lookup',async route=>{
 const res=await route.fetch();entered();await blocked;await route.fulfill({response:res});
});
await p.locator('button[value=lookup]').click();await reached;
await p.locator('#login').fill('different.operator');
const done=p.waitForResponse(r=>r.url().endsWith('/operator-accounts/lookup'));unblock();
await done;await p.unroute('**/operator-accounts/lookup');
checks.operator_stale_read=await p.locator('button[value=reissue]').isDisabled();
await p.locator('#login').fill('operator.native');
await click(p,'button[value=lookup]','/operator-accounts/lookup');
// A committed response can be lost. Reconcile by UUID and explicitly reissue.
let sends=0;
await p.route('**'+opPath,async route=>{
 sends++;await route.fetch();await route.abort();
});
await p.locator('button[value=reissue]').dblclick();
await p.getByText(/현재 상태입니다/).waitFor();
checks.operator_lost_ack=sends===1&&await p.locator('#delivery a').count()===0;
await p.unroute('**'+opPath);
const fresh=await click(p,'button[value=reissue]',opPath);
const url=(await fresh.json()).setup_link;
await r.goto(operator.setup_link);await r.locator('#new-password').fill(cfg.branchPassword);
checks.operator_old_denied=(await click(r,'form button','/operator-credentials/complete')).status()===400;
await r.goto(url);await r.waitForFunction(()=>!location.hash);
await r.locator('#new-password').fill(cfg.branchPassword);
checks.operator_complete=(await click(r,'form button','/operator-credentials/complete')).status()===204;
async function operatorLogin(password){
 await r.goto(cfg.origin+'/login');await r.locator('#identifier').fill('operator.native');
 await r.locator('#password').fill(password);await click(r,'#password-form button','/auth/login');
 await r.waitForURL('**/account');await r.getByText(/업무 지점 I1/).waitFor();
}
await operatorLogin(cfg.branchPassword);
checks.operator_branch=(await get(r,'/operator/branches/'+branch.body.id)).status===200;
checks.operator_denied=(await get(r,'/branches')).status===403;
await r.locator('#current-password').fill(cfg.branchPassword);await r.locator('#new-password').fill(next);
checks.operator_password=(await click(r,'#self-password button','/auth/password')).status()===204;
await r.waitForURL('**/login');await operatorLogin(next);
checks.operator_logout=(await click(r,'#signout','/auth/logout')).status()===204;
stage='operator-management';
await p.goto(cfg.origin+'/operator-roles');
await p.waitForFunction(()=>!document.getElementById('role-find').disabled);
await p.locator('#role-login').fill('operator.native');
await click(p,'#role-find','/operator-roles/lookup');
await p.waitForFunction(()=>!document.getElementById('role-revoke').disabled);
checks.role_lookup=await p.locator('#role-current').textContent().then(x=>x.includes('operator.native'));
const rolePath='/admin/operator-roles/'+operator.account_id+'/changes';
let roleSends=0;
await p.route('**'+rolePath,async route=>{roleSends++;await route.fetch();await route.abort();});
await p.locator('#role-revoke').dblclick();
await p.getByText(/응답이 확인되지/).waitFor();
checks.role_lost_ack=roleSends===1&&await p.locator('#role-current').textContent()==='';
await p.unroute('**'+rolePath);
await p.locator('#role-reconcile').click();await p.getByText(/확정 요청 버전/).waitFor();
checks.role_receipt_current=await p.locator('#role-current').textContent().then(x=>x.includes('없음'));
checks.role_regrant=(await click(p,'#role-grant',rolePath)).status()===200;
await p.waitForFunction(()=>!document.getElementById('role-revoke').disabled);
const roleCurrent=(await get(p,'/admin/operator-roles/'+operator.account_id)).body;
await post(p,rolePath,{operation_id:require('crypto').randomUUID(),
 expected_account_version:roleCurrent.account_version,
 expected_operator_version:roleCurrent.operator_grant.scope.version,
 branch_id:roleCurrent.branch_id,desired_granted:false});
checks.role_conflict=(await click(p,'#role-revoke',rolePath)).status()===409;
await p.getByText(/충돌했습니다/).waitFor();
checks.role_conflict_clear=await p.locator('#role-current').textContent()==='';
await click(p,'#role-find','/operator-roles/lookup');
await click(p,'#role-grant',rolePath);

await p.waitForFunction(()=>!document.getElementById('role-move').disabled);
const destination=await post(p,'/admin/branches',{code:'I17',name:'이동 지점'});
await p.reload();await p.waitForFunction(()=>!document.getElementById('role-find').disabled);
await p.locator('#role-login').fill('operator.native');
await click(p,'#role-find','/operator-roles/lookup');
await p.locator('#role-destination').selectOption(destination.body.id);
checks.role_move=(await click(p,'#role-move','/operator-roles/'+operator.account_id+'/branch')).status()===200;
await p.waitForFunction(()=>!document.getElementById('role-find').disabled);
// A delayed lookup cannot restore a target discarded by a new input generation.
let unblockRole;const roleGate=new Promise(resolve=>unblockRole=resolve);
await p.route('**/operator-roles/lookup',async route=>{const result=await route.fetch();
 await roleGate;await route.fulfill({response:result});});
await p.locator('#role-find').click();
await p.locator('#role-login').fill('different.target');
const lateRole=p.waitForResponse(response=>response.url().endsWith('/operator-roles/lookup'));
unblockRole();await lateRole;await p.unroute('**/operator-roles/lookup');
checks.role_stale_read=await p.locator('#role-grant').isDisabled()&&
 await p.locator('#role-current').textContent()==='';
await p.locator('#role-login').fill('master.test');
await click(p,'#role-find','/operator-roles/lookup');
const masterId=(await get(p,'/auth/me')).body.account_id;
checks.role_self=(await click(p,'#role-grant','/operator-roles/'+masterId+'/changes')).status()===200;
await p.getByText(/본인 변경이 저장/).waitFor();
checks.role_self_revoked=(await get(p,'/auth/me')).status===401;
await p.goto(cfg.origin+'/login');await p.locator('#identifier').fill('master.test');
await p.locator('#password').fill(cfg.masterPassword);
await click(p,'#password-form button','/auth/login');
await p.locator('#operator-link').waitFor();
checks.role_admin_landing=p.url().endsWith('/login')&&
 (await get(p,'/branches')).status===200;
await p.goto(cfg.origin+'/operator-roles');
await p.waitForFunction(()=>!document.getElementById('role-reconcile').disabled);
await p.locator('#role-reconcile').click();await p.getByText(/확정 요청 버전/).waitFor();
checks.role_self_receipt=await p.locator('#role-current').textContent().then(x=>x.includes('master.test'));
stage='operator-actor-switch';
const secondMaster=await post(p,'/admin/master-accounts',{login_id:'operator.manager.b'});
if(secondMaster.status!==201)throw Error();
const setupContext=await browser.newContext({ignoreHTTPSErrors:false});
const setupPage=await setupContext.newPage();await setupPage.goto(cfg.origin+'/login');
const setupToken=secondMaster.body.setup_link.split('#token=')[1];
if((await post(setupPage,'/auth/credentials/complete',
 {setup_token:setupToken,new_password:cfg.branchPassword})).status!==204)throw Error();
await setupContext.close();
const oldPending=await p.evaluate(()=>JSON.parse(sessionStorage.getItem('y3-operator-operation')));
const otherTab=await admin.newPage();
async function switchActor(name,password,label){
 stage=label+'-navigate';await otherTab.goto(cfg.origin+'/login');
 stage=label+'-current';if((await get(otherTab,'/auth/me')).status===200){
  stage=label+'-logout';if((await post(otherTab,'/auth/logout',{})).status!==204)throw Error();
 }
 stage=label+'-reload';await otherTab.reload();await otherTab.locator('#identifier').fill(name);
 await otherTab.locator('#password').fill(password);
 stage=label+'-login';if((await click(otherTab,'#password-form button','/auth/login')).status()!==204)throw Error();
 stage=label+'-landing';await otherTab.locator('#operator-link').waitFor();
}
async function selectOperator(label){
 stage=label+'-navigate';await p.goto(cfg.origin+'/operator-roles');
 stage=label+'-ready';await p.waitForFunction(()=>!document.getElementById('role-find').disabled);
 await p.locator('#role-login').fill('operator.native');
 stage=label+'-lookup';await click(p,'#role-find','/operator-roles/lookup');
 stage=label+'-selected';await p.waitForFunction(()=>!document.getElementById('role-revoke').disabled);
}
await selectOperator('actor-a-initial-query');
let switchedSends=0;
await p.route('**'+rolePath,async route=>{switchedSends++;await route.continue();});
await switchActor('operator.manager.b',cfg.branchPassword,'actor-b-first-switch');
await p.locator('#role-revoke').click();
await p.getByText(/로그인 계정이 바뀌었습니다/).waitFor();
checks.role_actor_switch=switchedSends===0&&await p.locator('#role-current').textContent()===''&&
 await p.locator('#role-reconcile').isDisabled();
await p.unroute('**'+rolePath);
stage='actor-old-receipt';checks.role_other_actor_receipt=(await get(otherTab,
 '/admin/operator-role-operations/'+oldPending.operation)).status===404;
await switchActor('master.test',cfg.masterPassword,'actor-a-return');
await selectOperator('actor-a-return-query');
evidencePage=p;
function endpoint(request){
 const value=request.url();
 if(value.endsWith('/auth/me'))return 'me';
 if(value.endsWith('/auth/csrf'))return 'csrf';
 if(value.endsWith(rolePath)&&request.method()==='POST')return 'role_change';
 return null;
}
p.on('request',request=>{const key=endpoint(request);if(key)networkEvidence.endpoints[key].requests++;});
p.on('response',response=>{const key=endpoint(response.request());
 if(key)networkEvidence.endpoints[key].statuses.push(response.status());});
p.on('requestfailed',request=>{const key=endpoint(request);if(key)networkEvidence.endpoints[key].failed++;});
p.on('pageerror',error=>networkEvidence.pageerrors.push(safeError(error)));
// Hold one original browser CSRF Response; do not replay its GET through APIRequestContext.
await p.evaluate(()=>{
 const original=window.fetch;
 let release;
 const gate=new Promise(resolve=>release=resolve);
 const state={arrived:false,status:null,returned:false,used:false,
  restore(){window.fetch=original;release();}};
 window.__y3RoleCsrfGate=state;
 window.fetch=async function(...args){
  if(!state.used&&args[0]==='/api/v1/auth/csrf'){
   state.used=true;
   const response=await original.apply(window,args);
   state.status=response.status;state.arrived=true;
   await gate;state.returned=true;return response;
  }
  return original.apply(window,args);
 };
});
releaseGates.push(async()=>{if(!p.isClosed())await p.evaluate(()=>{
 window.__y3RoleCsrfGate?.restore();delete window.__y3RoleCsrfGate;
});});
stage='actor-csrf-reach';await p.locator('#role-revoke').click();
await p.waitForFunction(()=>window.__y3RoleCsrfGate?.arrived);
networkEvidence.csrf_fetch_complete=true;
networkEvidence.csrf_status=await p.evaluate(()=>window.__y3RoleCsrfGate.status);
stage='actor-csrf-200-precondition';
if(networkEvidence.csrf_status!==200)throw Error();
await switchActor('operator.manager.b',cfg.branchPassword,'actor-b-race-switch');
const actorBlocked=p.waitForResponse(response=>response.url().endsWith(rolePath));
stage='actor-csrf-release';await p.evaluate(()=>window.__y3RoleCsrfGate.restore());
await p.waitForFunction(()=>window.__y3RoleCsrfGate.returned);
networkEvidence.csrf_return_complete=true;stage='actor-actual-response';
const blockedResponse=await actorBlocked;
stage='actor-ui-message';await p.getByText(/로그인 계정이 바뀌었습니다/).waitFor();
stage='actor-actual-409';checks.role_actor_send_race=blockedResponse.status()===409&&
 blockedResponse.request().headers()['x-y3-expected-actor']===masterId&&
 (await get(otherTab,'/admin/operator-roles/'+operator.account_id)).body.operator_grant.granted;
// Pending A receipt must not be queried from B's authenticated context.
await switchActor('master.test',cfg.masterPassword,'actor-a-pending-return');
await p.evaluate(value=>sessionStorage.setItem('y3-operator-operation',JSON.stringify(value)),oldPending);
stage='actor-pending-restore';await p.reload();
await p.waitForFunction(()=>!document.getElementById('role-reconcile').disabled);
await switchActor('operator.manager.b',cfg.branchPassword,'actor-b-pending-switch');
let receiptReads=0;
await p.route('**/operator-role-operations/*',async route=>{receiptReads++;await route.continue();});
stage='actor-pending-click';await p.locator('#role-reconcile').click();
stage='actor-pending-message';await p.getByText(/로그인 계정이 바뀌었습니다/).waitFor();
checks.role_actor_pending=receiptReads===0&&await p.locator('#role-reconcile').isDisabled();
await p.unroute('**/operator-role-operations/*');
await switchActor('master.test',cfg.masterPassword,'actor-a-late-return');await selectOperator('actor-a-late-query');
let releaseLookup,lookupReached;
const lookupGate=new Promise(resolve=>releaseLookup=resolve);releaseGates.push(()=>releaseLookup());
const lookupReady=new Promise(resolve=>lookupReached=resolve);
await p.route('**/operator-roles/lookup',async route=>{const response=await route.fetch();
 lookupReached();await lookupGate;await route.fulfill({response});});
stage='actor-late-read-reach';await p.locator('#role-find').click();await lookupReady;
await switchActor('operator.manager.b',cfg.branchPassword,'actor-b-late-switch');stage='actor-late-read-release';releaseLookup();
await p.getByText(/로그인 계정이 바뀌었습니다/).waitFor();
checks.role_actor_late_read=await p.locator('#role-current').textContent()===''&&
 await p.locator('#role-grant').isDisabled();
await p.unroute('**/operator-roles/lookup');await otherTab.close();
if(Object.keys(checks).length!==required.length||!required.every(k=>checks[k]===true))throw Error();
process.stderr.write('TRAINER_NETWORK_EVIDENCE='+JSON.stringify(networkEvidence)+'\n');
fs.writeFileSync(path.join(R,'browser-results.json'),JSON.stringify({checks,browser:browser.version()}));
}catch(error){
if(evidencePage){try{networkEvidence.message=await evidencePage.evaluate(()=>{
 const value=document.getElementById('role-message')?.textContent||'';
 if(value==='처리 중')return 'working';
 if(value.includes('로그인 계정이 바뀌었습니다'))return 'actor_changed';
 if(value.includes('충돌했습니다'))return 'conflict';
 if(value.includes('응답이 확인되지')||value.includes('결과를 확인할 수 없습니다'))return 'unknown';
 return 'other';
});}catch{networkEvidence.message='other';}}
process.stderr.write('TRAINER_NETWORK_EVIDENCE='+JSON.stringify(networkEvidence)+'\n');
process.stderr.write('TRAINER_BROWSER_FAILED stage='+stage+'\n');
const name=/^[A-Za-z]{1,40}$/.test(error?.name||'')?error.name:'Error';
const locations=[...(String(error?.stack||'').matchAll(/\/(?:browser|trainer)\.cjs:(\d+):(\d+)/g))]
 .map(match=>({line:Number(match[1]),column:Number(match[2])}));
process.stderr.write('TRAINER_ERROR_LOCATION='+JSON.stringify({name,locations})+'\n');
process.stderr.write('TRAINER_DIAGNOSTIC='+JSON.stringify(checks)+'\n');process.exitCode=1;}
finally{for(const release of releaseGates)await release();if(browser)await browser.close();}})();
