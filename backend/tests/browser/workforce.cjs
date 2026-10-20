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
const page=await context.newPage(),cdp=await context.newCDPSession(page);
await cdp.send('WebAuthn.enable');await cdp.send('WebAuthn.addVirtualAuthenticator',
{options:{protocol:'ctap2',transport:'internal',hasResidentKey:true,hasUserVerification:true,
isUserVerified:true,automaticPresenceSimulation:true}});return {context,page};}
const master=await device(),p=master.page;
async function submit(page,endpoint){const response=page.waitForResponse(r=>r.url().endsWith(endpoint));
await page.locator('#mfa button').click();return (await response).status();}
async function login(page,id,password){await page.goto(cfg.origin+'/login');
await page.locator('#identifier').fill(id);await page.locator('#password').fill(password);
return await submit(page,'/auth/login/passkey/verify');}
async function get(page,route){return page.evaluate(async route=>{const r=await fetch('/api/v1'+route);
return {status:r.status,body:await r.json()};},route);}
async function post(page,route,body){return page.evaluate(async({route,body})=>{
const c=await(await fetch('/api/v1/auth/csrf',{headers:{'X-Y3-Client':'browser'}})).json();
const r=await fetch('/api/v1'+route,{method:'POST',headers:{'Content-Type':'application/json',
'X-CSRF-Token':c.csrf_token},body:JSON.stringify(body)});
return {status:r.status,body:await r.json()};},{route,body});}
stage='setup';await p.goto(cfg.origin+'/enroll#token='+cfg.enrollmentToken);
checks.trusted_https=await p.evaluate(()=>isSecureContext);
checks.actual_master_setup=await submit(p,'/auth/passkeys/enrollment/verify')===204;
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
checks.branch_setup=await submit(b,'/auth/passkeys/enrollment/verify')===204;
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
