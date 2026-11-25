 'use strict';
const fs=require('fs'),path=require('path'),R=process.env.Y3_BROWSER_RUN;
const checks={},required=JSON.parse(fs.readFileSync(path.join(R,'required-checks.json')));
let stage='start';
(async()=>{let browser;const releases=[];try{
const {chromium}=require(path.join(R,'playwright-core'));
const cfg=JSON.parse(fs.readFileSync(path.join(R,'input.json')));
browser=await chromium.launch({executablePath:path.join(R,'browser-binaries/chrome'),headless:true,
chromiumSandbox:true,args:['--no-proxy-server','--disable-background-networking']});
const context=await browser.newContext({ignoreHTTPSErrors:false}),p=await context.newPage();
stage='login';await p.goto(cfg.origin+'/login');checks.trusted_https=await p.evaluate(()=>isSecureContext);
await p.locator('#identifier').fill('master.test');await p.locator('#password').fill(cfg.masterPassword);
const signin=p.waitForResponse(r=>r.url().endsWith('/auth/login'));
await p.locator('#password-form button').click();if((await signin).status()!==204)throw Error();
await p.locator('#products-link').waitFor();checks.master_menu=await p.locator('#products-link').getAttribute('href')==='/products';
async function api(route,body,client=p){return client.evaluate(async({route,body})=>{
 const me=await(await fetch('/api/v1/auth/me')).json();let headers={'X-Y3-Expected-Actor':me.account_id};
 if(body){const c=await(await fetch('/api/v1/auth/csrf',{headers:{'X-Y3-Client':'browser'}})).json();
 headers={...headers,'Content-Type':'application/json','X-CSRF-Token':c.csrf_token};}
 const r=await fetch('/api/v1'+route,{method:body?'POST':'GET',headers,...(body?{body:JSON.stringify(body)}:{})});
 return {status:r.status,body:await r.json()};},{route,body});}
const uuid=()=>p.evaluate(()=>crypto.randomUUID());
async function ready(){await p.waitForFunction(()=>!document.querySelector('#save').disabled);}
async function saved(){await p.waitForFunction(()=>document.querySelector('#product-result').textContent.includes('작업 당시'));await ready();}
async function fill(name,price,count,service='false',type='RATE'){
 await p.locator('#product-name').fill(name);await p.locator('#product-price').fill(price);
 await p.locator('#product-count').fill(count);await p.locator('#product-service').selectOption(service);
 await p.locator('#product-type').selectOption(type);}
async function external(id,name){const current=(await api('/admin/products/'+id)).body;
 return api('/admin/products/'+id,{operation_id:await uuid(),expected_product_version:current.version,
 ...current.values,name});}
stage='create';await p.locator('#products-link').click();await ready();
checks.explicit_empty=await p.locator('#product-name').inputValue()===''&&
await p.locator('#product-price').inputValue()===''&&await p.locator('#product-count').inputValue()===''&&
await p.locator('#product-type').inputValue()===''&&await p.locator('#product-service').inputValue()==='';
await fill('가상 상품A','0','1');await p.locator('#save').click();await saved();
let operation=await p.locator('#product-operation').inputValue();
const first=(await api('/admin/product-operations/'+operation)).body.committed_product,id=first.id;
checks.actual_create_zero_one=first.selling&&first.version===1&&first.values.price_won==='0'&&first.values.session_count==='1';
stage='exact-service';await fill('X'.repeat(200),'9'.repeat(1024),'9223372036854775807','true','FIXED_AMOUNT');
await p.locator('#save').click();await saved();
const exact=(await api('/admin/products/'+id)).body;
checks.exact_big_count_price=exact.values.price_won==='9'.repeat(1024)&&exact.values.session_count==='9223372036854775807'&&
await p.locator('#product-count').inputValue()==='9223372036854775807';
checks.service_fixed=exact.values.is_service===true&&exact.values.payment_type==='FIXED_AMOUNT';
await p.setViewportSize({width:390,height:844});
await p.locator('#refresh').click();await p.locator('[data-product="'+id+'"]').waitFor();
await p.waitForFunction(()=>document.querySelector('#selection').textContent.includes('X'.repeat(200)));
checks.mobile_no_overflow=(await p.locator('[data-product="'+id+'"]').textContent()).includes('X'.repeat(200))&&
(await p.locator('[data-product="'+id+'"]').textContent()).includes('9'.repeat(1024))&&
await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth);
stage='stop-edit';p.once('dialog',d=>d.accept());await p.locator('#stop').click();
await p.waitForFunction(()=>document.querySelector('#selling').textContent==='판매중단');await ready();
await fill('중단 후 정보수정','0','1','true','FIXED_AMOUNT');await p.locator('#save').click();await saved();
checks.stop_then_edit_stays_stopped=!(await api('/admin/products/'+id)).body.selling&&
await p.locator('#selling').textContent()==='판매중단';
const created=await api('/admin/products',{operation_id:await uuid(),name:'가상 상품B',price_won:'0',session_count:'1',payment_type:'RATE',is_service:false});
if(created.status!==200)throw Error();const bid=created.body.committed_product.id;
stage='old-refresh-continuation';let release,seen;const gate=new Promise(r=>release=r),observed=new Promise(r=>seen=r);releases.push(release);
let held=false;const pattern='**/api/v1/admin/products?*';
await p.route(pattern,async route=>{if(held){await route.continue();return;}held=true;
 const response=await route.fetch();seen();await gate;try{await route.fulfill({response});}catch{}});
await p.locator('#refresh').click();await observed;
await p.locator('#refresh').click();await p.locator('[data-product="'+bid+'"]').waitFor();
await p.locator('[data-product="'+bid+'"]').click();
await p.waitForFunction(()=>document.querySelector('#selection').textContent.includes('가상 상품B'));
checks.new_selection_before_old_release=await p.locator('#product-name').inputValue()==='가상 상품B';
let oldDetailRequests=0;const oldDetail=r=>{if(r.method()==='GET'&&r.url().endsWith('/api/v1/admin/products/'+id))oldDetailRequests++;};
p.on('request',oldDetail);
const oldList=p.waitForResponse(r=>r.url().includes('/api/v1/admin/products?'));
const ownerProof=p.waitForResponse(r=>r.url().endsWith('/api/v1/auth/me'));
release();await(await oldList).finished();await(await ownerProof).finished();
await p.waitForLoadState('networkidle');
await p.evaluate(()=>new Promise(resolve=>queueMicrotask(()=>requestAnimationFrame(resolve))));
p.off('request',oldDetail);
checks.stale_refresh_cannot_reselect=oldDetailRequests===0&&await p.locator('#product-name').inputValue()==='가상 상품B';
await p.unroute(pattern);
stage='network-ack';const writePattern='**/api/v1/admin/products/'+bid;let aborted;
await p.route(writePattern,async route=>{if(route.request().method()!=='POST'){await route.continue();return;}
 aborted=route.request().postDataJSON();const response=await route.fetch();if(response.status()!==200)throw Error();await route.abort('failed');});
await p.locator('#product-name').fill('응답 불명 네트워크');await p.locator('#save').click();
await p.waitForFunction(()=>document.querySelector('#product-result').textContent.includes('불명확'));
operation=await p.locator('#product-operation').inputValue();
checks.network_ack_keeps_uuid=aborted.operation_id===operation&&await p.locator('#save').isDisabled();
checks.pending_blocks_new=await p.locator('#new').isDisabled();await p.unroute(writePattern);
await p.locator('#check').click();await saved();
checks.same_uuid_reconciles=(await api('/admin/products/'+bid)).body.version===2&&
(await api('/admin/product-operations/'+operation)).body.committed_product.values.name==='응답 불명 네트워크';
stage='503-ack';let unavailable;
await p.route(writePattern,async route=>{if(route.request().method()!=='POST'){await route.continue();return;}
 unavailable=route.request().postDataJSON();const response=await route.fetch();if(response.status()!==200)throw Error();
 await route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'commit_outcome_unknown'})});});
