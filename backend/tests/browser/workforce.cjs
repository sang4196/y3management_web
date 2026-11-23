'use strict';
const fs=require('fs'),path=require('path'),R=process.env.Y3_BROWSER_RUN;
const checks={},required=JSON.parse(fs.readFileSync(path.join(R,'required-checks.json')));
let stage='start';
(async()=>{let browser;try{
const {chromium}=require(path.join(R,'playwright-core'));
const cfg=JSON.parse(fs.readFileSync(path.join(R,'input.json')));
browser=await chromium.launch({executablePath:path.join(R,'browser-binaries/chrome'),
headless:true,chromiumSandbox:true,args:['--no-proxy-server','--disable-background-networking']});
async function device(){const context=await browser.newContext({ignoreHTTPSErrors:false});
const page=await context.newPage();return {context,page};}
const master=await device(),p=master.page;
async function submit(page,endpoint){const response=page.waitForResponse(r=>r.url().endsWith(endpoint));
await page.locator('#password-form button').click();return (await response).status();}
async function login(page,id,password){await page.goto(cfg.origin+'/login');
await page.locator('#identifier').fill(id);await page.locator('#password').fill(password);
return await submit(page,'/auth/login');}
async function get(page,route){return page.evaluate(async route=>{const r=await fetch('/api/v1'+route);
return {status:r.status,body:await r.json()};},route);}
async function post(page,route,body){return page.evaluate(async({route,body})=>{
const c=await(await fetch('/api/v1/auth/csrf',{headers:{'X-Y3-Client':'browser'}})).json();
const r=await fetch('/api/v1'+route,{method:'POST',headers:{'Content-Type':'application/json',
'X-CSRF-Token':c.csrf_token},body:JSON.stringify(body)});
return {status:r.status,body:await r.json()};},{route,body});}
stage='setup';await p.goto(cfg.origin+'/login');
checks.trusted_https=await p.evaluate(()=>isSecureContext);
checks.actual_master_login=await login(p,'master.test',cfg.masterPassword)===204;
stage='branches';
for(let i=0;i<101;i++){const b=await post(p,'/admin/branches',{code:'W'+i,name:'가상지점 '+i});
if(b.status!==201)throw Error();}
const first=(await get(p,'/admin/trainer-home-candidates?limit=100')).body.items;
const later=(await get(p,'/admin/trainer-home-candidates?limit=100&offset=100')).body.items;
if(later.length!==1)throw Error();const home=later[0].id;
stage='mobile';await p.setViewportSize({width:390,height:844});await p.goto(cfg.origin+'/trainers');
await p.locator('#submit').waitFor();await p.waitForFunction(()=>!document.getElementById('submit').disabled);
checks.mobile_no_overflow=await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth);
checks.mobile_input_width=await p.locator('#name').evaluate(e=>e.getBoundingClientRect().width>200);
checks.later_candidate_loaded=await p.locator('#home_branch_id option').count()===102;
checks.explicit_empty_values=await p.locator('#fixed_amount_won').inputValue()===''&&
await p.locator('#base_salary_won').inputValue()===''&&await p.locator('#base_salary_start_month').inputValue()==='';
await p.locator('#name').fill('가상브라우저트레이너');await p.locator('#phone').fill('+99 000 example');
await p.locator('#home_branch_id').selectOption(home);await p.locator('#rate_percent').fill('0');
await p.locator('#fixed_amount_won').fill('0');await p.locator('#base_salary_won').fill('9'.repeat(1024));
await p.locator('#base_salary_start_month').fill('9999-12');
let submitted;
p.on('request',r=>{if(r.url().endsWith('/api/v1/admin/trainers')&&r.method()==='POST'&&!submitted)submitted=r.postDataJSON();});
const response=p.waitForResponse(r=>r.url().endsWith('/api/v1/admin/trainers')&&r.request().method()==='POST');
await p.locator('#submit').click();const created=await response;const data=await created.json();
checks.actual_form_registration=created.status()===201;
checks.later_candidate_registered=data.trainer.home_branch_id===home&&!first.some(x=>x.id===home);
checks.exact_money_string=typeof submitted.base_salary_won==='string'&&submitted.base_salary_won==='9'.repeat(1024)&&submitted.fixed_amount_won==='0';
checks.explicit_future_month=submitted.base_salary_start_month==='9999-12';
checks.minimal_response=Object.keys(data.trainer).sort().join(',')==='active,home_branch_id,id,name,version';
checks.authorized_replay=(await post(p,'/admin/trainers',submitted)).status===200;
checks.conflict=(await post(p,'/admin/trainers',{...submitted,name:'다른값'})).status===409;
const bad=await post(p,'/admin/trainers',{...submitted,phone:{private:'marker'}});
checks.validation_no_echo=bad.status===422&&JSON.stringify(bad.body)==='{"detail":"invalid_request"}';
stage='branch-admin';const issued=await post(p,'/admin/accounts',{login_id:'workforce.branch',branch_id:home});
const ba=await device(),b=ba.page;await b.goto(issued.body.setup_link);
await b.locator('#password').fill(cfg.branchPassword);
const branchSetup=b.waitForResponse(r=>r.url().endsWith('/auth/credentials/complete'));
await b.locator('#submit').click();checks.branch_setup=(await branchSetup).status()===204;
checks.branch_login=await login(b,'workforce.branch',cfg.branchPassword)===204;
checks.branch_scope=(await get(b,'/admin/trainer-home-candidates')).body.items.length===1;
checks.foreign_home_denied=(await post(b,'/admin/trainers',{...submitted,operation_id:await b.evaluate(()=>crypto.randomUUID()),home_branch_id:first[0].id})).status===404;
checks.current_other_actor_replay=(await post(b,'/admin/trainers',submitted)).status===200;
stage='branch-form';await b.goto(cfg.origin+'/trainers');
await b.waitForFunction(()=>!document.getElementById('submit').disabled);
const baCommands=[];
b.on('request',r=>{if(r.url().endsWith('/api/v1/admin/trainers')&&r.method()==='POST')baCommands.push(r.postDataJSON());});
async function fillBranchForm(){await b.locator('#name').fill('가상지점등록');
await b.locator('#phone').fill('+99 000 example');await b.locator('#home_branch_id').selectOption(home);
await b.locator('#rate_percent').fill('100');await b.locator('#fixed_amount_won').fill('9007199254740993');
await b.locator('#base_salary_won').fill('0');await b.locator('#base_salary_start_month').fill('0001-01');}
await fillBranchForm();let baResponse=b.waitForResponse(r=>r.url().endsWith('/api/v1/admin/trainers')&&r.request().method()==='POST');
await b.locator('#submit').dblclick();let baResult=await baResponse;
checks.branch_actual_form=baResult.status()===201;
await b.waitForFunction(()=>document.getElementById('result').textContent.includes('계정 미발급'));
checks.double_click_one_operation=baCommands.length===1;
const baFirst=baCommands[0],baId=(await baResult.json()).trainer.id;
const statusResponse=b.waitForResponse(r=>r.url().includes('/admin/trainer-registrations/'));
await b.locator('#status').click();checks.actual_status_button=(await statusResponse).status()===200;
checks.branch_same_operation=(await post(b,'/admin/trainers',baFirst)).status===200;
await b.locator('#new').click();checks.explicit_new_clears=await b.locator('#base_salary_won').inputValue()==='';
await fillBranchForm();baResponse=b.waitForResponse(r=>r.url().endsWith('/api/v1/admin/trainers')&&r.request().method()==='POST');
await b.locator('#submit').click();baResult=await baResponse;
checks.explicit_new_operation=baResult.status()===201&&baCommands[baCommands.length-1].operation_id!==baFirst.operation_id&&(await baResult.json()).trainer.id!==baId;
stage='chunked';
const csrfValue=await p.evaluate(async()=>{const r=await fetch('/api/v1/auth/csrf',{headers:{'X-Y3-Client':'browser'}});return (await r.json()).csrf_token;});
const cookieValue=(await master.context.cookies()).map(c=>c.name+'='+c.value).join('; ');
async function chunked(size){const raw=Buffer.from(JSON.stringify(submitted));
const payload=Buffer.concat([raw,Buffer.alloc(size-raw.length,32)]);
return new Promise((resolve,reject)=>{const req=require('https').request(cfg.origin+'/api/v1/admin/trainers',
{method:'POST',ca:fs.readFileSync(path.join(R,'ca.crt')),headers:{'Content-Type':'application/json',
'Origin':cfg.origin,'X-CSRF-Token':csrfValue,'Cookie':cookieValue,'Transfer-Encoding':'chunked'}},res=>{
res.resume();res.on('end',()=>resolve(res.statusCode));});req.on('error',reject);
req.write(payload.subarray(0,3000));setTimeout(()=>{req.write(payload.subarray(3000,6000));
setTimeout(()=>req.end(payload.subarray(6000)),10);},10);});}
checks.actual_chunked_8192=(await chunked(8192))===200;
checks.actual_chunked_8193=(await chunked(8193))===413;
stage='home-move';await p.goto(cfg.origin+'/trainers');
const homeBox=p.locator('[data-home-trainer="'+data.trainer.id+'"]');
await homeBox.locator('[data-home-change]').waitFor();
await p.waitForFunction(id=>!document.querySelector('[data-home-trainer="'+id+'"] [data-home-change]').disabled,
 data.trainer.id);
await homeBox.locator('[data-home-destination]').selectOption(first[0].id);
let homeWrites=0;p.on('request',r=>{if(r.url().endsWith('/'+data.trainer.id+'/home')&&
 r.method()==='POST')homeWrites++;});
const moved=p.waitForResponse(r=>r.url().endsWith('/'+data.trainer.id+'/home'));
await homeBox.locator('[data-home-change]').dblclick();const moveResponse=await moved;
const homeReceipt=await moveResponse.json();
checks.home_master_ui_move=moveResponse.status()===200&&homeReceipt.changed&&
 homeReceipt.current_state.home_branch_id===first[0].id;
checks.home_double_click_one=homeWrites===1;
await p.waitForFunction(id=>document.querySelector('[data-home-trainer="'+id+'"] [data-home-result]')
 .textContent.includes('소속 변경 완료'),data.trainer.id);
checks.home_old_admin_denied=(await get(b,'/admin/trainers/'+data.trainer.id)).status===404;
checks.home_current_registration=(await post(p,'/admin/trainers',submitted)).body.trainer.home_branch_id===first[0].id;
await homeBox.locator('[data-home-refresh]').click();
await p.waitForFunction(id=>!document.querySelector('[data-home-trainer="'+id+'"] [data-home-change]').disabled,
 data.trainer.id);
await homeBox.locator('[data-home-destination]').selectOption(home);
let homeAck=false;await p.route('**/api/v1/admin/trainers/'+data.trainer.id+'/home',async route=>{
 const response=await route.fetch();homeAck=response.status()===200;await route.abort();});
await homeBox.locator('[data-home-change]').click();
await p.waitForFunction(id=>document.querySelector('[data-home-trainer="'+id+'"] [data-home-result]')
 .textContent.includes('불명확'),data.trainer.id);
await p.unroute('**/api/v1/admin/trainers/'+data.trainer.id+'/home');
await homeBox.locator('[data-home-check]').click();
await p.waitForFunction(id=>document.querySelector('[data-home-trainer="'+id+'"] [data-home-result]')
 .textContent.includes('작업 당시 소속'),data.trainer.id);
checks.home_ack_reconciled=homeAck&&(await get(p,'/admin/trainers/'+data.trainer.id)).body.home_branch_id===home;
await homeBox.locator('[data-home-operation]').fill(homeReceipt.operation_id);
await homeBox.locator('[data-home-check]').click();
await p.waitForFunction(({id,home})=>document.querySelector('[data-home-trainer="'+id+'"] [data-home-result]')
 .textContent.includes('현재 소속: '),{id:data.trainer.id,home});
checks.home_receipt_keeps_current=(await get(p,'/admin/trainers/'+data.trainer.id)).body.home_branch_id===home;
stage='home-stale-response';
await p.waitForFunction(id=>!document.querySelector('[data-home-trainer="'+id+'"] [data-home-refresh]').disabled,
 data.trainer.id,{timeout:5000});
let capturedResolve,releaseResolve;
const captured=new Promise(resolve=>{capturedResolve=resolve;});
const releaseOld=new Promise(resolve=>{releaseResolve=resolve;});let delayed=false;
await p.route('**/api/v1/admin/trainers/'+data.trainer.id,async route=>{
 if(!delayed&&route.request().method()==='GET'){delayed=true;
  const response=await route.fetch();capturedResolve();await releaseOld;
  await route.fulfill({response});}else await route.continue();});
await homeBox.locator('[data-home-refresh]').click();stage='home-stale-capture';
await Promise.race([captured,new Promise((_,reject)=>setTimeout(()=>reject(Error()),5000))]);
stage='home-stale-external';
const owner=(await get(p,'/auth/me')).body.account_id;
const externalMove=await p.evaluate(async({id,dest,owner})=>{
 const current=await(await fetch('/api/v1/admin/trainers/'+id)).json();
 const csrf=await(await fetch('/api/v1/auth/csrf',{headers:{'X-Y3-Client':'browser-home'}})).json();
 const r=await fetch('/api/v1/admin/trainers/'+id+'/home',{method:'POST',
 headers:{'Content-Type':'application/json','X-CSRF-Token':csrf.csrf_token,'X-Y3-Expected-Actor':owner},
 body:JSON.stringify({operation_id:crypto.randomUUID(),destination_home_branch_id:dest,
 expected_trainer_version:current.version})});return r.status;
},{id:data.trainer.id,dest:first[0].id,owner});
stage='home-stale-state';const row=homeBox.locator('..');
await row.getByRole('button',{name:'새 상태 작업',exact:true}).click();
await p.waitForFunction(id=>document.querySelector('[data-state-trainer="'+id+'"] button')
 .disabled===false,data.trainer.id,{timeout:5000});
stage='home-stale-release';releaseResolve();
await p.waitForFunction(id=>document.querySelector('[data-home-trainer="'+id+'"] p')
 .textContent.includes('소속 정보가 변경'),data.trainer.id,{timeout:5000});
stage='home-stale-assert';const staleWrites=homeWrites;
checks.home_stale_response_blocked=externalMove===200&&
 await homeBox.locator('[data-home-change]').isDisabled()&&homeWrites===staleWrites;
await p.unroute('**/api/v1/admin/trainers/'+data.trainer.id);
await homeBox.locator('[data-home-refresh]').click();
await p.waitForFunction(id=>!document.querySelector('[data-home-trainer="'+id+'"] [data-home-change]').disabled,
 data.trainer.id);
checks.home_branch_name_display=!(await homeBox.locator('p').first().textContent()).includes(first[0].id);
const ownerCookies=await master.context.cookies();await master.context.clearCookies();
await master.context.addCookies(await ba.context.cookies());const writesBeforeActor=homeWrites;
await homeBox.locator('[data-home-refresh]').click();
await p.waitForFunction(id=>document.querySelector('[data-home-trainer="'+id+'"] [data-home-result]')
 .textContent.includes('확인할 수 없습니다'),data.trainer.id);
checks.home_actor_switch_blocks=homeWrites===writesBeforeActor&&await homeBox.locator('[data-home-change]').isDisabled();
await master.context.clearCookies();await master.context.addCookies(ownerCookies);
stage='nojs';const off=await browser.newContext({javaScriptEnabled:false,ignoreHTTPSErrors:false});
await off.addCookies(await master.context.cookies());const n=await off.newPage();let leaked=false;
n.on('request',r=>{if(['private-marker','phone-marker','amount-marker'].some(x=>r.url().includes(x)))leaked=true;});
await n.goto(cfg.origin+'/trainers');checks.nojs_disabled=await n.locator('#submit').isDisabled()&&await n.locator('#name').isDisabled();
checks.nojs_post_method=await n.locator('#trainer-form').getAttribute('method')==='post';
await n.evaluate(()=>{for(const [id,value] of [['name','private-marker'],['phone','phone-marker'],['base_salary_won','amount-marker']])document.getElementById(id).value=value;HTMLFormElement.prototype.submit.call(document.getElementById('trainer-form'));});
await n.waitForLoadState();checks.nojs_no_query_leak=!leaked&&!n.url().includes('?');
checks.actor_preserved=(await get(p,'/auth/me')).status===200;
if(Object.keys(checks).length!==required.length||!required.every(k=>checks[k]===true))throw Error();
fs.writeFileSync(path.join(R,'browser-results.json'),JSON.stringify({checks,browser:browser.version()}));
}catch{process.stderr.write('WORKFORCE_BROWSER_FAILED stage='+stage+'\n');
process.stderr.write('WORKFORCE_DIAGNOSTIC='+JSON.stringify(checks)+'\n');process.exitCode=1;}
finally{if(browser)await browser.close();}})();
