 'use strict';
const fs=require('fs'),path=require('path'),R=process.env.Y3_BROWSER_RUN;
const checks={},required=JSON.parse(fs.readFileSync(path.join(R,'required-checks.json')));
let stage='start',geometry=null;
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
checks.admin_management_menu=await p.locator('#pass-management-link').getAttribute('href')==='/pass-management';
const a=await createBranch('STATE-A'),b=await createBranch('STATE-B');
const tr=await api('/admin/trainers',{operation_id:await uuid(),name:'활성 Trainer',phone:'가상',home_branch_id:a,
rate_percent:0,fixed_amount_won:'0',base_salary_won:'0',base_salary_start_month:'2020-01'});
if(tr.status!==201)throw Error();const trainer=tr.body.trainer.id;
const member=await api('/admin/members',{operation_id:await uuid(),name:'가상 회원',phone:'01020000000',home_branch_id:a});if(member.status!==200)throw Error();
const product=await api('/admin/products',{operation_id:await uuid(),name:'X'.repeat(200),price_won:'0',session_count:'5',payment_type:'RATE',is_service:false});if(product.status!==200)throw Error();
async function issue(branch){const r=await api('/admin/passes',{operation_id:await uuid(),issued_branch_id:branch,expected_branch_version:1,
member_id:member.body.current_member.id,expected_member_version:1,trainer_id:trainer,expected_trainer_version:1,
product_id:product.body.current_product.id,expected_product_version:1});if(r.status!==200)throw Error();return r.body;}
const issuedA=await issue(a),issuedB=await issue(b),id=issuedB.pass_record.id;
stage='management-page';await p.locator('#pass-management-link').click();
await p.locator('#members button').filter({hasText:id}).waitFor();
let invalidGets=0;const invalidObserver=r=>{if(r.url().includes('/admin/pass-management/passes/'))invalidGets++;};p.on('request',invalidObserver);
await p.locator('#pass-id').fill('private-marker/../bad');await p.locator('#find').click();
await p.waitForFunction(()=>document.querySelector('#message').textContent.includes('올바른 이용권'));
checks.invalid_pass_text_not_sent_to_url=invalidGets===0;p.off('request',invalidObserver);
await p.locator('#members button').filter({hasText:id}).click();
await p.waitForFunction(()=>document.querySelector('#selection').textContent.includes('v1'));
await p.setViewportSize({width:390,height:844});await p.locator('#reason').fill('긴사유'.repeat(66));
checks.mobile_390_long_name_reason=await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth);
stage='ack-loss';const write='**/api/v1/admin/pass-management/passes/'+id+'/expiration';let saved,posts=0;
const postObserver=r=>{if(r.method()==='POST'&&r.url().endsWith('/pass-management/passes/'+id+'/expiration'))posts++;};p.on('request',postObserver);
await p.route(write,async route=>{saved=route.request().postDataJSON();const r=await route.fetch();if(r.status()!==200)throw Error();await route.abort('failed');});
await p.locator('#expire').click();await p.waitForFunction(()=>document.querySelector('#message').textContent.includes('불명확'));
checks.unknown_uuid_kept_reason_cleared=await p.locator('#operation').textContent().then(t=>t.includes(saved.operation_id))&&
await p.locator('#reason').inputValue()===''&&await p.locator('#selection').textContent()==='';
await p.unroute(write);await p.locator('#reconcile').click();
await p.waitForFunction(()=>document.querySelector('#selection').textContent.includes('v2'));
checks.ack_receipt_without_new_post=posts===1&&(await api('/admin/pass-management/passes/'+id)).body.manual_expired===true;
checks.success_restores_list_and_same_balance=await p.locator('#members button').filter({hasText:id}).count()===1&&
(await p.locator('#selection').textContent()).includes('잔여 5회');
stage='release';await p.locator('#reason').fill('가상 해제');await p.locator('#release').click();
await p.waitForFunction(()=>document.querySelector('#selection').textContent.includes('v3'));
checks.release_preserves_issue_original=JSON.stringify((await api('/admin/pass-operations/'+issuedB.operation_id)).body)===JSON.stringify(issuedB)&&
(await api('/admin/pass-management/passes/'+id)).body.manual_expired===false;
stage='missing-stale';let unsubmitted;
await p.route(write,async route=>{unsubmitted=route.request().postDataJSON();await route.abort('failed');});
await p.locator('#reason').fill('미전달 가상 사유');await p.locator('#expire').click();
await p.waitForFunction(()=>document.querySelector('#message').textContent.includes('불명확'));await p.unroute(write);
const advance=await api('/admin/pass-management/passes/'+id+'/expiration',{operation_id:await uuid(),expected_state_version:3,desired_expired:true,reason:'다른 가상 처리'});if(advance.status!==200)throw Error();
let retry;await p.route(write,async route=>{retry=route.request().postDataJSON();await route.continue();});
await p.locator('#reconcile').click();await p.waitForFunction(()=>document.querySelector('#selection').textContent.includes('v4'));await p.unroute(write);
checks.receipt404_exact_retry409_fresh_state=JSON.stringify(retry)===JSON.stringify(unsubmitted)&&await p.locator('#reason').inputValue()===''&&await p.locator('#operation').textContent()==='';
let fresh;await p.route(write,async route=>{fresh=route.request().postDataJSON();await route.continue();});
await p.locator('#reason').fill('새 현재 버전 해제');await p.locator('#release').click();
await p.waitForFunction(()=>document.querySelector('#selection').textContent.includes('v5'));await p.unroute(write);
checks.fresh_command_new_uuid_cas=fresh.operation_id!==unsubmitted.operation_id&&fresh.expected_state_version===4;
stage='same-session-relogin';await p.route(write,route=>route.abort('failed'));
await p.locator('#reason').fill('옛 세션 사유');await p.locator('#expire').click();await p.waitForFunction(()=>document.querySelector('#message').textContent.includes('불명확'));await p.unroute(write);
const replacement=await context.newPage();await replacement.goto(cfg.origin+'/account');await api('/auth/logout',{},replacement);await signin(replacement);
const countBefore=posts;await p.locator('#reconcile').click();
await p.waitForFunction(()=>document.querySelector('#message').textContent.includes('관리 범위가 변경'));
checks.same_actor_new_session_clears_reason_old_post_zero=posts===countBefore&&await p.locator('#reason').inputValue()===''&&
await p.locator('#members').textContent()===''&&await p.locator('#selection').textContent()==='';p.off('request',postObserver);
stage='ba-operator-scope';const issued=await api('/admin/accounts',{login_id:'state.branch',branch_id:a},replacement);if(issued.status!==201)throw Error();
const baContext=await browser.newContext({ignoreHTTPSErrors:false}),ba=await baContext.newPage();
await ba.goto(issued.body.setup_link);await ba.locator('#password').fill(cfg.branchPassword);
const complete=ba.waitForResponse(r=>r.url().endsWith('/auth/credentials/complete'));await ba.locator('#submit').click();if((await complete).status()!==204)throw Error();
const lookup=await api('/admin/operator-roles/lookup',{login_id:'state.branch',branch_id:b},replacement);
const granted=await api('/admin/operator-roles/'+lookup.body.account_id+'/changes',{operation_id:await uuid(),expected_account_version:lookup.body.account_version,
expected_operator_version:0,branch_id:b,desired_granted:true},replacement);if(granted.status!==200)throw Error();
await signin(ba,'state.branch',cfg.branchPassword);await ba.locator('#pass-management-link').click();
await ba.locator('#members button').filter({hasText:issuedA.pass_record.id}).waitFor();
checks.ba_a_operator_b_list_direct_scope=await ba.locator('#members button').count()===1&&
(await api('/admin/pass-management/passes/'+id,undefined,ba)).status===404;
await ba.locator('#members button').first().click();await ba.waitForFunction(()=>document.querySelector('#selection').textContent.includes('v1'));
await ba.locator('#reason').fill('현재 발급 지점 관리자 처리');await ba.locator('#expire').click();
await ba.waitForFunction(()=>document.querySelector('#selection').textContent.includes('v2'));
checks.ba_real_expiration=(await api('/admin/pass-management/passes/'+issuedA.pass_record.id,undefined,ba)).body.manual_expired===true;
await baContext.close();
for(const key of required)if(checks[key]!==true)throw Error();
fs.writeFileSync(path.join(R,'browser-results.json'),JSON.stringify({checks,browser:browser.version()}));
}catch{console.error('WORKFORCE_BROWSER_FAILED stage='+stage);console.error('WORKFORCE_DIAGNOSTIC='+JSON.stringify(checks));process.exitCode=1;}
finally{for(const release of releases)release();if(browser)await browser.close();}})();
