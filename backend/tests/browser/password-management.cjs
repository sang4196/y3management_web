'use strict';
const fs=require('fs'),path=require('path'),R=process.env.Y3_BROWSER_RUN;
const checks={},required=JSON.parse(fs.readFileSync(path.join(R,'required-checks.json')));
let stage='start';
(async()=>{let browser;try{
 const {chromium}=require(path.join(R,'playwright-core'));
 const cfg=JSON.parse(fs.readFileSync(path.join(R,'input.json')));
 browser=await chromium.launch({executablePath:path.join(R,'browser-binaries/chrome'),
 headless:true,chromiumSandbox:true,args:['--no-proxy-server','--disable-background-networking']});
 async function page(){const context=await browser.newContext({ignoreHTTPSErrors:false});
 return {context,p:await context.newPage()};}
 async function api(p,url,body,nonce){return p.evaluate(async({url,body,nonce})=>{
 const headers={'X-Y3-Client':'password-browser'};
 if(body!==undefined){const prep=await fetch('/api/v1/auth/csrf',{headers});
 if(!prep.ok)return {status:prep.status,body:null};
 headers['Content-Type']='application/json';headers['X-CSRF-Token']=nonce||(await prep.json()).csrf_token;}
 const r=await fetch('/api/v1'+url,{method:body===undefined?'GET':'POST',headers,
 body:body===undefined?undefined:JSON.stringify(body)});
 return {status:r.status,body:r.status===204?null:await r.json()};},{url,body,nonce});}
 async function login(who,password,id){await who.p.goto(cfg.origin+'/login');
 await who.p.locator('#identifier').fill(id);await who.p.locator('#password').fill(password);
 const response=who.p.waitForResponse(r=>r.url().endsWith('/auth/login')&&r.request().method()==='POST');
 await who.p.locator('#password-form button').click();const status=(await response).status();
 if(status===204)await who.p.getByText('로그인되었습니다.',{exact:true}).waitFor();
 return {status};}
 const master=await page();await master.p.goto(cfg.origin+'/login');
 checks.secure_context=await master.p.evaluate(()=>isSecureContext);
 stage='master-login';checks.master_password_form=(await login(master,cfg.masterPassword,'master.test')).status===204;
 const cookie=(await master.context.cookies()).find(c=>c.name==='__Host-y3-auth');
 checks.cookie_flags=!!cookie&&cookie.secure&&cookie.httpOnly&&cookie.sameSite==='Lax'&&cookie.path==='/'&&cookie.domain==='localhost';
 checks.cookie_js_hidden=await master.p.evaluate(()=>!document.cookie.includes('__Host-y3'));
 const a=await api(master.p,'/admin/branches',{code:'A',name:'A'});
 const b=await api(master.p,'/admin/branches',{code:'B',name:'B'});
 if(a.status!==201||b.status!==201)throw Error();
 const issued=await api(master.p,'/admin/accounts',{login_id:'browser.branch',branch_id:a.body.id});
 checks.actual_issuance=issued.status===201;
 const branch=await page(),raw=issued.body.setup_link.split('#token=')[1];let leaked=false;
 branch.p.on('request',r=>{if(r.url().includes(raw))leaked=true;});
 stage='branch-setup';await branch.p.goto(issued.body.setup_link);
 checks.fragment_removed=await branch.p.evaluate(()=>location.hash==='');
 checks.link_get_not_activated=(await api(master.p,'/admin/accounts/'+issued.body.account_id)).body.state==='PENDING_SETUP';
 await branch.p.locator('#password').fill(cfg.branchPassword);
 const completed=branch.p.waitForResponse(r=>r.url().endsWith('/auth/credentials/complete'));
 await branch.p.locator('#submit').click();checks.branch_setup_form=(await completed).status()===204;
 checks.no_auto_login=!(await branch.context.cookies()).some(c=>c.name==='__Host-y3-auth')&&(await api(branch.p,'/auth/me')).status===401;
 checks.fragment_absent_request_urls=!leaked;
 checks.branch_login=(await login(branch,cfg.branchPassword,'browser.branch')).status===204;
 checks.scope_enforced=(await api(branch.p,'/branches')).body.total===1&&(await api(branch.p,'/branches/'+b.body.id)).status===404;
 checks.missing_csrf_denied=(await branch.context.request.post(cfg.origin+'/api/v1/auth/logout',
 {headers:{Origin:cfg.origin},data:{}})).status()===403;
 const csrf=(await api(branch.p,'/auth/csrf')).body.csrf_token;
 checks.forged_origin_denied=(await branch.context.request.post(cfg.origin+'/api/v1/auth/logout',
 {headers:{Origin:'https://other.invalid','X-CSRF-Token':csrf},data:{}})).status()===403;
 const saved=(await branch.context.cookies()).find(c=>c.name==='__Host-y3-auth');
 await api(branch.p,'/auth/logout',{});
 checks.logout_reuse_denied=(await branch.context.request.get(cfg.origin+'/api/v1/auth/me',
 {headers:{Cookie:'__Host-y3-auth='+saved.value}})).status()===401;
 stage='management';const actors=await require(path.join(R,'management.cjs'))({page,api,login,master,branch,cfg,setStage:s=>{stage=s;}});
 const management=actors.checks;
 const reset=await require(path.join(R,'reset.cjs'))({...actors,page,api,login,cfg,setStage:s=>{stage=s;}});
 const masterManagement=await require(path.join(R,'master-management.cjs'))({...actors,api,login,cfg,setStage:s=>{stage=s;}});
 // Disabled JavaScript cannot submit credentials using the browser's default form action.
 const off=await browser.newContext({ignoreHTTPSErrors:false,javaScriptEnabled:false}),n=await off.newPage();
 let transmitted=false;n.on('request',r=>{if(r.method()==='POST'||(r.url().includes(cfg.branchPassword)||r.url().includes(encodeURIComponent(cfg.branchPassword))))transmitted=true;});
 checks.nojs_disabled=true;checks.nojs_post_fallback=true;
 for(const route of ['/login','/reset#token=synthetic-unusable','/emergency-recover#token=synthetic-unusable']){
 await n.goto(cfg.origin+route);await n.locator('#password').fill(cfg.branchPassword);
 await n.locator('#password').press('Enter');
 checks.nojs_disabled=checks.nojs_disabled&&await n.locator('form button').isDisabled();
 checks.nojs_post_fallback=checks.nojs_post_fallback&&await n.locator('form').getAttribute('method')==='post'&&await n.locator('form').getAttribute('action')===route.split('#')[0]&&await n.locator('#password').getAttribute('name')===null&&await n.locator('#identifier').getAttribute('name')===null;}
 checks.nojs_no_secret_submission=!transmitted;
 fs.writeFileSync(path.join(R,'browser-results.json'),JSON.stringify({checks,management,reset,masterManagement,browser:browser.version()}));
 for(const [value,names] of [[checks,required],...[['management',management],['reset',reset],['master-management',masterManagement]].map(([name,value])=>[value,JSON.parse(fs.readFileSync(path.join(R,name+'-checks.json')))])]){
 if(!names.length||Object.keys(value).length!==names.length||names.some(k=>value[k]!==true))throw Error();}
 }catch{console.error('PASSWORD_BROWSER_FAILED stage='+stage);process.exitCode=1;}
 finally{if(browser)await browser.close();}})();
