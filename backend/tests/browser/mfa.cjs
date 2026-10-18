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
 const p=await context.newPage(),cdp=await context.newCDPSession(p);
 await cdp.send('WebAuthn.enable');const {authenticatorId}=await cdp.send('WebAuthn.addVirtualAuthenticator',
 {options:{protocol:'ctap2',transport:'internal',hasResidentKey:true,hasUserVerification:true,
 isUserVerified:true,automaticPresenceSimulation:true}});return {context,p,cdp,authenticatorId};}
 let master=await page();let leaked=false;
 master.p.on('request',r=>{if(r.url().includes(cfg.enrollmentToken))leaked=true;});
 await master.p.goto(cfg.origin+'/enroll#token='+cfg.enrollmentToken);
 checks.secure_context=await master.p.evaluate(()=>isSecureContext);
 checks.fragment_removed=await master.p.evaluate(()=>location.hash==='');
 const registered=master.p.waitForResponse(r=>r.url().endsWith('/auth/passkeys/enrollment/verify'));
 stage='first-enroll';await master.p.locator('#mfa button').click();
 checks.first_key_form=(await registered).status()===204;
 checks.fragment_absent_request_urls=!leaked;
 checks.no_auto_login=!(await master.context.cookies()).some(c=>c.name==='__Host-y3-auth');
 const first=(await master.cdp.send('WebAuthn.getCredentials',{authenticatorId:master.authenticatorId})).credentials[0];
 async function api(p,url,body,nonce){return p.evaluate(async({url,body,nonce})=>{
 const headers={'X-Y3-Client':'mfa-browser'};
 if(body!==undefined){headers['Content-Type']='application/json';headers['X-CSRF-Token']=nonce||
 (await(await fetch('/api/v1/auth/csrf',{headers})).json()).csrf_token;}
 const r=await fetch('/api/v1'+url,{method:body===undefined?'GET':'POST',headers,
 body:body===undefined?undefined:JSON.stringify(body)});
 return {status:r.status,body:r.status===204?null:await r.json()};},{url,body,nonce});}
 async function assertion(p,options,wanted,weak=false){return p.evaluate(async({options,wanted,weak})=>{
 const dec=s=>Uint8Array.from(atob(s.replace(/-/g,'+').replace(/_/g,'/')),c=>c.charCodeAt(0));
 const enc=b=>btoa(String.fromCharCode(...new Uint8Array(b))).replace(/\+/g,'-').replace(/\//g,'_').replace(/=/g,'');
 options.challenge=dec(options.challenge);
 if(wanted){const id=wanted.replace(/\+/g,'-').replace(/\//g,'_').replace(/=/g,'');
 options.allowCredentials=options.allowCredentials.filter(c=>c.id===id);}
 options.allowCredentials=options.allowCredentials.map(c=>({...c,id:dec(c.id)}));
 if(weak)options.userVerification='discouraged';
 const c=await navigator.credentials.get({publicKey:options});
 return {id:c.id,rawId:enc(c.rawId),type:c.type,response:{clientDataJSON:enc(c.response.clientDataJSON),
 authenticatorData:enc(c.response.authenticatorData),signature:enc(c.response.signature),
 ...(c.response.userHandle?{userHandle:enc(c.response.userHandle)}:{})}};},{options,wanted,weak});}
 async function login(who,password,id,wanted){const r=await api(who.p,'/auth/login',{login_id:id,password});
 if(r.status!==200)throw Error();
 checks.password_stage_no_auth=(checks.password_stage_no_auth??true)&&!(await who.context.cookies()).some(c=>c.name==='__Host-y3-auth')&&
 (await api(who.p,'/auth/me')).status===401;
 const credential=await assertion(who.p,r.body.publicKey,wanted);
 const result=await api(who.p,'/auth/login/passkey/verify',{credential},r.body.csrf_token);
 return {result,credential,nonce:r.body.csrf_token};}
 stage='first-login';let logged=await login(master,cfg.masterPassword,'master.test',first.credentialId);
 checks.first_key_login=logged.result.status===204;
 const cookie=(await master.context.cookies()).find(c=>c.name==='__Host-y3-auth');
 checks.cookie_flags=!!cookie&&cookie.secure&&cookie.httpOnly&&cookie.sameSite==='Lax'&&cookie.path==='/';
 checks.cookie_js_hidden=await master.p.evaluate(()=>!document.cookie.includes('__Host-y3'));
 checks.assertion_replay_denied=(await api(master.p,'/auth/login/passkey/verify',
 {credential:logged.credential},logged.nonce)).status===401;
 stage='add';const additional=await page();
 await additional.context.addCookies(await master.context.cookies());
 await master.context.clearCookies();master=additional;
 await master.p.goto(cfg.origin+'/passkeys');
 const added=master.p.waitForResponse(r=>r.url().endsWith('/auth/passkeys/verify'));
 await master.p.locator('#mfa button').click();checks.additional_key_form=(await added).status()===204;
 const second=(await master.cdp.send('WebAuthn.getCredentials',{authenticatorId:master.authenticatorId})).credentials
 .find(c=>c.credentialId!==first.credentialId);
 await api(master.p,'/auth/logout',{});
 stage='second-login';logged=await login(master,cfg.masterPassword,'master.test',second.credentialId);
 checks.second_key_login=logged.result.status===204;
 const a=await api(master.p,'/admin/branches',{code:'A',name:'A'});
 const b=await api(master.p,'/admin/branches',{code:'B',name:'B'});
 const issued=await api(master.p,'/admin/accounts',{login_id:'browser.branch',branch_id:a.body.id});
 checks.actual_issuance=issued.status===201;
 const branch=await page();await branch.p.goto(issued.body.setup_link);
 stage='branch-setup';await branch.p.locator('#password').fill(cfg.branchPassword);
 const completed=branch.p.waitForResponse(r=>r.url().endsWith('/auth/passkeys/enrollment/verify'));
 await branch.p.locator('button').click();checks.branch_setup_form=(await completed).status()===204;
 const branchKey=(await branch.cdp.send('WebAuthn.getCredentials',{authenticatorId:branch.authenticatorId})).credentials[0];
 stage='branch-login';logged=await login(branch,cfg.branchPassword,'browser.branch',branchKey.credentialId);
 checks.branch_login=logged.result.status===204;
 checks.scope_enforced=(await api(branch.p,'/branches')).body.total===1&&
 (await api(branch.p,'/branches/'+b.body.id)).status===404;
 checks.missing_csrf_denied=(await branch.context.request.post(cfg.origin+'/api/v1/auth/passkeys/options',
 {headers:{Origin:cfg.origin},data:{}})).status()===403;
 checks.forged_origin_denied=(await branch.context.request.post(cfg.origin+'/api/v1/auth/passkeys/options',
 {headers:{Origin:'https://other.invalid'},data:{}})).status()===403;
 const saved=(await branch.context.cookies()).find(c=>c.name==='__Host-y3-auth');
 await api(branch.p,'/auth/logout',{});
 checks.logout_reuse_denied=(await branch.context.request.get(cfg.origin+'/api/v1/auth/me',
 {headers:{Cookie:'__Host-y3-auth='+saved.value}})).status()===401;
 let reset;stage='management';const management=await require(path.join(R,'management.cjs'))({page,api,login,master,branch,branchKey,second,cfg,setStage:s=>{stage=s;},onReset:async actors=>{reset=await require(path.join(R,'reset.cjs'))({...actors,api,login,cfg,setStage:s=>{stage=s;}});}});
 stage='uv-negative';const options=await api(branch.p,'/auth/login',
 {login_id:'browser.branch',password:cfg.branchPassword});
 await branch.cdp.send('WebAuthn.setUserVerified',{authenticatorId:branch.authenticatorId,isUserVerified:false});
 const weak=await assertion(branch.p,options.body.publicKey,undefined,true);
 checks.uv_false_denied=(await api(branch.p,'/auth/login/passkey/verify',{credential:weak},
 options.body.csrf_token)).status===401;
 fs.writeFileSync(path.join(R,'browser-results.json'),JSON.stringify({checks,management,reset,browser:browser.version()}));
 const rr=JSON.parse(fs.readFileSync(path.join(R,'reset-checks.json')));
 if(Object.keys(reset).length!==rr.length||rr.some(k=>reset[k]!==true))throw Error();
 const mr=JSON.parse(fs.readFileSync(path.join(R,'management-checks.json')));
 if(Object.keys(management).length!==mr.length||mr.some(k=>management[k]!==true))throw Error();
 if(Object.keys(checks).length!==required.length||required.some(k=>checks[k]!==true))throw Error();
 }catch{console.error('MFA_BROWSER_FAILED stage='+stage);process.exitCode=1;}
 finally{if(browser)await browser.close();}})();
