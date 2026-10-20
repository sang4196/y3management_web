'use strict';
const fs=require('fs'),path=require('path'),R=process.env.Y3_BROWSER_RUN;
const statuses=[],checks={},required=JSON.parse(fs.readFileSync(path.join(R,'required-checks.json')));
let stage='start';
(async()=>{let browser;try{
 const {chromium}=require(path.join(R,'playwright-core'));
 const cfg=JSON.parse(fs.readFileSync(path.join(R,'input.json')));
 browser=await chromium.launch({executablePath:path.join(R,'browser-binaries/chrome'),
 headless:true,chromiumSandbox:true,args:['--no-proxy-server','--disable-background-networking']});
 const context=await browser.newContext({ignoreHTTPSErrors:false}),p=await context.newPage();
 p.on('response',r=>{const route=new URL(r.url()).pathname;
 if(['/api/v1/auth/csrf','/api/v1/auth/emergency-recovery/inspect',
 '/api/v1/auth/emergency-recovery/options','/api/v1/auth/emergency-recovery/verify',
 '/api/v1/auth/emergency-recovery/password/complete'].includes(route))
 statuses.push({route,status:r.status()});});
 const cdp=await context.newCDPSession(p);await cdp.send('WebAuthn.enable');
 const {authenticatorId}=await cdp.send('WebAuthn.addVirtualAuthenticator',
 {options:{protocol:'ctap2',transport:'internal',hasResidentKey:true,hasUserVerification:true,
 isUserVerified:true,automaticPresenceSimulation:true}});
 let leaked=false;const tokens=[cfg.enrollmentToken];
 p.on('request',r=>{if(tokens.some(t=>r.url().includes(t)))leaked=true;});
 stage='enroll';await p.goto(cfg.origin+'/enroll#token='+cfg.enrollmentToken);
 checks.trusted_secure_context=await p.evaluate(()=>isSecureContext);
 let response=p.waitForResponse(r=>r.url().endsWith('/auth/passkeys/enrollment/verify'));
 await p.locator('#mfa button').click();checks.actual_initial_enrollment=(await response).status()===204;
 async function login(password){await p.goto(cfg.origin+'/login');
 await p.locator('#identifier').fill('master.test');await p.locator('#password').fill(password);
 const verified=p.waitForResponse(r=>r.url().endsWith('/auth/login/passkey/verify'));
 await p.locator('#mfa button').click();return (await verified).status()===204;}
 async function me(){return p.evaluate(async()=> (await fetch('/api/v1/auth/me')).status);}
 async function keyIds(){return (await cdp.send('WebAuthn.getCredentials',{authenticatorId})).credentials
 .map(k=>k.credentialId).sort().join(',');}
 stage='login';checks.actual_initial_login=await login(cfg.masterPassword);
 let currentPassword=cfg.masterPassword;checks.fragment_removed=true;checks.cookie_flags=true;
 for(const [index,factor] of ['password','passkey','both'].entries()){
 const old=(await context.cookies()).find(c=>c.name==='__Host-y3-auth')?.value;
 const oldKeys=await keyIds();
 fs.writeFileSync(path.join(R,'emergency-issue-ready-'+index),'ready',{mode:0o600});
 stage='operator';let deadline=Date.now()+70000;
 while(!fs.existsSync(path.join(R,'emergency-issued-ready-'+index))&&Date.now()<deadline)
 await new Promise(r=>setTimeout(r,100));
 if(!fs.existsSync(path.join(R,'emergency-issued-ready-'+index)))throw Error();
 const link=fs.readFileSync(path.join(R,'emergency-delivery-'+index),'utf8').trim();
 tokens.push(link.split('#token=')[1]);stage='recovery-'+factor;await p.goto(link);
 checks.fragment_removed=checks.fragment_removed&&await p.evaluate(()=>location.hash==='');
 checks[factor+'_target_session_revoked']=(await me())===401;
 checks[factor+'_stale_cookie_retained']=(await context.cookies()).find(c=>c.name==='__Host-y3-auth')?.value===old;
 if(factor!=='passkey'){
 currentPassword=cfg.branchPassword+'-'+index;await p.locator('#password').fill(currentPassword);}
 const endpoint=factor==='password'?'/auth/emergency-recovery/password/complete':'/auth/emergency-recovery/verify';
 response=p.waitForResponse(r=>r.url().endsWith(endpoint));
 await p.locator('#mfa button').click();checks[factor+'_completion_form']=(await response).status()===204;
 checks[factor+'_completion_no_auto_login']=(await me())===401;
 if(factor==='password')checks.password_keeps_existing_key=(await keyIds())===oldKeys;
 if(factor==='passkey')checks.passkey_keeps_existing_password=currentPassword===cfg.branchPassword+'-0';
 stage='relogin-'+factor;
 checks[factor+'_actual_relogin_password_uv']=await login(currentPassword)&&(await me())===200;
 const cookie=(await context.cookies()).find(c=>c.name==='__Host-y3-auth');
 checks.cookie_flags=checks.cookie_flags&&!!cookie&&cookie.value!==old&&cookie.secure&&cookie.httpOnly&&
 cookie.sameSite==='Lax'&&cookie.path==='/';}
 checks.no_token_request_url=!leaked;
 if(Object.keys(checks).length!==required.length||!required.every(k=>checks[k]===true))throw Error();
 fs.writeFileSync(path.join(R,'browser-results.json'),JSON.stringify({checks,browser:browser.version()}));
 }catch{process.stderr.write('MFA_BROWSER_FAILED stage='+stage+'\n');
 process.stderr.write('EMERGENCY_DIAGNOSTIC='+JSON.stringify({checks,statuses})+'\n');process.exitCode=1;}
 finally{if(browser)await browser.close();}})();