await p.locator('#product-name').fill('응답 불명503');await p.locator('#save').click();
await p.waitForFunction(()=>document.querySelector('#product-result').textContent.includes('불명확'));
operation=await p.locator('#product-operation').inputValue();
checks.http503_keeps_uuid=unavailable.operation_id===operation&&await p.locator('#new').isDisabled();
await p.unroute(writePattern);
stage='receipt-external-fresh';const receiptPattern='**/api/v1/admin/product-operations/'+operation;let captured;
await p.route(receiptPattern,async route=>{const response=await route.fetch();captured=await response.json();
 if((await external(bid,'receipt 뒤 외부 최신')).status!==200)throw Error();await route.fulfill({response});});
await p.locator('#check').click();await saved();await p.unroute(receiptPattern);
checks.receipt_then_external_fresh=captured.current_product.version===3&&
await p.locator('#product-name').inputValue()==='receipt 뒤 외부 최신'&&
(await p.locator('#product-result').textContent()).includes('작업 당시 update · 버전 3');
stage='paging';for(let i=0;i<25;i++){const r=await api('/admin/products',{operation_id:await uuid(),name:'페이지 '+i,
 price_won:'0',session_count:'1',payment_type:'RATE',is_service:false});if(r.status!==200)throw Error();}
await p.locator('#refresh').click();await ready();
await p.waitForFunction(()=>!document.querySelector('#next').disabled);
await p.locator('#product-name').fill('저장하지 않은 이전 상품');let posts=0;
const watch=r=>{if(r.method()==='POST'&&r.url().includes('/admin/products'))posts++;};p.on('request',watch);
await p.locator('#next').click();await ready();
checks.paging_clears_edit=await p.locator('#product-name').inputValue()===''&&
await p.locator('#product-price').inputValue()===''&&await p.locator('#save').textContent()==='등록';
await p.locator('#save').click();await p.evaluate(()=>new Promise(requestAnimationFrame));
checks.paging_no_accidental_create=posts===0;p.off('request',watch);
stage='actor-switch';const issued=await api('/admin/master-accounts',{login_id:'catalog.other'});if(issued.status!==201)throw Error();
const otherContext=await browser.newContext({ignoreHTTPSErrors:false}),other=await otherContext.newPage();
await other.goto(issued.body.setup_link);await other.locator('#password').fill(cfg.branchPassword);
const setup=other.waitForResponse(r=>r.url().endsWith('/auth/credentials/complete'));
await other.locator('#submit').click();if((await setup).status()!==204)throw Error();
await other.goto(cfg.origin+'/login');await other.locator('#identifier').fill('catalog.other');
await other.locator('#password').fill(cfg.branchPassword);const login=other.waitForResponse(r=>r.url().endsWith('/auth/login'));
await other.locator('#password-form button').click();if((await login).status()!==204)throw Error();

