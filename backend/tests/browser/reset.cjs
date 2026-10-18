'use strict';
module.exports=async function({api,login,master,other,ident,cfg,setStage}){
 const checks={};setStage('password-reset');
 const prior=(await other.context.cookies()).find(c=>c.name==='__Host-y3-auth');
 const keys=(await api(other.p,'/auth/passkeys')).body;
 const state=(await api(master.p,'/admin/accounts/'+ident+'/password-reset')).body;
 const issued=await api(master.p,'/admin/accounts/'+ident+'/password-reset',{
 expected_account_version:state.account_version,expected_generation:state.generation,identity_confirmed:true});
 checks.explicit_start=issued.status===201;
 checks.old_session_denied=(await other.context.request.get(cfg.origin+'/api/v1/auth/me',{
 headers:{Cookie:'__Host-y3-auth='+prior.value}})).status()===401;
 const raw=issued.body.reset_link.split('#token=')[1];let leak=false;
 other.p.on('request',r=>{if(r.url().includes(raw))leak=true;});
 await other.p.goto(issued.body.reset_link);
 checks.fragment_removed=await other.p.evaluate(()=>location.hash==='');
 const before=(await api(master.p,'/admin/accounts/'+ident+'/password-reset')).body;
 checks.get_nonmutating=before.password_reset_pending&&before.generation===state.generation+1;
 await other.p.locator('#password').fill(cfg.masterPassword);
 const done=other.p.waitForResponse(r=>r.url().endsWith('/auth/password-reset/complete'));
 await other.p.locator('#mfa button').click();checks.form_complete=(await done).status()===204;
 checks.no_auto_login=!(await other.context.cookies()).some(c=>c.name==='__Host-y3-auth')&&
 (await api(other.p,'/auth/me')).status===401;
 checks.url_private=!leak;
 checks.replay_denied=(await api(other.p,'/auth/password-reset/complete',{
 reset_token:raw,new_password:cfg.masterPassword})).status===401;
 checks.old_password_denied=(await api(other.p,'/auth/login',{
 login_id:'browser.master.two',password:cfg.branchPassword})).status===401;
 setStage('password-reset-existing-key-login');
 checks.existing_uv_key_login=(await login(other,cfg.masterPassword,'browser.master.two')).result.status===204;
 checks.keys_preserved=JSON.stringify((await api(other.p,'/auth/passkeys')).body)===JSON.stringify(keys);
 return checks;
};
