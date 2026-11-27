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
checks.login_issue_menu=await p.locator('#passes-link').getAttribute('href')==='/passes';
const a=await createBranch('ISSUE-A'),b=await createBranch('ISSUE-B');
const reg=await api('/admin/trainers',{operation_id:await uuid(),name:'활성 미발급 Trainer',phone:'가상',home_branch_id:a,
rate_percent:0,fixed_amount_won:'0',base_salary_won:'0',base_salary_start_month:'2020-01'});
if(reg.status!==201)throw Error();const trainer=reg.body.trainer.id;
const members=[];for(let i=0;i<2;i++){const r=await api('/admin/members',{operation_id:await uuid(),name:'같은 이름',phone:'01020000000',home_branch_id:a});if(r.status!==200)throw Error();members.push(r.body.current_member.id);}
const prod=await api('/admin/products',{operation_id:await uuid(),name:'발급 상품',price_won:'9'.repeat(1024),session_count:'9223372036854775807',payment_type:'FIXED_AMOUNT',is_service:true});
if(prod.status!==200)throw Error();const product=prod.body.current_product.id;
stage='master-issue-page';await p.locator('#passes-link').click();
stage='master-branch-attached';await p.locator('#issued option[value="'+b+'"]').waitFor({state:'attached'});
let release,seen,held=false;const gate=new Promise(r=>release=r),observed=new Promise(r=>seen=r);releases.push(release);
const products='**/api/v1/admin/pass-issuance/products?*';
await p.route(products,async route=>{if(held){await route.continue();return;}held=true;const r=await route.fetch();seen();await gate;await route.fulfill({response:r});});
stage='master-branch-select';await p.locator('#issued').selectOption(b);
stage='master-product-response-held';await observed;
checks.search_blocked_until_choices_ready=await p.locator('#search').isDisabled();release();
stage='master-choices-ready';
await p.waitForFunction(()=>!document.querySelector('#search').disabled);await p.unroute(products);
checks.choices_survive_initial_search_race=await p.locator('#trainer option[value="'+trainer+'"]').count()===1&&await p.locator('#product option[value="'+product+'"]').count()===1;
async function selectMember(id=members[1]){await p.locator('#query').fill('같은 이름');await p.locator('#search').click();
await p.locator('#members button').filter({hasText:id}).click();
await p.locator('#trainer').selectOption(trainer);await p.locator('#product').selectOption(product);}
stage='duplicate-select';await p.locator('#query').fill('같은 이름');await p.locator('#search').click();
await p.locator('#members button').nth(1).waitFor();
checks.duplicate_members_explicit_uuid_no_auto_selection=await p.locator('#issue').isDisabled()&&
await p.locator('#selection').textContent()===''&&await p.locator('#members button').filter({hasText:members[0]}).count()===1&&
await p.locator('#members button').filter({hasText:members[1]}).count()===1;
await p.locator('#members button').filter({hasText:members[1]}).click();
await p.locator('#trainer').selectOption(trainer);await p.locator('#product').selectOption(product);
let firstCommand;const sent=p.waitForResponse(r=>r.url().endsWith('/admin/passes')&&r.request().method()==='POST');
await p.locator('#issue').click();const response=await sent;firstCommand=response.request().postDataJSON();const first=await response.json();
await p.waitForFunction(()=>document.querySelector('#receipt').textContent.includes('발급 완료'));
checks.actual_issue_original_conditions=first.pass_record.member_id===members[1]&&first.pass_record.initial_trainer_id===trainer&&
first.pass_record.product.price_won==='9'.repeat(1024)&&first.pass_record.initial_remaining_sessions==='9223372036854775807';
checks.receipt_first_balance_labeled=await p.locator('#receipt').textContent().then(t=>t.includes('최초 잔여'));
const again=await api('/admin/passes',firstCommand);
checks.replay_same_original_timestamp=JSON.stringify(again.body)===JSON.stringify(first);
await p.setViewportSize({width:390,height:844});
checks.mobile_390_long_snapshot=await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth);
stage='ack-loss';await selectMember();let saved,posts=0;
const write='**/api/v1/admin/passes';
p.on('request',r=>{if(r.method()==='POST'&&r.url().endsWith('/admin/passes'))posts++;});
await p.route(write,async route=>{saved=route.request().postDataJSON();const r=await route.fetch();if(r.status()!==200)throw Error();await route.abort('failed');});
await p.locator('#issue').click();await p.waitForFunction(()=>document.querySelector('#message').textContent.includes('불명확'));
checks.unknown_keeps_uuid_clears_pii=await p.locator('#operation').textContent().then(t=>t.includes(saved.operation_id))&&
await p.locator('#query').inputValue()===''&&await p.locator('#selection').textContent()===''&&await p.locator('#members').textContent()==='';
await p.unroute(write);await p.locator('#reconcile').click();await p.waitForFunction(()=>document.querySelector('#receipt').textContent.includes('발급 완료'));
checks.ack_receipt_recovery_without_new_post=posts===1;
stage='404-409';await selectMember();let unsubmitted;
await p.route(write,async route=>{unsubmitted=route.request().postDataJSON();await route.abort('failed');});
await p.locator('#issue').click();await p.waitForFunction(()=>document.querySelector('#message').textContent.includes('불명확'));await p.unroute(write);
const changed=await api('/admin/products/'+product,{operation_id:await uuid(),expected_product_version:1,name:'새 발급 조건',price_won:'1',session_count:'2',payment_type:'RATE',is_service:false});if(changed.status!==200)throw Error();
let retry;await p.route(write,async route=>{retry=route.request().postDataJSON();await route.continue();});
await p.locator('#reconcile').click();await p.waitForFunction(()=>document.querySelector('#message').textContent.includes('다시 검색'));await p.unroute(write);
checks.missing_receipt_stale_command_exact_retry=JSON.stringify(retry)===JSON.stringify(unsubmitted)&&await p.locator('#selection').textContent()===''&&await p.locator('#operation').textContent()==='';
await selectMember(members[0]);let fresh;
await p.route(write,async route=>{fresh=route.request().postDataJSON();await route.continue();});
await p.locator('#issue').click();await p.waitForFunction(()=>document.querySelector('#receipt').textContent.includes('발급 완료'));await p.unroute(write);
checks.fresh_selection_new_uuid_version=fresh.operation_id!==unsubmitted.operation_id&&fresh.expected_product_version===2;
stage='new-session';await selectMember();await p.route(write,route=>route.abort('failed'));
await p.locator('#issue').click();await p.waitForFunction(()=>document.querySelector('#message').textContent.includes('불명확'));await p.unroute(write);
const replacement=await context.newPage();await replacement.goto(cfg.origin+'/account');
await api('/auth/logout',{},replacement);await signin(replacement);
let stalePosts=0;p.on('request',r=>{if(r.method()==='POST'&&r.url().endsWith('/admin/passes'))stalePosts++;});
await p.locator('#reconcile').click();await p.waitForFunction(()=>document.querySelector('#message').textContent.includes('발급 범위가 변경'));
checks.same_actor_new_session_old_post_zero=stalePosts===0&&await p.locator('#query').inputValue()===''&&await p.locator('#receipt').textContent()==='';
stage='operator-ui';const issued=await api('/admin/operator-accounts',{login_id:'pass.operator',branch_id:b},replacement);if(issued.status!==201)throw Error();
const opContext=await browser.newContext({ignoreHTTPSErrors:false}),op=await opContext.newPage();
stage='operator-setup-page';await op.goto(issued.body.setup_link);
stage='operator-setup-password';await op.locator('#new-password').fill(cfg.branchPassword);
const complete=op.waitForResponse(r=>r.url().endsWith('/auth/operator-credentials/complete'));await op.locator('form button').click();if((await complete).status()!==204)throw Error();
stage='operator-signin';await signin(op,'pass.operator',cfg.branchPassword);
stage='operator-issue-page';await op.locator('#passes-link').click();
stage='operator-branch-attached';
await op.locator('#issued option[value="'+b+'"]').waitFor({state:'attached'});
checks.operator_menu_and_exact_issued_scope=await op.locator('#issued option').count()===2;
stage='operator-branch-select';await op.locator('#issued').selectOption(b);
stage='operator-choices-ready';await op.waitForFunction(()=>!document.querySelector('#search').disabled);
await op.locator('#query').fill('같은 이름');await op.locator('#search').click();await op.locator('#members button').filter({hasText:members[0]}).click();
await op.locator('#trainer').selectOption(trainer);await op.locator('#product').selectOption(product);await op.locator('#issue').click();
await op.waitForFunction(()=>document.querySelector('#receipt').textContent.includes('발급 완료'));
checks.operator_actual_cross_home_issue=await op.locator('#receipt').textContent().then(t=>t.includes('최초 잔여 2회'));
await opContext.close();
for(const key of required)if(checks[key]!==true)throw Error();
fs.writeFileSync(path.join(R,'browser-results.json'),JSON.stringify({checks,browser:browser.version()}));
}catch{console.error('WORKFORCE_BROWSER_FAILED stage='+stage);console.error('WORKFORCE_DIAGNOSTIC='+JSON.stringify(checks));process.exitCode=1;}
finally{for(const release of releases)release();if(browser)await browser.close();}})();
