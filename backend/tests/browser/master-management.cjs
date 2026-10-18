'use strict';
module.exports=async function({api,master,other,ident,cfg,setStage}){
 const checks={};setStage('master-management');
 const root='/admin/master-accounts/'+ident;
 async function change(operation,body){return master.p.evaluate(async({url,operation,body})=>{
  const headers={'X-Y3-Client':'mfa-browser','Content-Type':'application/json'};
  headers['X-CSRF-Token']=(await(await fetch('/api/v1/auth/csrf',{headers})).json()).csrf_token;
  const r=await fetch('/api/v1'+url+'/'+operation,{method:operation==='restore'?'POST':'PATCH',headers,body:JSON.stringify(body)});
  return {status:r.status,body:await r.json()};
 },{url:root,operation,body});}
 async function relogin(id,old){
  const retained=(await other.context.cookies()).some(c=>c.name==='__Host-y3-auth'&&c.value===old.value);
  await other.p.goto(cfg.origin+'/login');
  await other.p.locator('#identifier').fill(id);
  await other.p.locator('#password').fill(cfg.masterPassword);
  const csrfRequest=other.p.waitForRequest(r=>r.url().endsWith('/auth/csrf'));
  const csrfResponse=other.p.waitForResponse(r=>r.url().endsWith('/auth/csrf'));
  const passwordResponse=other.p.waitForResponse(r=>r.url().endsWith('/auth/login'));
  const uvResponse=other.p.waitForResponse(r=>r.url().endsWith('/auth/login/passkey/verify'));
  await other.p.locator('#mfa button').click();
  const sent=(await(await csrfRequest).allHeaders()).cookie||'';
  const csrfStatus=(await csrfResponse).status(),passwordStatus=(await passwordResponse).status();
  const uvStatus=(await uvResponse).status();
  const fresh=(await other.context.cookies()).find(c=>c.name==='__Host-y3-auth');
  return retained&&sent.includes('__Host-y3-auth='+old.value)&&csrfStatus===200&&passwordStatus===200&&
   uvStatus===204&&!!fresh&&fresh.value!==old.value&&(await api(other.p,'/auth/me')).status===200;
 }
 const initial=(await api(master.p,root)).body;
 const keys=(await api(other.p,'/auth/passkeys')).body;
 const prior=(await other.context.cookies()).find(c=>c.name==='__Host-y3-auth');
 const disabled=await change('status',{expected_version:initial.version,status:'DISABLED'});
 checks.disable=disabled.status===200&&disabled.body.state==='DISABLED';
 checks.old_cookie_disabled=(await other.context.request.get(cfg.origin+'/api/v1/auth/me',{
 headers:{Cookie:'__Host-y3-auth='+prior.value}})).status()===401;
 const restored=await change('restore',{expected_version:disabled.body.version});
 checks.restore=restored.status===200&&restored.body.state==='ACTIVE';
 checks.old_cookie_not_revived=(await other.context.request.get(cfg.origin+'/api/v1/auth/me',{
 headers:{Cookie:'__Host-y3-auth='+prior.value}})).status()===401;
 checks.original_factors_login=await relogin('browser.master.two',prior);
 const active=(await other.context.cookies()).find(c=>c.name==='__Host-y3-auth');
 const same=await change('login-id',{expected_version:restored.body.version,login_id:'BROWSER.MASTER.TWO'});
 checks.normalized_noop=same.status===200&&same.body.version===restored.body.version&&(await api(other.p,'/auth/me')).status===200;
 const renamed=await change('login-id',{expected_version:same.body.version,login_id:'browser.master.renamed'});
 checks.rename=renamed.status===200&&renamed.body.login_id==='browser.master.renamed';
 checks.old_cookie_renamed=(await other.context.request.get(cfg.origin+'/api/v1/auth/me',{
 headers:{Cookie:'__Host-y3-auth='+active.value}})).status()===401;
 checks.old_id_denied=(await api(other.p,'/auth/login',{login_id:'browser.master.two',password:cfg.masterPassword})).status===401;
 checks.new_id_existing_uv_login=await relogin('browser.master.renamed',active);
 checks.keys_preserved=JSON.stringify((await api(other.p,'/auth/passkeys')).body)===JSON.stringify(keys);
 checks.actor_survives=(await api(master.p,'/auth/me')).status===200;
 return checks;
};
