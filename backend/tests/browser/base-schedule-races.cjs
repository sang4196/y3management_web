 'use strict';
const fs=require('fs'),path=require('path'),R=process.env.Y3_BROWSER_RUN;
const checks={},required=JSON.parse(fs.readFileSync(path.join(R,'required-checks.json')));
let stage='start';
(async()=>{let browser;const releases=[];try{
const {chromium}=require(path.join(R,'playwright-core'));
const cfg=JSON.parse(fs.readFileSync(path.join(R,'input.json')));
browser=await chromium.launch({executablePath:path.join(R,'browser-binaries/chrome'),headless:true,
chromiumSandbox:true,args:['--no-proxy-server','--disable-background-networking']});
const context=await browser.newContext({ignoreHTTPSErrors:false}),p=await context.newPage();
stage='login';await p.goto(cfg.origin+'/login');checks.trusted_https=await p.evaluate(()=>isSecureContext);
await p.locator('#identifier').fill('master.test');await p.locator('#password').fill(cfg.masterPassword);
const login=p.waitForResponse(r=>r.url().endsWith('/auth/login'));
await p.locator('#password-form button').click();checks.actual_master_login=(await login).status()===204;
async function api(route,body){return p.evaluate(async({route,body})=>{
 const me=await(await fetch('/api/v1/auth/me')).json();let headers={'X-Y3-Expected-Actor':me.account_id};
 if(body){const c=await(await fetch('/api/v1/auth/csrf',{headers:{'X-Y3-Client':'browser'}})).json();
 headers={...headers,'Content-Type':'application/json','X-CSRF-Token':c.csrf_token};}
 const r=await fetch('/api/v1'+route,{method:body?'POST':'GET',headers,...(body?{body:JSON.stringify(body)}:{})});
 return {status:r.status,body:await r.json()};},{route,body});}
stage='setup';const branch=await api('/admin/branches',{code:'BASE',name:'기본급 가상지점'});
if(branch.status!==201)throw Error();
const reg=await api('/admin/trainers',{operation_id:await p.evaluate(()=>crypto.randomUUID()),
 name:'기본급 가상트레이너',phone:'example',home_branch_id:branch.body.id,
 rate_percent:0,fixed_amount_won:'0',base_salary_won:'100',base_salary_start_month:'2020-01'});
if(reg.status!==201)throw Error();const id=reg.body.trainer.id,base='/admin/trainers/'+id;

stage='initial-old-read';await p.goto(cfg.origin+'/trainers');
const box=p.locator('[data-base-trainer="'+id+'"]');await box.waitFor({state:'visible'});
// Finish the other initial panels before attributing the delayed Base owner proof.
await p.waitForFunction(id=>{const comp=document.querySelector('[data-compensation-trainer="'+id+'"] [data-compensation-change]');
 const home=document.querySelector('[data-home-trainer="'+id+'"] [data-home-change]');
 return comp&&!comp.disabled&&home&&!home.disabled;},id);
async function ready(){await box.locator('[data-base-create]').waitFor({state:'visible'});
await p.waitForFunction(id=>{const b=document.querySelector('[data-base-trainer="'+id+'"] [data-base-create]');return b&&!b.disabled;},id);}
async function external(start,amount){const state=(await api(base+'/base-schedule?basis_month=2099-01')).body;
return api(base+'/base-schedule/changes',{operation_id:await p.evaluate(()=>crypto.randomUUID()),
 expected_trainer_version:state.trainer_version,expected_base_ledger_version:state.base_ledger_version,
 start_month:start,planned_amount_won:amount});}
let release,observed;const gate=new Promise(r=>release=r),seen=new Promise(r=>observed=r);
releases.push(release);let held=false;
const pattern='**/api/v1/admin/trainers/'+id+'/base-schedule?*';
await p.route(pattern,async route=>{if(held){await route.continue();return;}held=true;
const response=await route.fetch();observed();await gate;try{await route.fulfill({response});}catch{}});
try{await box.locator('[data-base-open]').click();await seen;
if((await external('2090-01','7')).status!==200)throw Error();
await box.locator('[data-base-basis]').fill('2099-01');
await box.locator('[data-base-refresh]').click();await ready();
checks.new_ui_before_old_release=(await box.locator('[data-base-effective]').textContent()).includes('7원 / 2090-01');
const ownerBefore=(await api('/auth/me')).body.account_id;
const oldResponse=p.waitForResponse(r=>r.url().includes('/base-schedule?basis_month=0001-01'));
// No other panel is loading. This owner GET is the old Base load's final actor proof.
const oldOwnerProof=p.waitForResponse(r=>r.url().endsWith('/api/v1/auth/me')&&r.request().method()==='GET');
release();await (await oldResponse).finished();
const ownerResponse=await oldOwnerProof;await ownerResponse.finished();
if((await ownerResponse.json()).account_id!==ownerBefore)throw Error();
await p.evaluate(()=>new Promise(resolve=>queueMicrotask(()=>requestAnimationFrame(resolve))));
checks.old_initial_cannot_overwrite=(await box.locator('[data-base-effective]').textContent()).includes('7원 / 2090-01')&&
(await api(base+'/base-schedule?basis_month=2099-01')).body.trainer_version===1;
}finally{release();await p.unroute(pattern);}
stage='ack-abort';let abortedBody;
const writePattern='**/api/v1/admin/trainers/'+id+'/base-schedule/changes';
await p.route(writePattern,async route=>{abortedBody=route.request().postDataJSON();
const response=await route.fetch();if(response.status()!==200)throw Error();await route.abort('failed');});
await box.locator('[data-base-start]').fill('2091-01');await box.locator('[data-base-amount]').fill('8');
await box.locator('[data-base-create]').click();
await p.waitForFunction(id=>document.querySelector('[data-base-trainer="'+id+'"] [data-base-result]')
 .textContent.includes('불명확'),id);await p.unroute(writePattern);
const op=await box.locator('[data-base-operation]').inputValue();
checks.ack_commit_uncertain=abortedBody.expected_base_ledger_version===2&&abortedBody.operation_id===op&&
await box.locator('[data-base-create]').isDisabled();
await box.locator('[data-base-check]').click();await ready();
checks.same_uuid_reconciles_no_duplicate=(await api(base+'/base-schedule-history')).body.total===3&&
(await box.locator('[data-base-result]').textContent()).includes('작업 당시 create');
stage='receipt-then-new-current';const receiptPattern='**/api/v1/admin/trainer-base-operations/'+op;
let receiptCaptured;
await p.route(receiptPattern,async route=>{const response=await route.fetch();receiptCaptured=await response.json();
if((await external('2092-01','9')).status!==200)throw Error();await route.fulfill({response});});
await box.locator('[data-base-check]').click();await ready();await p.unroute(receiptPattern);
checks.receipt_then_external_current=receiptCaptured.current_base_ledger_version===3&&
(await box.locator('[data-base-effective]').textContent()).includes('9원 / 2092-01')&&
(await box.locator('[data-base-result]').textContent()).includes('현재 일정은 조회 패널 기준');
stage='actor-switch';const issued=await api('/admin/master-accounts',{login_id:'base.other'});
if(issued.status!==201)throw Error();const otherContext=await browser.newContext({ignoreHTTPSErrors:false});
const other=await otherContext.newPage();await other.goto(issued.body.setup_link);
await other.locator('#password').fill(cfg.branchPassword);
const setup=other.waitForResponse(r=>r.url().endsWith('/auth/credentials/complete'));
await other.locator('#submit').click();if((await setup).status()!==204)throw Error();
await other.goto(cfg.origin+'/login');await other.locator('#identifier').fill('base.other');
await other.locator('#password').fill(cfg.branchPassword);
const signin=other.waitForResponse(r=>r.url().endsWith('/auth/login'));
await other.locator('#password-form button').click();if((await signin).status()!==204)throw Error();
const otherId=(await other.evaluate(async()=> (await(await fetch('/api/v1/auth/me')).json()).account_id));
const originalId=(await api('/auth/me')).body.account_id;if(otherId===originalId)throw Error();
await box.locator('[data-base-amount]').fill('987654321');
let switchedPosts=0;p.on('request',r=>{if(r.method()==='POST')switchedPosts++;});
await context.clearCookies();await context.addCookies(await otherContext.cookies());
await box.locator('[data-base-refresh]').click();
await p.waitForFunction(id=>document.querySelector('[data-base-trainer="'+id+'"] [data-base-result]')
 .textContent.includes('새로 조회'),id);
checks.actor_switch_clears_selection=await box.locator('[data-base-create]').isDisabled()&&
await box.locator('[data-base-rows] li').count()===0&&await box.locator('[data-base-anchor]').textContent()===''&&
await box.locator('[data-base-amount]').inputValue()===''&&switchedPosts===0&&
!(await box.locator('[data-base-result]').textContent()).includes('작업 당시');
if(Object.keys(checks).length!==required.length||!required.every(k=>checks[k]===true))throw Error();
fs.writeFileSync(path.join(R,'browser-results.json'),JSON.stringify({checks,browser:browser.version()}));
}catch(error){stage=(stage+'-'+(['Error','TypeError','TimeoutError'].includes(error.name)?error.name.toLowerCase():'error')).slice(0,64);
process.stderr.write('WORKFORCE_BROWSER_FAILED stage='+stage+'\nWORKFORCE_DIAGNOSTIC='+JSON.stringify(checks)+'\n');process.exitCode=1;}
finally{for(const release of releases)release();if(browser)await browser.close();}})();