stage='unsaved-ack';await p.goto(cfg.origin+'/products');await ready();
await p.locator('[data-product="'+bid+'"]').click();
await p.waitForFunction(()=>document.querySelector('#product-name').value==='receipt 뒤 외부 최신');
const beforeRetry=(await api('/admin/products/'+bid)).body;let originalRetry;
await p.route(writePattern,async route=>{if(route.request().method()!=='POST'){await route.continue();return;}
 originalRetry=route.request().postDataJSON();await route.abort('failed');});
await p.locator('#product-name').fill('미전달 원 작업');await p.locator('#save').click();
await p.waitForFunction(()=>document.querySelector('#product-result').textContent.includes('불명확'));
const refusedOperation=await p.locator('#product-operation').inputValue();
await p.unroute(writePattern);
if((await api('/admin/product-operations/'+refusedOperation)).status!==404||
 (await api('/admin/products/'+bid)).body.version!==beforeRetry.version)throw Error();
stage='retry-503';let unknownRetry;
await p.route(writePattern,async route=>{if(route.request().method()!=='POST'){await route.continue();return;}
 unknownRetry=route.request().postDataJSON();await route.fulfill({status:503,contentType:'application/json',
 body:JSON.stringify({detail:'commit_outcome_unknown'})});});
const unknownResponse=p.waitForResponse(r=>r.url().endsWith('/admin/products/'+bid)&&r.request().method()==='POST');
await p.locator('#check').click();const unknown=await unknownResponse;await unknown.finished();
await p.waitForFunction(()=>!document.querySelector('#check').disabled);
checks.retry_5xx_preserves_pending=unknown.status()===503&&
 JSON.stringify(unknownRetry)===JSON.stringify(originalRetry)&&
 await p.locator('#product-operation').inputValue()===refusedOperation&&
 await p.locator('#new').isDisabled()&&await p.locator('#save').isDisabled();
