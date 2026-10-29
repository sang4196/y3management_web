'use strict';
const fs=require('fs'),path=require('path'),R=process.env.Y3_BROWSER_RUN;
const checks={},required=JSON.parse(fs.readFileSync(path.join(R,'required-checks.json')));
let stage='start';
const causal={};
(async()=>{let browser;try{
const {chromium}=require(path.join(R,'playwright-core'));
const cfg=JSON.parse(fs.readFileSync(path.join(R,'input.json')));
browser=await chromium.launch({executablePath:path.join(R,'browser-binaries/chrome'),
headless:true,chromiumSandbox:true,args:['--no-proxy-server','--disable-background-networking']});
const admin=await browser.newContext({ignoreHTTPSErrors:false}),p=await admin.newPage();
const cdp=await admin.newCDPSession(p);await cdp.send('WebAuthn.enable');
await cdp.send('WebAuthn.addVirtualAuthenticator',{options:{protocol:'ctap2',transport:'internal',
hasResidentKey:true,hasUserVerification:true,isUserVerified:true,automaticPresenceSimulation:true}});
async function click(page,selector,path){const result=page.waitForResponse(r=>r.url().endsWith(path)&&r.request().method()==='POST');
await page.locator(selector).click();return await result;}
async function get(page,route){return page.evaluate(async route=>{const r=await fetch('/api/v1'+route);
return {status:r.status,body:await r.json()};},route);}
async function post(page,route,body){return page.evaluate(async({route,body})=>{
const c=await(await fetch('/api/v1/auth/csrf',{headers:{'X-Y3-Client':'browser'}})).json();
const r=await fetch('/api/v1'+route,{method:'POST',headers:{'Content-Type':'application/json',
'X-CSRF-Token':c.csrf_token},body:JSON.stringify(body)});
return {status:r.status,body:r.status===204?null:await r.json()};},{route,body});}
stage='admin';await p.goto(cfg.origin+'/enroll#token='+cfg.enrollmentToken);
checks.trusted_https=await p.evaluate(()=>isSecureContext);
checks.master_enroll=(await click(p,'#mfa button','/auth/passkeys/enrollment/verify')).status()===204;
await p.goto(cfg.origin+'/login');await p.locator('#identifier').fill('master.test');
await p.locator('#password').fill(cfg.masterPassword);
checks.master_uv=(await click(p,'#mfa button','/auth/login/passkey/verify')).status()===204;
const branch=await post(p,'/admin/branches',{code:'I1',name:'가상지점'});
if(branch.status!==201)throw Error();
stage='registration';await p.goto(cfg.origin+'/trainers');
await p.waitForFunction(()=>!document.getElementById('submit').disabled);
for(const [id,value] of Object.entries({name:'가상트레이너',phone:'+99 example',rate_percent:'0',
fixed_amount_won:'0',base_salary_won:'0',base_salary_start_month:'2026-10'}))await p.locator('#'+id).fill(value);
await p.locator('#home_branch_id').selectOption(branch.body.id);
const created=await click(p,'#submit','/api/v1/admin/trainers'),trainer=(await created.json()).trainer;
checks.w0_actual_form=created.status()===201;

const selector='[data-role-trainer="'+trainer.id+'"]', box=p.locator(selector);
p.on('dialog',dialog=>dialog.accept());
stage='lookup';await box.locator('form input').fill('master.test');
checks.exact_lookup=(await click(p,selector+' form button','/role-account-lookup')).status()===200;
await box.getByText('Trainer 역할 부여',{exact:true}).click();
checks.confirmation_required=await box.locator('[role=status]').textContent()==='동일인 확인이 필요합니다.';
await box.locator('input[type=checkbox]').check();
let roleReply=null;
await p.route('**/api/v1/admin/trainers/'+trainer.id+'/role',async route=>{
 if(route.request().method()!=='POST'){await route.continue();return;}
 const response=await route.fetch();roleReply=await response.json();await route.fulfill({response});
});
stage='self-link';const linked=await click(p,selector+' button:text-is("Trainer 역할 부여")','/role');
const outcome=roleReply;stage=linked.status()===200?'self-linked':linked.status()===409?'self-conflict':linked.status()===401?'self-unauthorized':linked.status()===422?'self-invalid':'self-error';checks.self_link=linked.status()===200&&outcome.changed&&outcome.reauthentication_required;
await p.waitForURL('**/login');checks.self_redirect=true;
checks.self_cookie_cleared=!(await admin.cookies()).some(c=>c.name==='__Host-y3-auth');
checks.old_session_denied=(await get(p,'/auth/me')).status===401;
async function login(){await p.goto(cfg.origin+'/login');await p.locator('#identifier').fill('master.test');
await p.locator('#password').fill(cfg.masterPassword);
const response=await click(p,'#mfa button','/auth/login/passkey/verify');await p.getByText('로그인되었습니다.',{exact:true}).waitFor();return response.status();}
checks.relogin_uv=await login()===204;
const me=await get(p,'/auth/me');checks.dual_roles=me.status===200&&me.body.roles.map(x=>x.role).join(',')==='ADMIN,TRAINER';
stage='w1-admin';await p.goto(cfg.origin+'/trainers');
const stateSelector='[data-state-trainer="'+trainer.id+'"]';
const adminState=p.locator(stateSelector);
const cookieBefore=(await admin.cookies()).find(c=>c.name==='__Host-y3-auth').value;
checks.w1_admin_off=(await click(p,stateSelector+' button:text-is("Trainer 비활성화")','/state')).status()===200;
await adminState.getByText('업무 상태 처리 완료. 작업 번호를 보관하세요.',{exact:true}).waitFor();
const adminStateOperation=await adminState.getByLabel('업무 상태 작업 번호').inputValue();
const inactiveMe=await get(p,'/auth/me');
checks.w1_admin_session=inactiveMe.status===200&&inactiveMe.body.roles.map(x=>x.role).join(',')==='ADMIN'&&
 (await admin.cookies()).find(c=>c.name==='__Host-y3-auth').value===cookieBefore;
await adminState.getByText('새 상태 작업',{exact:true}).click();
checks.w1_admin_on=(await click(p,stateSelector+' button:text-is("Trainer 재활성화")','/state')).status()===200;
await adminState.getByText('업무 상태 처리 완료. 작업 번호를 보관하세요.',{exact:true}).waitFor();
checks.w1_dual_restored=(await get(p,'/auth/me')).body.roles.map(x=>x.role).join(',')==='ADMIN,TRAINER';
const status=await get(p,'/admin/trainer-role-operations/'+outcome.operation_id);
checks.receipt=status.status===200&&status.body.committed_granted===true;
checks.status_keeps_session=(await get(p,'/auth/me')).status===200;
stage='withdraw';await p.goto(cfg.origin+'/trainers');
await box.getByText('Trainer 역할 회수',{exact:true}).waitFor();
const revoked=await click(p,selector+' button:text-is("Trainer 역할 회수")','/role');
checks.self_withdraw=revoked.status()===200&&roleReply.reauthentication_required;
await p.waitForURL('**/login');checks.withdraw_relogin=await login()===204;
const after=await get(p,'/auth/me');checks.admin_survives=after.status===200&&after.body.roles.map(x=>x.role).join(',')==='ADMIN'&&after.body.trainer_binding.granted===false;
stage='regrant';await p.unroute('**/api/v1/admin/trainers/'+trainer.id+'/role');
await p.goto(cfg.origin+'/trainers');
let lostId=null;
await p.route('**/api/v1/admin/trainers/'+trainer.id+'/role',async route=>{
 if(route.request().method()!=='POST'){await route.continue();return;}
 lostId=route.request().postDataJSON().operation_id;
 const committed=await route.fetch();checks.commit_before_drop=committed.status()===200;
 await route.abort('failed');
});
await box.getByText('Trainer 역할 부여',{exact:true}).click();
await box.getByText('결과가 불명확합니다. 자동 재시도하지 말고 작업 결과를 확인해 주세요.',{exact:true}).waitFor();
checks.operation_displayed=await box.getByLabel('역할 작업 번호').inputValue()===lostId;
checks.drop_old_session_denied=(await get(p,'/auth/me')).status===401;
await p.unroute('**/api/v1/admin/trainers/'+trainer.id+'/role');
checks.regrant_uv=await login()===204;
await p.goto(cfg.origin+'/trainers');await box.getByLabel('역할 작업 번호').fill(lostId);
const receipt=p.waitForResponse(r=>r.url().endsWith('/trainer-role-operations/'+lostId));
await box.getByText('역할 작업 결과 확인',{exact:true}).click();
const reconciled=await receipt;checks.lost_response_reconciled=reconciled.status()===200&&(await reconciled.json()).committed_granted;
checks.reconcile_keeps_new_session=(await get(p,'/auth/me')).status===200;
stage='pending';
const pendingTrainer=await post(p,'/admin/trainers',{operation_id:crypto.randomUUID(),name:'미설정 가상트레이너',phone:'가상',home_branch_id:branch.body.id,rate_percent:0,fixed_amount_won:'0',base_salary_won:'0',base_salary_start_month:'2026-10'});
if(pendingTrainer.status!==201)throw Error();
const pendingId=pendingTrainer.body.trainer.id;await p.goto(cfg.origin+'/trainers');
const account=p.locator('[data-trainer="'+pendingId+'"]');
const roles=p.locator('[data-role-trainer="'+pendingId+'"]');
// Deliver a real pre-issue account GET only after the new link is displayed.
const causalState=p.locator('[data-state-trainer="'+pendingId+'"]');
await causalState.getByText('새 상태 작업',{exact:true}).click();
await account.locator('form input').fill('pending.native');
const accountPath='/api/v1/admin/trainers/'+pendingId+'/login-account';
let releaseOld,oldReady,oldDelivered,holding=false;
const oldGate=new Promise(resolve=>{releaseOld=resolve;});
const oldCaptured=new Promise(resolve=>{oldReady=resolve;});
const oldDone=new Promise(resolve=>{oldDelivered=resolve;});
await p.route('**'+accountPath,async route=>{
 if(holding||route.request().method()!=='GET'){await route.continue();return;}
 holding=true;const response=await route.fetch();const body=await response.json();
 causal.preissue_response=response.status()===200&&body.account_id===null;
 oldReady();await oldGate;await route.fulfill({response});oldDelivered();
});
await account.getByText('계정 상태 확인',{exact:true}).click();await oldCaptured;
const issued=await click(p,'[data-trainer="'+pendingId+'"] form button','/login-account');
const initial=(await issued.json()).setup_link;checks.pending_issue=issued.status()===201;
await account.locator('a').waitFor();
await p.waitForFunction(id=>!Array.from(document.querySelector('[data-trainer="'+id+'"]')
 .querySelectorAll('button')).find(b=>b.textContent==='초기 설정 링크 재발급').disabled,pendingId);
causal.link_before_release=await account.locator('a').count()===1;
const oldResponse=p.waitForResponse(r=>r.url().endsWith(accountPath)&&r.request().method()==='GET');
releaseOld();await oldDone;await (await oldResponse).finished();
await p.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
await p.unroute('**'+accountPath);
causal.link_after_release=await account.locator('a').count()===1;
checks.causal_real_preissue_response=causal.preissue_response;
checks.causal_link_before_release=causal.link_before_release;
checks.causal_link_survives_late_response=causal.link_after_release;
stage='w1-pending';
const statePending=p.locator('[data-state-trainer="'+pendingId+'"]');
const statePath='/api/v1/admin/trainers/'+pendingId+'/state';let stateLost=null;
const initialExpires=(await get(p,'/admin/trainers/'+pendingId+'/login-account')).body.initial_setup_expires_at;
// A second real response crosses the committed W1 change through the role panel.
const trainerPath='/api/v1/admin/trainers/'+pendingId;
let releaseTrainer,trainerReady,trainerDelivered,trainerHolding=false;
const trainerGate=new Promise(resolve=>{releaseTrainer=resolve;});
const trainerCaptured=new Promise(resolve=>{trainerReady=resolve;});
const trainerDone=new Promise(resolve=>{trainerDelivered=resolve;});
await p.route('**'+trainerPath,async route=>{
 if(trainerHolding||route.request().method()!=='GET'){await route.continue();return;}
 trainerHolding=true;const response=await route.fetch();const body=await response.json();
 causal.preoff_response=response.status()===200&&body.active===true;
 trainerReady();await trainerGate;await route.fulfill({response});trainerDelivered();
});
await roles.getByText('새 역할 작업',{exact:true}).click();await trainerCaptured;
await p.route('**'+statePath,async route=>{
 if(route.request().method()!=='POST'){await route.continue();return;}
 stateLost=route.request().postDataJSON().operation_id;
 const response=await route.fetch();checks.w1_commit_before_drop=response.status()===200;
 await route.abort('failed');});
await statePending.getByText('Trainer 비활성화',{exact:true}).click();
await statePending.getByText('결과가 불명확합니다. 작업 번호로 결과를 확인해 주세요.',{exact:true}).waitFor();
checks.w1_operation_retained=await statePending.getByLabel('업무 상태 작업 번호').inputValue()===stateLost;
await p.unroute('**'+statePath);
await statePending.getByText('상태 작업 결과 확인',{exact:true}).click();
await statePending.getByText('상태 변경 기록 확인',{exact:true}).waitFor();
const trainerResponse=p.waitForResponse(r=>r.url().endsWith(trainerPath)&&r.request().method()==='GET');
releaseTrainer();await trainerDone;await (await trainerResponse).finished();
await p.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
await p.unroute('**'+trainerPath);
checks.causal_real_preoff_response=causal.preoff_response;
checks.causal_inactive_survives_late_response=
 await statePending.getByText('Trainer 재활성화',{exact:true}).count()===1&&
 await account.getByText('초기 설정 링크 재발급',{exact:true}).isDisabled()&&
 await roles.getByText('Trainer 역할 부여',{exact:true}).isDisabled();
checks.w1_link_paused=await account.locator('a').count()===1&&
 await account.locator('a').getAttribute('href')===null&&
 await account.locator('a').getAttribute('aria-disabled')==='true';
causal.paused=await account.evaluate(box=>({link_count:box.querySelectorAll('a').length,
 href_present:!!box.querySelector('a')?.hasAttribute('href'),
 aria_disabled:box.querySelector('a')?.getAttribute('aria-disabled')==='true'}));
checks.w1_panels_inactive=await account.getByText('초기 설정 링크 재발급',{exact:true}).isDisabled()&&
 await roles.getByText('Trainer 역할 부여',{exact:true}).isDisabled();
await statePending.getByText('새 상태 작업',{exact:true}).click();
checks.w1_pending_on=(await click(p,'[data-state-trainer="'+pendingId+'"] button:text-is("Trainer 재활성화")','/state')).status()===200;
await statePending.getByText('업무 상태 처리 완료. 작업 번호를 보관하세요.',{exact:true}).waitFor();
checks.w1_link_preserved=await account.locator('a').getAttribute('href')===initial&&
 (await get(p,'/admin/trainers/'+pendingId+'/login-account')).body.initial_setup_expires_at===initialExpires;
checks.w1_panels_reactivated=!(await account.getByText('초기 설정 링크 재발급',{exact:true}).isDisabled())&&
 !(await roles.getByText('Trainer 역할 부여',{exact:true}).isDisabled());
stage='pending';
await roles.getByText('새 역할 작업',{exact:true}).click();
const withdrawal=await click(p,'[data-role-trainer="'+pendingId+'"] button:text-is("Trainer 역할 회수")','/role');
checks.pending_withdraw=withdrawal.status()===200;
await account.locator('a').waitFor({state:'detached'});
checks.withdrawn_link_removed=await account.locator('a').count()===0;
await p.waitForFunction(id=>Array.from(document.querySelector('[data-trainer="'+id+'"]').querySelectorAll('button')).some(b=>b.textContent==='초기 설정 링크 재발급'&&b.disabled),pendingId);
checks.withdrawn_reissue_disabled=await account.getByText('초기 설정 링크 재발급',{exact:true}).isDisabled();
await roles.getByText('새 역할 작업',{exact:true}).click();
checks.pending_regrant=(await click(p,'[data-role-trainer="'+pendingId+'"] button:text-is("Trainer 역할 부여")','/role')).status()===200;
await account.getByText('초기 설정 링크 재발급',{exact:true}).waitFor();
const reissued=await click(p,'[data-trainer="'+pendingId+'"] button:text-is("초기 설정 링크 재발급")','/initial-setup');
const newLink=(await reissued.json()).setup_link;checks.explicit_new_source=reissued.status()===201&&initial!==newLink;
const recipient=await browser.newContext({ignoreHTTPSErrors:false});const r=await recipient.newPage();
await r.goto(initial);await r.locator('#new-password').fill(cfg.branchPassword);
checks.old_source_rejected=(await click(r,'#trainer-setup button','/trainer-credentials/complete')).status()===400;
await r.goto('about:blank');await r.goto(newLink);await r.locator('#new-password').fill(cfg.branchPassword);
checks.new_source_setup=(await click(r,'#trainer-setup button','/trainer-credentials/complete')).status()===204;
await r.goto(cfg.origin+'/login');await r.locator('#identifier').fill('pending.native');await r.locator('#password').fill(cfg.branchPassword);
checks.pending_trainer_login=(await click(r,'#mfa button','/auth/login')).status()===204;
stage='wrong-card';
await roles.getByLabel('역할 작업 번호').fill(outcome.operation_id);
const otherReceipt=p.waitForResponse(x=>x.url().endsWith('/trainer-role-operations/'+outcome.operation_id));
await roles.getByText('역할 작업 결과 확인',{exact:true}).click();
await otherReceipt;await roles.getByText('다른 Trainer의 작업 번호입니다.',{exact:true}).waitFor();
checks.wrong_card_receipt_rejected=await roles.locator('[role=status]').textContent()==='다른 Trainer의 작업 번호입니다.';
stage='w1-wrong-card';
const beforeWrongState=await get(p,'/admin/trainers/'+pendingId);
const beforeWrongCookie=(await admin.cookies()).find(c=>c.name==='__Host-y3-auth').value;
await statePending.getByLabel('업무 상태 작업 번호').fill(adminStateOperation);
await statePending.getByText('상태 작업 결과 확인',{exact:true}).click();
await statePending.getByText('다른 Trainer의 작업 번호입니다.',{exact:true}).waitFor();
checks.w1_wrong_card_receipt_rejected=await statePending.locator('[role=status]').textContent()===
 '다른 Trainer의 작업 번호입니다.';
const afterWrongState=await get(p,'/admin/trainers/'+pendingId);
checks.w1_wrong_card_preserves_state_session=afterWrongState.status===200&&
 JSON.stringify(beforeWrongState.body)===JSON.stringify(afterWrongState.body)&&
 (await get(p,'/auth/me')).status===200&&
 (await admin.cookies()).find(c=>c.name==='__Host-y3-auth').value===beforeWrongCookie;
await p.setViewportSize({width:390,height:844});await p.goto(cfg.origin+'/login');
checks.login_390=await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth&&document.querySelector('meta[name=viewport]')!==null);
stage='nojs';const off=await browser.newContext({javaScriptEnabled:false,ignoreHTTPSErrors:false});
const n=await off.newPage();await n.goto(newLink);
checks.nojs_disabled=await n.locator('form button').isDisabled();
checks.nojs_post=await n.locator('form').getAttribute('method')==='post';
if(Object.keys(checks).length!==required.length||!required.every(k=>checks[k]===true))throw Error();
fs.writeFileSync(path.join(R,'browser-results.json'),JSON.stringify({checks,browser:browser.version()}));
 }catch(error){
causal.error_name=['Error','TimeoutError','TypeError'].includes(error?.name)?error.name:'Other';
process.stderr.write('TRAINER_SAFE_CAUSAL='+JSON.stringify(causal)+'\n');
process.stderr.write('TRAINER_BROWSER_FAILED stage='+stage+'\n');
process.stderr.write('TRAINER_DIAGNOSTIC='+JSON.stringify(checks)+'\n');process.exitCode=1;}
finally{if(browser)await browser.close();}})();
