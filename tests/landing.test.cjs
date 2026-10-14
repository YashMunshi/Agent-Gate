const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
global.crypto=require('node:crypto').webcrypto;
const fixtureContext={window:{}};vm.runInNewContext(fs.readFileSync('public/fixture.js','utf8'),fixtureContext);global.GateFixture=fixtureContext.window.GateFixture;
const GateDemo=require('../hosted/demo.js');
function setup(){
 const samples=['read','boundary','approval'].map(sample=>({dataset:{sample},setAttribute(name,value){this[name]=value;}}));
 const launches=['alice','bob','admin'].map(launch=>({dataset:{launch},innerHTML:'Open lab',setAttribute(){},removeAttribute(){}}));
 const output={innerHTML:''},error={textContent:''};
 const root={innerHTML:'',querySelectorAll:selector=>selector==='[data-sample]'?samples:selector==='[data-launch]'?launches:[],querySelector:selector=>selector==='#sample-output'?output:selector==='#launch-error'?error:{focus(){}}};
 const window={GateFixture:global.GateFixture,GateDemo};vm.runInNewContext(fs.readFileSync('public/landing.js','utf8'),{window});
 return {window,root,samples,launches,output,error};
}
test('Public entrance explains the product and renders one accessible main heading',()=>{
 const {window,root}=setup();window.AgentGateLanding.render(root,{mark:'<svg aria-hidden="true"></svg>',onEnter:async()=>{}});
 assert.equal((root.innerHTML.match(/<h1\b/g)||[]).length,1);assert.ok(root.innerHTML.includes('Explore the live lab'));assert.ok(root.innerHTML.includes('Public browser simulation. Synthetic data.'));assert.ok(root.innerHTML.includes('Read the threat model'));assert.ok(!root.innerHTML.includes('type="password"'));assert.ok(root.innerHTML.includes('<dd>03</dd>'));assert.ok(root.innerHTML.includes('<dd>04</dd>'));
});
test('Preview choices execute real demo checks without changing the visitor workspace',()=>{
 const {window,root,samples,output}=setup(),workspace=new GateDemo();workspace.request('login',{name:'alice',password:'DemoPass!2026'});const before=JSON.stringify(workspace.db);
 window.AgentGateLanding.render(root,{mark:'',onEnter:async()=>{}});
 const expected={read:'allow',boundary:'deny',approval:'approval_required'};
 for(const [key,decision] of Object.entries(expected)){assert.equal(window.AgentGateLanding.sample(key).result.decision,decision);samples.find(button=>button.dataset.sample===key).onclick();assert.ok(output.innerHTML.includes('sample-verdict '+decision));assert.equal(samples.filter(button=>button['aria-pressed']==='true').length,1);}
 assert.equal(JSON.stringify(workspace.db),before);
});
test('Every role entry opens the selected demo perspective',async()=>{
 const {window,root,launches}=setup(),selected=[];window.AgentGateLanding.render(root,{mark:'',onEnter:async role=>selected.push(role)});for(const button of launches)await button.onclick();assert.deepEqual(selected,['alice','bob','admin']);
});
test('Public startup uses the project entrance; local startup retains backend login',()=>{
 const source=fs.readFileSync('public/app.js','utf8').replace('refresh().catch(()=>login());','');let publicRenders=0;
 const root={innerHTML:'',querySelector:()=>({}),querySelectorAll:()=>[]};
 const context=vm.createContext({window:{agentGateDemo:{},AgentGateLanding:{render:()=>publicRenders++}},document:{querySelector:()=>root},Blob,URL,console});vm.runInContext(source,context);assert.equal(publicRenders,1);
 context.window.AgentGateLanding=undefined;vm.runInContext('login();',context);assert.ok(root.innerHTML.includes('id="login-form"'));assert.ok(root.innerHTML.includes('type="password"'));
});