await p.unroute(writePattern);
stage='other-master-advance';const originalActor=(await api('/auth/me')).body.account_id;
const otherActor=(await api('/auth/me',undefined,other)).body.account_id;
if(originalActor===otherActor)throw Error();
const otherCurrent=(await api('/admin/products/'+bid,undefined,other)).body;
const advanced=await api('/admin/products/'+bid,{operation_id:await uuid(),
 expected_product_version:otherCurrent.version,...otherCurrent.values,name:'다른 Master 최신'},other);
if(advanced.status!==200||advanced.body.current_product.version!==beforeRetry.version+1)throw Error();
stage='definite-retry-conflict';let refusedBody;
const retried=r=>{if(r.method()==='POST'&&r.url().endsWith('/admin/products/'+bid))refusedBody=r.postDataJSON();};
p.on('request',retried);
const absentReceipt=p.waitForResponse(r=>r.url().endsWith('/admin/product-operations/'+refusedOperation));
const refusedResponse=p.waitForResponse(r=>r.url().endsWith('/admin/products/'+bid)&&r.request().method()==='POST');
await p.locator('#check').click();const absent=await absentReceipt,refused=await refusedResponse;
await absent.finished();await refused.finished();
await p.waitForFunction(()=>document.querySelector('#product-result').textContent.includes('원 작업이 거부')&&
 document.querySelector('#product-name').value==='다른 Master 최신'&&!document.querySelector('#save').disabled);
p.off('request',retried);
checks.retry_conflict_refreshes_current=absent.status()===404&&refused.status()===409&&
 (await refused.json()).detail==='conflict'&&JSON.stringify(refusedBody)===JSON.stringify(originalRetry)&&
 await p.locator('#product-operation').inputValue()===refusedOperation&&
 await p.locator('#new').isEnabled()&&await p.locator('#check').isDisabled()&&
 (await api('/admin/product-operations/'+refusedOperation)).status===404&&
 (await api('/admin/products/'+bid)).body.version===beforeRetry.version+1;
stage='fresh-cas-new-uuid';let freshBody;
const recovered=r=>{if(r.method()==='POST'&&r.url().endsWith('/admin/products/'+bid))freshBody=r.postDataJSON();};
p.on('request',recovered);await p.locator('#product-name').fill('거부 후 새 CAS');
await p.locator('#save').click();await saved();p.off('request',recovered);
checks.retry_new_uuid_uses_fresh_cas=freshBody.operation_id!==refusedOperation&&
 freshBody.expected_product_version===beforeRetry.version+1&&
 (await api('/admin/products/'+bid)).body.version===beforeRetry.version+2;
stage='actor-switch';
await p.locator('#product-name').fill('이전 Actor 초안');posts=0;p.on('request',watch);
await context.clearCookies();await context.addCookies(await otherContext.cookies());
await p.locator('#refresh').click();await p.waitForFunction(()=>document.querySelector('#product-result').textContent.includes('계정이 변경'));
checks.actor_switch_clears=await p.locator('#product-name').inputValue()===''&&await p.locator('#product-price').inputValue()===''&&
await p.locator('#save').isDisabled()&&await p.locator('#products li').count()===0;
checks.actor_switch_zero_posts=posts===0;
if(Object.keys(checks).length!==required.length||!required.every(k=>checks[k]===true))throw Error();
fs.writeFileSync(path.join(R,'browser-results.json'),JSON.stringify({checks,browser:browser.version()}));
}catch(error){stage=(stage+'-'+(['Error','TypeError','TimeoutError'].includes(error.name)?error.name.toLowerCase():'error')).slice(0,64);
process.stderr.write('WORKFORCE_BROWSER_FAILED stage='+stage+'\nWORKFORCE_DIAGNOSTIC='+JSON.stringify(checks)+'\n');process.exitCode=1;}
finally{for(const release of releases)release();if(browser)await browser.close();}})();
