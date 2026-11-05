'use strict';
const fs=require('fs'),path=require('path'),R=process.env.Y3_BROWSER_RUN;
const checks={},required=JSON.parse(fs.readFileSync(path.join(R,'required-checks.json')));
let stage='start';
(async()=>{let browser;try{
const {chromium}=require(path.join(R,'playwright-core'));
const cfg=JSON.parse(fs.readFileSync(path.join(R,'input.json')));
browser=await chromium.launch({executablePath:path.join(R,'browser-binaries/chrome'),
headless:true,chromiumSandbox:true,args:['--no-proxy-server','--disable-background-networking']});
const admin=await browser.newContext({ignoreHTTPSErrors:false}),p=await admin.newPage();
async function click(page,selector,path){const result=page.waitForResponse(r=>r.url().endsWith(path)&&r.request().method()==='POST');
await page.locator(selector).click();return await result;}
async function get(page,route){return page.evaluate(async route=>{const r=await fetch('/api/v1'+route);
return {status:r.status,body:await r.json()};},route);}
async function post(page,route,body){return page.evaluate(async({route,body})=>{
const c=await(await fetch('/api/v1/auth/csrf',{headers:{'X-Y3-Client':'browser'}})).json();
const r=await fetch('/api/v1'+route,{method:'POST',headers:{'Content-Type':'application/json',
'X-CSRF-Token':c.csrf_token},body:JSON.stringify(body)});
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
await post(p,opPath,{expected_version:operator.version});
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
if(Object.keys(checks).length!==required.length||!required.every(k=>checks[k]===true))throw Error();
fs.writeFileSync(path.join(R,'browser-results.json'),JSON.stringify({checks,browser:browser.version()}));
}catch{process.stderr.write('TRAINER_BROWSER_FAILED stage='+stage+'\n');
process.stderr.write('TRAINER_DIAGNOSTIC='+JSON.stringify(checks)+'\n');process.exitCode=1;}
finally{if(browser)await browser.close();}})();
