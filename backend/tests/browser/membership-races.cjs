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
stage='seed';const home=await createBranch('MEM-RACE');
const created=await api('/admin/members',{operation_id:await uuid(),home_branch_id:home,name:'가상 원본',phone:'01020000000'});
const id=created.body.current_member.id;await p.goto(cfg.origin+'/members');await ready();
await p.locator('#members button').first().click();await current(id,1);
stage='late-list';let releaseList,seenList,listHeld=false;
const listGate=new Promise(r=>releaseList=r),listSeen=new Promise(r=>seenList=r);releases.push(releaseList);
await p.route('**/api/v1/admin/members?*',async route=>{if(listHeld){await route.continue();return;}
listHeld=true;const response=await route.fetch();seenList();await listGate;try{await route.fulfill({response});}catch{}});
await p.locator('#refresh').click();await listSeen;
const newer=await api('/admin/members',{operation_id:await uuid(),home_branch_id:home,name:'늦은 목록 뒤 새 선택',phone:'01020000000'});
if(newer.status!==200)throw Error();await p.locator('#refresh').click();
await p.locator('#members button').filter({hasText:'늦은 목록 뒤 새 선택'}).click();
await p.waitForFunction(()=>document.querySelector('#name').value==='늦은 목록 뒤 새 선택');
releaseList();await p.waitForLoadState('networkidle');
checks.late_list_keeps_new_selection=await p.locator('#name').inputValue()==='늦은 목록 뒤 새 선택'&&
await p.locator('#members button').filter({hasText:'늦은 목록 뒤 새 선택'}).count()===1&&
(await p.locator('#page').textContent()).includes('2명');
await p.unroute('**/api/v1/admin/members?*');await p.locator('#members button').filter({hasText:'가상 원본'}).click();await current(id,1);
stage='late-detail';let releaseDetail,seenDetail,detailHeld=false;
const detailGate=new Promise(r=>releaseDetail=r),detailSeen=new Promise(r=>seenDetail=r);releases.push(releaseDetail);
await p.route('**/api/v1/admin/members/'+id,async route=>{if(detailHeld){await route.continue();return;}
detailHeld=true;const response=await route.fetch();seenDetail();await detailGate;try{await route.fulfill({response});}catch{}});
await p.locator('#members button').filter({hasText:'가상 원본'}).click();await detailSeen;
await p.locator('#members button').filter({hasText:'늦은 목록 뒤 새 선택'}).click();
await p.waitForFunction(()=>document.querySelector('#name').value==='늦은 목록 뒤 새 선택');
releaseDetail();await p.waitForLoadState('networkidle');
checks.late_detail_keeps_new_selection=await p.locator('#name').inputValue()==='늦은 목록 뒤 새 선택'&&
(await p.locator('#selection').textContent()).includes('늦은 목록 뒤 새 선택');
await p.unroute('**/api/v1/admin/members/'+id);await p.locator('#members button').filter({hasText:'가상 원본'}).click();await current(id,1);
stage='ack-loss';let original;const writePattern='**/api/v1/admin/members/'+id;
await p.route(writePattern,async route=>{if(route.request().method()!=='POST'){await route.continue();return;}
original=route.request().postDataJSON();const response=await route.fetch();if(response.status()!==200)throw Error();await route.abort('failed');});
await fill('ACK 유실');await p.locator('#save').click();
await p.waitForFunction(()=>document.querySelector('#message').textContent.includes('확인되지'));
checks.ack_unknown_uuid_preserved=await p.locator('#operation').textContent().then(x=>x.includes(original.operation_id))&&await p.locator('#new').isDisabled();
await p.unroute(writePattern);await p.locator('#reconcile').click();await current(id,2);
checks.ack_same_uuid_one_effect=(await api('/admin/members/'+id)).body.version===2&&
(await api('/admin/member-operations/'+original.operation_id)).body.committed_member.version===2;
stage='404-409';let unsubmitted;
await p.route(writePattern,async route=>{if(route.request().method()!=='POST'){await route.continue();return;}
unsubmitted=route.request().postDataJSON();await route.abort('failed');});
await fill('미전달 초안');await p.locator('#save').click();
await p.waitForFunction(()=>document.querySelector('#message').textContent.includes('확인되지'));
await p.unroute(writePattern);
const advanced=await api('/admin/members/'+id,{operation_id:await uuid(),expected_member_version:2,name:'외부 최신',phone:'01020000000'});if(advanced.status!==200)throw Error();
let retry;await p.route(writePattern,async route=>{if(route.request().method()==='POST')retry=route.request().postDataJSON();await route.continue();});
await p.locator('#reconcile').click();await current(id,3);await p.unroute(writePattern);
checks.receipt404_retry409_fresh=JSON.stringify(retry)===JSON.stringify(unsubmitted)&&await p.locator('#name').inputValue()==='외부 최신'&&await p.locator('#operation').textContent()==='';
let newCommand;const captureNew=r=>{if(r.method()==='POST'&&r.url().endsWith('/admin/members/'+id))newCommand=r.postDataJSON();};
p.on('request',captureNew);await fill('새 CAS');await p.locator('#save').click();await current(id,4);p.off('request',captureNew);
checks.fresh_new_uuid_recovers=newCommand.operation_id!==unsubmitted.operation_id&&newCommand.expected_member_version===3&&
(await api('/admin/members/'+id)).body.values.name==='새 CAS';
stage='same-account-relogin';await p.route(writePattern,async route=>{if(route.request().method()!=='POST'){await route.continue();return;}await route.abort('failed');});
await fill('옛 로그인 초안');await p.locator('#save').click();
await p.waitForFunction(()=>document.querySelector('#message').textContent.includes('확인되지'));await p.unroute(writePattern);
let release,seen,held=false;const gate=new Promise(r=>release=r),observed=new Promise(r=>seen=r);releases.push(release);
await p.route('**/api/v1/auth/me',async route=>{if(held){await route.continue();return;}held=true;const response=await route.fetch();seen();await gate;await route.fulfill({response});});
let oldPosts=0;p.on('request',r=>{if(r.method()==='POST'&&r.url().includes('/admin/members'))oldPosts++;});
await p.locator('#reconcile').click();await observed;
const same=await context.newPage();await same.goto(cfg.origin+'/account');
await api('/auth/logout',{},same);
await signin(same);release();
await p.waitForFunction(()=>document.querySelector('#message').textContent.includes('로그인 또는 관리 범위'));
await p.waitForLoadState('networkidle');
checks.same_actor_new_session_old_post_zero=oldPosts===0;
checks.same_actor_new_session_clears_personal_ui=await p.locator('#name').inputValue()===''&&await p.locator('#phone').inputValue()===''&&
await p.locator('#members').textContent()===''&&await p.locator('#selection').textContent()==='';
await p.unroute('**/api/v1/auth/me');await same.close();

for(const key of required)if(checks[key]!==true)throw Error();
fs.writeFileSync(path.join(R,'browser-results.json'),JSON.stringify({checks,browser:browser.version()}));
}catch{console.error('WORKFORCE_BROWSER_FAILED stage='+stage);console.error('WORKFORCE_DIAGNOSTIC='+JSON.stringify(checks));process.exitCode=1;}
finally{for(const release of releases)release();if(browser)await browser.close();}})();
