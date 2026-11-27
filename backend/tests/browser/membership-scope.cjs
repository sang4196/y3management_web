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
async function signin(client=p,login='master.test',password=cfg.masterPassword){
 await client.goto(cfg.origin+'/login');await client.locator('#identifier').fill(login);
 await client.locator('#password').fill(password);
 const response=client.waitForResponse(r=>r.url().endsWith('/auth/login'));
 await client.locator('#password-form button').click();if((await response).status()!==204)throw Error();
 await client.locator('#members-link').waitFor();
}
async function api(route,body,client=p){return client.evaluate(async({route,body})=>{
 const me=await(await fetch('/api/v1/auth/me')).json();let headers={'X-Y3-Expected-Actor':me.account_id};
 if(body){const c=await(await fetch('/api/v1/auth/csrf',{headers:{'X-Y3-Client':'browser'}})).json();
 headers={...headers,'Content-Type':'application/json','X-CSRF-Token':c.csrf_token};}
 const r=await fetch('/api/v1'+route,{method:body?'POST':'GET',headers,...(body?{body:JSON.stringify(body)}:{})});
 return {status:r.status,body:r.status===204?{}:await r.json()};},{route,body});}
const uuid=()=>p.evaluate(()=>crypto.randomUUID());
async function ready(){await p.waitForFunction(()=>!document.querySelector('#save').matches(':disabled'));}
async function current(id,version){await p.waitForFunction(v=>document.querySelector('#selection').textContent.includes('v'+v),version);await ready();return (await api('/admin/members/'+id)).body;}
async function createBranch(code){const r=await api('/admin/branches',{code,name:'가상 '+code});if(r.status!==201)throw Error();return r.body.id;}
async function fill(name,phone='010-2000-0000'){await p.locator('#name').fill(name);await p.locator('#phone').fill(phone);}
stage='login';await signin();checks.trusted_https=await p.evaluate(()=>isSecureContext);
stage='scope-seed';const a=await createBranch('MEM-A'),b=await createBranch('MEM-B'),c=await createBranch('MEM-C');
const issued=await api('/admin/operator-accounts',{login_id:'member.operator',branch_id:b});if(issued.status!==201)throw Error();
const opContext=await browser.newContext({ignoreHTTPSErrors:false}),op=await opContext.newPage();
await op.goto(issued.body.setup_link);await op.locator('#new-password').fill(cfg.branchPassword);
const setup=op.waitForResponse(r=>r.url().endsWith('/auth/operator-credentials/complete'));
await op.locator('form button').click();if((await setup).status()!==204)throw Error();
await signin(op,'member.operator',cfg.branchPassword);
checks.operator_account_menu=op.url().endsWith('/account')&&await op.locator('#members-link').getAttribute('href')==='/members';
await op.locator('#members-link').click();await op.waitForFunction(()=>!document.querySelector('#save').matches(':disabled'));
checks.operator_candidate_scope=await op.locator('#home option').count()===2&&await op.locator('#home option[value="'+b+'"]').count()===1;
await op.locator('#home').selectOption(b);await op.locator('#name').fill('Operator 실제 등록');await op.locator('#phone').fill('01020000000');
await op.locator('#save').click();await op.waitForFunction(()=>document.querySelector('#selection').textContent.includes('v1'));
await op.waitForFunction(()=>!document.querySelector('#save').matches(':disabled'));
await op.locator('#name').fill('Operator 실제 수정');await op.locator('#save').click();
await op.waitForFunction(()=>document.querySelector('#selection').textContent.includes('v2'));
checks.operator_real_create_update_no_admin_state=await op.locator('#deactivate').isHidden()&&await op.locator('#reactivate').isHidden();
const list=(await api('/admin/members',undefined,op)).body,id=list.items[0].id;
checks.operator_other_home_denied=(await api('/admin/members',{operation_id:await uuid(),home_branch_id:a,name:'불가',phone:'01020000000'},op)).status===404;
stage='actual-scope-change';const oldNonce=await op.evaluate(async()=>
(await(await fetch('/api/v1/auth/csrf',{headers:{'X-Y3-Client':'browser'}})).json()).csrf_token);
const row=(await api('/admin/operator-roles/lookup',{login_id:'member.operator',branch_id:b})).body;
const moved=await api('/admin/operator-roles/'+row.account_id+'/branch',{operation_id:await uuid(),expected_account_version:row.account_version,
expected_operator_version:row.operator_grant.scope.version,branch_id:c});if(moved.status!==200)throw Error();
const replacement=await opContext.newPage();await signin(replacement,'member.operator',cfg.branchPassword);
// Hold the nonce at its original value so this condition observes the real scope fingerprint change independently.
await op.route('**/api/v1/auth/csrf',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({csrf_token:oldNonce})}));
let posts=0;op.on('request',r=>{if(r.method()==='POST'&&r.url().includes('/admin/members'))posts++;});
await op.locator('#name').fill('옛 지점 초안');await op.locator('#save').click();
await op.waitForFunction(()=>document.querySelector('#message').textContent.includes('로그인 또는 관리 범위'));
checks.same_actor_actual_scope_change_old_post_zero=posts===0;
checks.scope_change_clears_selection_personal_values=await op.locator('#phone').inputValue()===''&&await op.locator('#name').inputValue()===''&&
await op.locator('#selection').textContent()==='';
await op.unroute('**/api/v1/auth/csrf');
checks.new_scope_blocks_old_direct_id=(await api('/admin/members/'+id,undefined,replacement)).status===404;
await replacement.locator('#members-link').click();await replacement.waitForFunction(()=>!document.querySelector('#save').matches(':disabled'));
checks.new_scope_candidate_current=await replacement.locator('#home option[value="'+c+'"]').count()===1&&await replacement.locator('#home option[value="'+b+'"]').count()===0;
await opContext.close();
for(const key of required)if(checks[key]!==true)throw Error();
fs.writeFileSync(path.join(R,'browser-results.json'),JSON.stringify({checks,browser:browser.version()}));
}catch{console.error('WORKFORCE_BROWSER_FAILED stage='+stage);console.error('WORKFORCE_DIAGNOSTIC='+JSON.stringify(checks));process.exitCode=1;}
finally{for(const release of releases)release();if(browser)await browser.close();}})();
