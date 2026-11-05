'use strict';
module.exports=async function({api,master,other,ident,cfg,setStage}){
 const checks={};setStage('master-management');
 const root='/admin/master-accounts/'+ident;
 async function change(operation,body){return master.p.evaluate(async({url,operation,body})=>{
  const headers={'X-Y3-Client':'password-browser','Content-Type':'application/json'};
  headers['X-CSRF-Token']=(await(await fetch('/api/v1/auth/csrf',{headers})).json()).csrf_token;
  const r=await fetch('/api/v1'+url+'/'+operation,{method:operation==='restore'?'POST':'PATCH',headers,body:JSON.stringify(body)});
  return {status:r.status,body:await r.json()};
 },{url:root,operation,body});}
 async function relogin(id,old){
  const retained=(await other.context.cookies()).some(c=>c.name==='__Host-y3-auth'&&c.value===old.value);
  await other.p.goto(cfg.origin+'/login');
  await other.p.locator('#identifier').fill(id);await other.p.locator('#password').fill(cfg.masterPassword);
  const csrfRequest=other.p.waitForRequest(r=>r.url().endsWith('/auth/csrf'));
  const csrfResponse=other.p.waitForResponse(r=>r.url().endsWith('/auth/csrf'));
  const passwordResponse=other.p.waitForResponse(r=>r.url().endsWith('/auth/login'));
  await other.p.locator('#password-form button').click();
  const sent=(await(await csrfRequest).allHeaders()).cookie||'';
  const csrfStatus=(await csrfResponse).status(),passwordStatus=(await passwordResponse).status();
  if(passwordStatus===204)await other.p.getByText('로그인되었습니다.',{exact:true}).waitFor();
  const fresh=(await other.context.cookies()).find(c=>c.name==='__Host-y3-auth');
  return retained&&sent.includes('__Host-y3-auth='+old.value)&&csrfStatus===200&&passwordStatus===204&&
   !!fresh&&fresh.value!==old.value&&(await api(other.p,'/auth/me')).status===200;
 }
 const initial=(await api(master.p,root)).body;
 const identity=(await api(other.p,'/auth/me')).body;
 const prior=(await other.context.cookies()).find(c=>c.name==='__Host-y3-auth');
 const disabled=await change('status',{expected_version:initial.version,status:'DISABLED'});
 checks.disable=disabled.status===200&&disabled.body.state==='DISABLED';
 checks.old_cookie_disabled=(await other.context.request.get(cfg.origin+'/api/v1/auth/me',{
 headers:{Cookie:'__Host-y3-auth='+prior.value}})).status()===401;
 const restored=await change('restore',{expected_version:disabled.body.version});
 checks.restore=restored.status===200&&restored.body.state==='ACTIVE';
 checks.old_cookie_not_revived=(await other.context.request.get(cfg.origin+'/api/v1/auth/me',{
 headers:{Cookie:'__Host-y3-auth='+prior.value}})).status()===401;
 checks.original_password_login=await relogin('browser.master.two',prior);
 const active=(await other.context.cookies()).find(c=>c.name==='__Host-y3-auth');
 const same=await change('login-id',{expected_version:restored.body.version,login_id:'BROWSER.MASTER.TWO'});
 checks.normalized_noop=same.status===200&&same.body.version===restored.body.version&&(await api(other.p,'/auth/me')).status===200;
 const renamed=await change('login-id',{expected_version:same.body.version,login_id:'browser.master.renamed'});
 checks.rename=renamed.status===200&&renamed.body.login_id==='browser.master.renamed';
 checks.old_cookie_renamed=(await other.context.request.get(cfg.origin+'/api/v1/auth/me',{
 headers:{Cookie:'__Host-y3-auth='+active.value}})).status()===401;
 checks.old_id_denied=(await api(other.p,'/auth/login',{login_id:'browser.master.two',password:cfg.masterPassword})).status===401;
 checks.new_id_existing_password_login=await relogin('browser.master.renamed',active);
 checks.identity_scope_preserved=JSON.stringify((await api(other.p,'/auth/me')).body)===JSON.stringify(identity)&&(await api(other.p,'/branches')).body.total===2;
 checks.actor_survives=(await api(master.p,'/auth/me')).status===200;
 setStage('lifecycle-ui');
 const pending=await api(master.p,'/admin/master-accounts',{login_id:'browser.lifecycle'});
 if(pending.status!==201)throw Error();
 const p=master.p,account=pending.body.account_id;
 await p.goto(cfg.origin+'/account-lifecycle');
 const state=p.locator('#state'),message=p.locator('#message'),secret=p.locator('#link');
 await p.locator('#identifier').fill('browser.lifecycle');
 await p.locator('#lookup button').click();
 await p.waitForFunction(()=>document.querySelector('#state').textContent.includes('PENDING_SETUP'));
 let issued=0;
 p.on('request',r=>{if(r.url().endsWith('/'+account+'/activation'))issued++;});
 // Deliver the real committed write, then drop only its acknowledgement.
 let posts=0;
 await p.route('**/admin/accounts/'+account+'/status',async route=>{
  posts++;await route.fetch();await route.abort();
 });
 await p.locator('#disable').evaluate(b=>{b.click();b.click();});
 await p.waitForFunction(()=>document.querySelector('#state').textContent.includes('복구 시'));
 checks.lifecycle_unknown_ack=posts===1&&(await message.textContent()).includes('확인할 수 없습니다');
 checks.lifecycle_pending_destination=(await state.textContent()).includes('복구 시 PENDING_SETUP');
 await p.locator('#restore').click();
 await p.waitForFunction(()=>!document.querySelector('#setup').disabled);
 checks.lifecycle_explicit_reissue=issued===0&&await secret.textContent()==='';
 await p.locator('#setup').click();
 await p.waitForFunction(()=>document.querySelector('#link').textContent.includes('#token='));
 await p.locator('#new-id').fill('browser.lifecycle.next');
 await p.locator('#rename').click();
 await p.waitForFunction(()=>document.querySelector('#state').textContent.includes('browser.lifecycle.next'));
 checks.lifecycle_rename_clears_link=issued===1&&await secret.textContent()==='';
 // A separate explicit reissue advances the target while the UI still holds its prior version.
 await p.unroute('**/admin/accounts/'+account+'/status');
 const latest=(await api(p,'/admin/account-lifecycle/'+account)).body;
 const conflict=await api(p,'/admin/master-accounts/'+account+'/activation',{expected_version:latest.version});
 if(conflict.status!==201)throw Error();
 let attempts=0;
 p.on('request',r=>{if(r.url().endsWith('/'+account+'/status'))attempts++;});
 await p.locator('#disable').click();
 await p.waitForFunction(()=>document.querySelector('#message').textContent.includes('다시 선택'));
 checks.lifecycle_stale_requires_retry=attempts===1&&await secret.textContent()===''&&
  (await state.textContent()).includes('PENDING_SETUP')&&!await p.locator('#disable').isDisabled();
 // A prior successful exact lookup arrives after a newer failed lookup.
 let received,release;
 const held=new Promise(resolve=>{received=resolve;});
 const resume=new Promise(resolve=>{release=resolve;});
 await p.route('**/account-lifecycle/lookup',async route=>{
  const response=await route.fetch();
  if(route.request().postDataJSON().login_id==='browser.lifecycle.next'){
   received();await resume;
  }
  await route.fulfill({response});
 });
 await p.locator('#identifier').fill('browser.lifecycle.next');await p.locator('#lookup button').click();
 await held;await p.locator('#identifier').fill('browser.lifecycle.missing');
 await p.locator('#lookup button').click();
 await p.waitForFunction(()=>document.querySelector('#message').textContent.includes('확인할 수 없습니다'));
 const late=p.waitForResponse(r=>r.url().endsWith('/account-lifecycle/lookup')&&r.status()===200);
 release();await (await late).finished();
 await p.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
 checks.lifecycle_late_lookup_ignored=await state.textContent()===''&&await secret.textContent()===''&&
  await p.locator('#rename').isDisabled();
 return checks;
};
