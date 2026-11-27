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
checks.member_menu=await p.locator('#members-link').getAttribute('href')==='/members';
stage='all-branch-candidates';for(let i=0;i<102;i++)await createBranch('MEM'+i);
const tail=(await api('/admin/member-branches?offset=100&limit=100')).body;if(tail.length!==2)throw Error();
await p.locator('#members-link').click();await ready();
checks.self_stylesheet_applied=await p.evaluate(()=>getComputedStyle(document.querySelector('#selection')).overflowWrap==='anywhere'&&
[...document.styleSheets].some(s=>s.href===location.origin+'/members.css'));
checks.beyond_100_branch_reachable=await p.locator('#home option[value="'+tail[0].id+'"]').count()===1;
await p.locator('#home').selectOption(tail[0].id);await fill('한'.repeat(200),'+82 10 2000 0000');
await p.locator('#save').click();await p.waitForFunction(()=>document.querySelector('#selection').textContent.includes('v1'));await ready();
const list=(await api('/admin/members')).body,first=list.items[0],id=first.id;
checks.actual_create_canonical=first.version===1&&first.home_branch_id===tail[0].id&&first.values.phone==='01020000000';
const dup=await api('/admin/members',{operation_id:await uuid(),home_branch_id:tail[0].id,name:first.values.name,phone:first.values.phone});
checks.duplicate_separate_uuid=dup.status===200&&dup.body.current_member.id!==id;
stage='inactive-edit';await p.locator('#deactivate').click();let inactive=await current(id,2);
checks.state_command_inactive=inactive.active===false;
await fill('X'.repeat(200));await p.locator('#save').click();const updated=await current(id,3);
checks.inactive_edit_preserves_state=updated.active===false&&await p.locator('#name').inputValue()==='X'.repeat(200);
await p.setViewportSize({width:390,height:844});
await p.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
checks.mobile_390_long_detail=await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth);
if(!checks.mobile_390_long_detail)geometry=await p.evaluate(()=>({width:innerWidth,scrollX,scroll:document.documentElement.scrollWidth,items:[...document.querySelectorAll('*')].filter(e=>e.scrollWidth>e.clientWidth+1||e.getBoundingClientRect().right+scrollX>innerWidth).map(e=>[e.tagName,e.id,e.clientWidth,e.scrollWidth,Math.round(e.getBoundingClientRect().width),getComputedStyle(e).overflowWrap,getComputedStyle(e).whiteSpace]).slice(0,14)}));
const refreshed=p.waitForResponse(r=>r.url().includes('/admin/members?'));
await p.locator('#refresh').click();await(await refreshed).finished();await p.waitForLoadState('networkidle');
await p.locator('#members button').first().waitFor();
checks.mobile_390_long_list=await p.locator('#members').textContent().then(x=>x.includes('X'.repeat(200)))&&
await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth);
stage='branch-admin';const issued=await api('/admin/accounts',{login_id:'member.branch',branch_id:tail[0].id});if(issued.status!==201)throw Error();
stage='ba-context';const branchContext=await browser.newContext({ignoreHTTPSErrors:false}),ba=await branchContext.newPage();
stage='ba-navigate';await ba.goto(issued.body.setup_link);stage='ba-password';await ba.locator('#password').fill(cfg.branchPassword);
const setup=ba.waitForResponse(r=>r.url().endsWith('/auth/credentials/complete'));
await ba.locator('#submit').click();if((await setup).status()!==204)throw Error();
stage='ba-activated';await signin(ba,'member.branch',cfg.branchPassword);stage='ba-signedin';await ba.locator('#members-link').click();
await ba.waitForFunction(()=>!document.querySelector('#save').matches(':disabled'));
await ba.locator('#home').selectOption(tail[0].id);await ba.locator('#name').fill('BA 실제 등록');await ba.locator('#phone').fill('01020000000');
stage='ba-form';await ba.locator('#save').click();await ba.waitForFunction(()=>document.querySelector('#selection').textContent.includes('v1'));
stage='ba-posted';await ba.waitForFunction(()=>!document.querySelector('#deactivate').hidden&&!document.querySelector('#deactivate').disabled);
checks.ba_create_immediate_state_button=await ba.locator('#deactivate').isVisible();
const hidden=await api('/admin/members',{operation_id:await uuid(),home_branch_id:tail[1].id,name:'다른 Home',phone:'01020000000'});
checks.ba_minimal_scope=(await api('/admin/members',undefined,ba)).body.total===3&&
(await api('/admin/members/'+hidden.body.current_member.id,undefined,ba)).status===404;
await branchContext.close();

for(const key of required)if(checks[key]!==true)throw Error();
fs.writeFileSync(path.join(R,'browser-results.json'),JSON.stringify({checks,browser:browser.version()}));
}catch{console.error('WORKFORCE_BROWSER_FAILED stage='+stage);console.error('WORKFORCE_DIAGNOSTIC='+JSON.stringify(checks));if(geometry)console.error('MEMBERSHIP_GEOMETRY='+JSON.stringify(geometry));process.exitCode=1;}
finally{for(const release of releases)release();if(browser)await browser.close();}})();
