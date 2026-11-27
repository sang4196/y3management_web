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
const a=await createBranch('HOME-A'),b=await createBranch('HOME-B');
async function member(name){const original={operation_id:await uuid(),home_branch_id:a,name,phone:'01020000000'};
const made=await api('/admin/members',original);if(made.status!==200)throw Error();
const id=made.body.current_member.id;
if((await api('/admin/members/'+id+'/deactivate',{operation_id:await uuid(),expected_member_version:1})).status!==200)throw Error();
return {id,original};}
const first=await member('이동할 비활성 회원'),second=await member('ACK 유실 회원');
const issued=await api('/admin/accounts',{login_id:'member.home.ba',branch_id:a});if(issued.status!==201)throw Error();
const baContext=await browser.newContext({ignoreHTTPSErrors:false}),ba=await baContext.newPage();
await ba.goto(issued.body.setup_link);await ba.locator('#password').fill(cfg.branchPassword);
const setup=ba.waitForResponse(r=>r.url().endsWith('/auth/credentials/complete'));
await ba.locator('#submit').click();if((await setup).status()!==204)throw Error();
await signin(ba,'member.home.ba',cfg.branchPassword);await ba.locator('#members-link').click();
await ba.locator('#members button').filter({hasText:'이동할 비활성 회원'}).click();
await ba.waitForFunction(()=>!document.querySelector('#move-home-save').disabled);
checks.ba_move_candidates_without_assignment_scope_expansion=await ba.locator('#move-home option[value="'+b+'"]').count()===1&&
(await api('/admin/member-branches',undefined,ba)).body.every(x=>x.id===a);
await ba.setViewportSize({width:390,height:844});
checks.mobile_390=await ba.evaluate(()=>document.documentElement.scrollWidth<=innerWidth);
await ba.locator('#move-home').selectOption(b);
const normal=ba.waitForResponse(r=>r.url().endsWith('/members/'+first.id+'/home')&&r.request().method()==='POST');
await ba.locator('#move-home-save').click();const response=await normal,ack=await response.json();
await ba.waitForFunction(()=>document.querySelector('#message').textContent.includes('소속 지점을 변경했습니다'));
checks.source_ba_minimal_ack=response.status()===200&&ack.changed===true&&ack.committed_member_version===3&&
Object.keys(ack).sort().join(',')==='changed,committed_member_version,kind,member_id,operation_id';
checks.source_ba_pii_cleared=await ba.locator('#name').inputValue()===''&&await ba.locator('#phone').inputValue()===''&&
await ba.locator('#selection').textContent()===''&&await ba.locator('#members button').filter({hasText:'이동할 비활성 회원'}).count()===0;
const actual=(await api('/admin/members/'+first.id)).body;
checks.inactive_state_values_preserved=actual.active===false&&actual.version===3&&actual.home_branch_id===b&&actual.values.name==='이동할 비활성 회원';
checks.source_receipt404_other_actor404=(await api('/admin/member-home-operations/'+ack.operation_id,undefined,ba)).status===404&&
(await api('/admin/member-home-operations/'+ack.operation_id)).status===404;
const old=(await api('/admin/member-operations/'+first.original.operation_id)).body;
checks.old_receipt_home_metadata_not_mislabeled=old.committed_member.home_branch_id===a&&old.committed_member.home_branch_name===null&&
old.committed_member.home_active===null&&old.current_member.home_branch_id===b;
stage='ack-loss';await ba.locator('#members button').filter({hasText:'ACK 유실 회원'}).click();
await ba.waitForFunction(()=>!document.querySelector('#move-home-save').disabled);
await ba.locator('#move-home').selectOption(b);let original,posts=0,retry;
const write='**/api/v1/admin/members/'+second.id+'/home';
const countPosts=r=>{if(r.method()==='POST'&&r.url().endsWith('/members/'+second.id+'/home'))posts++;};ba.on('request',countPosts);
await ba.route(write,async route=>{original=route.request().postDataJSON();const r=await route.fetch();if(r.status()!==200)throw Error();await route.abort('failed');});
await ba.locator('#move-home-save').click();await ba.waitForFunction(()=>document.querySelector('#message').textContent.includes('확인되지'));
checks.ack_loss_clears_pii_keeps_uuid=await ba.locator('#operation').textContent().then(t=>t.includes(original.operation_id))&&
await ba.locator('#name').inputValue()===''&&await ba.locator('#phone').inputValue()==='';
await ba.unroute(write);await ba.route(write,async route=>{retry=route.request().postDataJSON();await route.continue();});
await ba.locator('#reconcile').click();await ba.waitForFunction(()=>document.querySelector('#message').textContent.includes('불명확'));
checks.receipt404_same_uuid_replay404_is_uncertain=JSON.stringify(retry)===JSON.stringify(original)&&posts===2&&
await ba.locator('#new').isDisabled()&&(await api('/admin/members/'+second.id)).body.version===3;
await ba.unroute(write);await ba.locator('#home-uncertain').click();
await ba.waitForFunction(()=>!document.querySelector('#new').disabled);
checks.explicit_uncertainty_ack_returns_to_current_work=await ba.locator('#message').textContent().then(t=>t.includes('결과는 불명'))&&
await ba.locator('#operation').textContent().then(t=>t.includes(original.operation_id))&&
await ba.locator('#name').inputValue()===''&&await ba.locator('#phone').inputValue()===''&&await ba.locator('#members').textContent()==='';
await ba.locator('#new').click();await ba.waitForFunction(()=>!document.querySelector('#save').matches(':disabled'));
checks.no_automatic_new_command=posts===2;ba.off('request',countPosts);await baContext.close();
stage='master-noop';await p.goto(cfg.origin+'/members');
await p.locator('#members button').filter({hasText:'이동할 비활성 회원'}).click();
await p.waitForFunction(()=>!document.querySelector('#move-home-save').disabled);
await p.locator('#move-home').selectOption(b);await p.locator('#move-home-save').click();
await p.waitForFunction(()=>document.querySelector('#message').textContent.includes('동일한 소속'));
checks.same_home_noop_message_and_version=(await api('/admin/members/'+first.id)).body.version===3;
stage='late-candidates';let release,seen,held=false;const gate=new Promise(r=>release=r),observed=new Promise(r=>seen=r);releases.push(release);
const candidatePattern='**/api/v1/admin/members/'+first.id+'/home-candidates?*';
await p.route(candidatePattern,async route=>{if(held){await route.continue();return;}held=true;const r=await route.fetch();seen();await gate;try{await route.fulfill({response:r});}catch{}});
await p.locator('#members button').filter({hasText:'이동할 비활성 회원'}).click();await observed;
const c=await createBranch('HOME-C');await p.locator('#members button').filter({hasText:'ACK 유실 회원'}).click();
await p.waitForFunction(()=>!document.querySelector('#move-home-save').disabled);
release();await p.waitForLoadState('networkidle');
checks.late_destination_candidates_do_not_overwrite_selection=await p.locator('#name').inputValue()==='ACK 유실 회원'&&
await p.locator('#move-home option[value="'+c+'"]').count()===1;
await p.unroute(candidatePattern);
for(const key of required)if(checks[key]!==true)throw Error();
fs.writeFileSync(path.join(R,'browser-results.json'),JSON.stringify({checks,browser:browser.version()}));
}catch{console.error('WORKFORCE_BROWSER_FAILED stage='+stage);console.error('WORKFORCE_DIAGNOSTIC='+JSON.stringify(checks));process.exitCode=1;}
finally{for(const release of releases)release();if(browser)await browser.close();}})();
