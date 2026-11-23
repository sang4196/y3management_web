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
await p.setViewportSize({width:390,height:844});await p.goto(cfg.origin+'/trainers');
const box=p.locator('[data-base-trainer="'+id+'"]');await box.waitFor({state:'visible'});
checks.lazy_panel=await box.locator('[data-base-panel]').count()===0;
await box.locator('[data-base-open]').click();
async function ready(){await box.locator('[data-base-create]').waitFor({state:'visible'});
 await p.waitForFunction(id=>{const b=document.querySelector('[data-base-trainer="'+id+'"] [data-base-create]');return b&&!b.disabled;},id);}
await ready();checks.initial_anchor=(await box.locator('[data-base-anchor]').textContent()).includes('100원 / 2020-01');
await box.locator('[data-base-basis]').fill('2019-12');await box.locator('[data-base-refresh]').click();await ready();
checks.before_anchor_absence=(await box.locator('[data-base-effective]').textContent()).includes('없음');
await box.locator('[data-base-basis]').fill('2090-06');await box.locator('[data-base-refresh]').click();await ready();
await box.locator('[data-base-start]').fill('2090-01');await box.locator('[data-base-amount]').fill('100');
stage='create';await box.locator('[data-base-create]').click();await ready();
const first=await api(base+'/base-schedule?basis_month=2090-06');const cid=first.body.items[0].change_id;
checks.same_amount_boundary=first.body.base_ledger_version===2&&first.body.general_setting.change_id===cid;
let row=box.locator('[data-base-change="'+cid+'"]');await row.locator('[data-base-edit-amount]').fill('0');
stage='edit';await row.locator('[data-base-edit]').click();await ready();
checks.edit_zero=(await api(base+'/base-schedule?basis_month=2090-06')).body.general_setting.planned_amount_won==='0';
await row.locator('[data-base-edit]').click();await ready();
checks.edit_noop=(await api(base+'/base-schedule?basis_month=2090-06')).body.base_ledger_version===3;
let dialogText='';p.on('dialog',dialog=>{dialogText=dialog.message();dialog.accept();});stage='cancel';await row.locator('[data-base-cancel]').click();await ready();
const canceled=(await api(base+'/base-schedule?basis_month=2090-06')).body;
checks.cancel_retains_amount=!canceled.items[0].active&&canceled.items[0].planned_amount_won==='0'&&
(await row.textContent()).includes('적용 금액 아님');
checks.cancel_effective_anchor=canceled.general_setting.is_initial&&canceled.general_setting.planned_amount_won==='100'&&dialogText.includes('2090-01 / 0원');
await box.locator('[data-base-amount]').fill('7');await box.locator('[data-base-create]').click();await ready();
checks.vacated_new_identity=(await api(base+'/base-schedule?basis_month=2090-06')).body.general_setting.change_id!==cid;
stage='receipt';await box.locator('[data-base-check]').click();await ready();
checks.receipt_reconciles=(await box.locator('[data-base-result]').textContent()).includes('작업 당시 create');
const history=(await api(base+'/base-schedule-history')).body;
checks.history_preserved=history.total===5&&history.items.map(x=>x.kind).join(',')==='initial,create,edit,cancel,create';
// Hold only the first old plan response; a second refresh publishes the external new ledger.
stage='stale';let release,observed;const gate=new Promise(r=>release=r),seen=new Promise(r=>observed=r);
releases.push(release);let held=false;
const routePattern='**/api/v1/admin/trainers/'+id+'/base-schedule?*';
await p.route(routePattern,async route=>{if(held){await route.continue();return;}held=true;
 const response=await route.fetch();observed();await gate;try{await route.fulfill({response});}catch{}});
try{await box.locator('[data-base-refresh]').click();await seen;
 const old=(await api(base+'/base-schedule?basis_month=2090-06')).body;
 const changed=await api(base+'/base-schedule/changes',{operation_id:await p.evaluate(()=>crypto.randomUUID()),
 expected_base_ledger_version:old.base_ledger_version,expected_trainer_version:old.trainer_version,
 start_month:'2091-01',planned_amount_won:'9'});if(changed.status!==200)throw Error();
 release();await ready();
 // Old load is internally inconsistent with the audit read or remains a version5 CAS;
 // either refuses publication or a subsequent stale write must be rejected.
 const fresh=await api(base+'/base-schedule?basis_month=2090-06');
 await box.locator('[data-base-start]').fill('2092-01');
 await box.locator('[data-base-amount]').fill('10');
 const staleResponse=p.waitForResponse(r=>r.url().endsWith('/base-schedule/changes')&&r.request().method()==='POST');
 await box.locator('[data-base-create]').click();const rejected=await staleResponse;
 await p.waitForFunction(id=>document.querySelector('[data-base-trainer="'+id+'"] [data-base-result]')
 .textContent.includes('불명확'),id);
 checks.stale_read_rejected=fresh.body.base_ledger_version===6&&rejected.status()===409&&
 await box.locator('[data-base-create]').isDisabled();

}finally{release();await p.unroute(routePattern);}
checks.mobile_no_overflow=await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth);
if(Object.keys(checks).length!==required.length||!required.every(k=>checks[k]===true))throw Error();
fs.writeFileSync(path.join(R,'browser-results.json'),JSON.stringify({checks,browser:browser.version()}));
}catch(error){stage=(stage+'-'+(['Error','TypeError','TimeoutError'].includes(error.name)?error.name.toLowerCase():'error')).slice(0,64);
process.stderr.write('WORKFORCE_BROWSER_FAILED stage='+stage+'\nWORKFORCE_DIAGNOSTIC='+JSON.stringify(checks)+'\n');process.exitCode=1;}
finally{for(const release of releases)release();if(browser)await browser.close();}})();
