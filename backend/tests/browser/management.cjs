'use strict';
module.exports=async function({page,api,login,master,branch,branchKey,second,cfg,setStage,onReset}){
 const checks={};
 const before=await api(master.p,'/auth/passkeys');
 checks.minimal_key_list=before.status===200&&before.body.items.length===2&&
 before.body.items.every(k=>Object.keys(k).sort().join(',')==='backed_up,created_at,device_type,key_id');
 const old=before.body.items.slice().sort((a,b)=>a.created_at.localeCompare(b.created_at)).at(-1);
 setStage('management-observer');
 const observer=await page();await observer.p.goto(cfg.origin+'/login');
 await observer.cdp.send('WebAuthn.addCredential',{authenticatorId:observer.authenticatorId,credential:(await master.cdp.send('WebAuthn.getCredentials',{authenticatorId:master.authenticatorId})).credentials.find(c=>c.credentialId===second.credentialId)});
 checks.second_browser_login=(await login(observer,cfg.masterPassword,'master.test',second.credentialId)).result.status===204;
 const oldCookies=await master.context.cookies(),observerCookies=await observer.context.cookies();
 setStage('management-add');const fresh=await page();
 await fresh.context.addCookies(await master.context.cookies());
 await master.context.clearCookies();master=fresh;
 await master.p.goto(cfg.origin+'/passkeys');
 const added=master.p.waitForResponse(r=>r.url().endsWith('/auth/passkeys/verify'));
 await master.p.locator('#mfa button').click();
 if((await added).status()!==204)throw Error();
 const third=(await master.cdp.send('WebAuthn.getCredentials',{authenticatorId:master.authenticatorId})).credentials
 .find(c=>c.credentialId!==second.credentialId);
 const snapshot=(await api(master.p,'/auth/passkeys')).body;
 setStage('management-delete');const deleted=await master.p.evaluate(async({old,version})=>{
 const csrf=(await(await fetch('/api/v1/auth/csrf',{headers:{'X-Y3-Client':'mfa'}})).json()).csrf_token;
 return (await fetch('/api/v1/auth/passkeys/'+old,{method:'DELETE',
 headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},
 body:JSON.stringify({expected_key_set_version:version})})).status;
 },{old:old.key_id,version:snapshot.key_set_version});
 checks.delete_success=deleted===204;
 checks.delete_clears_cookies=!(await master.context.cookies()).some(c=>['__Host-y3-auth','__Host-y3-preauth','__Host-y3-ceremony'].includes(c.name));
 async function reused(who,cookies){const c=cookies.find(v=>v.name==='__Host-y3-auth');
 return (await who.context.request.get(cfg.origin+'/api/v1/auth/me',
 {headers:{Cookie:'__Host-y3-auth='+c.value}})).status()===401;}
 checks.all_old_sessions_denied=await reused(master,oldCookies)&&await reused(observer,observerCookies);
 checks.remaining_key_login=(await login(master,cfg.masterPassword,'master.test',third.credentialId)).result.status===204;
 setStage('management-master');const issued=await api(master.p,'/admin/master-accounts',{login_id:'browser.master.two'});
 checks.master_issued=issued.status===201&&issued.body.admin_scope.kind==='ORGANIZATION';
 const other=await page();await other.p.goto(issued.body.setup_link);
 await other.p.locator('#password').fill(cfg.branchPassword);
 const completed=other.p.waitForResponse(r=>r.url().endsWith('/auth/passkeys/enrollment/verify'));
 await other.p.locator('#mfa button').click();checks.master_setup=(await completed).status()===204;
 const otherKey=(await other.cdp.send('WebAuthn.getCredentials',{authenticatorId:other.authenticatorId})).credentials[0];
 checks.master_login=(await login(other,cfg.branchPassword,'browser.master.two',otherKey.credentialId)).result.status===204;
 checks.master_scope=(await api(other.p,'/branches')).body.total===2;
 async function recover(target,ident,password,loginId){
 const prior=await target.context.cookies();
 const state=(await api(master.p,'/admin/accounts/'+ident+'/passkey-recovery')).body;
 const issued=await api(master.p,'/admin/accounts/'+ident+'/passkey-recovery',{
 expected_account_version:state.account_version,expected_key_set_version:state.key_set_version,identity_confirmed:true});
 if(issued.status!==201)return false;
 if(!(await reused(target,prior)))return false;
 const token=issued.body.recovery_link.split('#token=')[1];let leaked=false;
 target.p.on('request',r=>{if(r.url().includes(token))leaked=true;});
 await target.p.goto(issued.body.recovery_link);
 checks.recovery_fragment_removed=(checks.recovery_fragment_removed??true)&&await target.p.evaluate(()=>location.hash==='');
 const done=target.p.waitForResponse(r=>r.url().endsWith('/auth/passkeys/recovery/verify'));
 await target.p.locator('#mfa button').click();if((await done).status()!==204)return false;
 checks.recovery_no_auto_login=(checks.recovery_no_auto_login??true)&&!(await target.context.cookies()).some(c=>c.name==='__Host-y3-auth');
 checks.recovery_url_private=(checks.recovery_url_private??true)&&!leaked;
 const result=await login(target,password,loginId,undefined);
 return result.result.status===204&&(await api(target.p,'/auth/passkeys')).body.items.length===1;
 }
 setStage('management-recovery-master');checks.master_recovery=await recover(other,issued.body.account_id,cfg.branchPassword,'browser.master.two');
 await login(branch,cfg.branchPassword,'browser.branch',branchKey.credentialId);
 const branchId=(await api(master.p,'/admin/accounts/lookup',{login_id:'browser.branch'})).body.account_id;
 setStage('management-recovery-branch');checks.branch_recovery=await recover(branch,branchId,cfg.branchPassword,'browser.branch');
 await api(branch.p,'/auth/logout',{});
 await onReset({master,other,ident:issued.body.account_id});
 return checks;
};
