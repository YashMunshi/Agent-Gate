'use strict';
// Public browser simulation. This is not an authentication or security boundary.
// Run app.py for the server-enforced Python/SQLite implementation.
(function(global){
  const clone=value=>JSON.parse(JSON.stringify(value));
  const profiles={alice:{name:'alice',department:'sales',role:'employee'},bob:{name:'bob',department:'finance',role:'employee'},admin:{name:'admin',department:'security',role:'security_admin'}};
  class GateDemo {
    constructor(storage=null,now=()=>Date.now()/1000){
      this.storage=storage;this.now=now;
      this.db={schema:1,user:null,tickets:clone(global.GateFixture.tickets),credentials:[],approvals:[],exports:[],audit:[],tests:null,next:1};
      try{const saved=JSON.parse(storage?.getItem('agent-gate-lab')||'null');if(saved?.schema===1&&Array.isArray(saved.tickets)&&Array.isArray(saved.credentials)&&Array.isArray(saved.approvals)&&Array.isArray(saved.audit)&&Array.isArray(saved.exports)&&Number.isSafeInteger(saved.next)&&(!saved.user||profiles[saved.user]))this.db=saved;}catch{}
    }
    save(){try{this.storage?.setItem('agent-gate-lab',JSON.stringify(this.db));}catch{}}
    id(){return this.db.next++;}
    log(actor,event,resource,decision,reason){this.db.audit.push({id:this.id(),timestamp:this.now(),actor,event,resource,decision,reason});this.db.audit=this.db.audit.slice(-80);}
    user(){const user=profiles[this.db.user];if(!user)throw Error('Choose a demo account to enter the workspace.');return user;}
    agent(id){const agent=global.GateFixture.agents.find(a=>a.id===id);if(!agent)throw Error('Agent identity does not exist.');return agent;}
    manage(user,agent){if(user.role!=='security_admin'&&user.name!==agent.owner)throw Error('Only the agent owner or security administrator can use this identity.');}
    administrator(user){if(user.role!=='security_admin')throw Error('An administrator must review this action.');}
    issue(user,id){
      const agent=this.agent(id);this.manage(user,agent);
      const token='demo_'+global.crypto.randomUUID();
      this.db.credentials.push({token,agent_id:id,issuer:user.name,expires:this.now()+180,revoked:0});
      this.db.credentials=this.db.credentials.slice(-200);
      this.log(user.name,'credential.issue',id,'allow','Demo credential issued for 180 seconds');
      return {token,agent_id:id,expires_in:180,scopes:agent.scopes};
    }
    credential(token){
      const credential=this.db.credentials.find(c=>c.token===token);
      if(!credential||credential.revoked||credential.expires<=this.now())throw Error('Agent credential is invalid, expired, or revoked.');
      return credential;
    }
    fingerprint(agent,tool,args){return JSON.stringify([agent.id,tool,Object.entries(args).sort(([a],[b])=>a.localeCompare(b))]);}
    check(agent,tool,args){
      const trace=['Demo agent identity validated'];
      if(!global.GateFixture.tools.includes(tool)||!agent.scopes.includes(tool))return {decision:'deny',reason:'Tool is outside this agent’s allowed scopes',trace:[...trace,'Scope check failed']};
      trace.push('Tool scope allowed');
      const fields={'tickets.read':['ticket_id'],'tickets.update':['status','ticket_id'],'finance.read':[],'reports.export':['destination']}[tool];
      if(!args||typeof args!=='object'||Array.isArray(args)||JSON.stringify(Object.keys(args).sort())!==JSON.stringify(fields))return {decision:'deny',reason:'Tool arguments do not match the permitted schema',trace:[...trace,'Argument schema rejected']};
      trace.push('Argument schema validated');
      if(tool.startsWith('tickets.')){
        const ticket=this.db.tickets.find(t=>t.id===String(args.ticket_id));
        if(!ticket||ticket.department!==agent.department)return {decision:'deny',reason:'Ticket is outside the agent’s department',trace:[...trace,'Resource scope rejected']};
        if(tool==='tickets.update'&&!['open','resolved'].includes(args.status))return {decision:'deny',reason:'Unsupported ticket status',trace:[...trace,'Value restriction rejected']};
      }
      if(tool==='reports.export'&&args.destination!=='internal://reports')return {decision:'deny',reason:'Exports are restricted to the internal report store',trace:[...trace,'Destination restriction rejected']};
      trace.push('Resource boundary validated');
      return ['tickets.update','reports.export'].includes(tool)?{decision:'approval_required',reason:'An administrator must approve this exact action',trace:[...trace,'Sensitive action requires approval']}:{decision:'allow',reason:'All demo access checks passed',trace};
    }
    execute(user,body){
      const credential=this.credential(body.token),agent=this.agent(credential.agent_id);this.manage(user,agent);
      const tool=String(body.tool||''),args=body.args??{};
      if(JSON.stringify(args).length>4000)throw Error('Tool arguments are too large.');
      const result={...this.check(agent,tool,args),data:null,approval_id:null,execution_mode:'public browser simulation; synthetic records; no LLM call'};
      if(result.decision==='approval_required'){
        const fingerprint=this.fingerprint(agent,tool,args);
        if(body.approval_id!==undefined){
          const approval=this.db.approvals.find(a=>a.id===Number(body.approval_id));
          if(!approval||approval.status!=='approved'||approval.expires<=this.now()){result.decision='deny';result.reason='Approval is missing, expired, or already consumed';}
          else if(approval.fingerprint!==fingerprint||approval.requester!==credential.issuer){result.decision='deny';result.reason='Approval is bound to different arguments, identity, or requester';}
          else{result.decision='allow';result.reason='Exact action approved and demo permissions revalidated';approval.status='consumed';result.trace.push('Action-bound approval consumed once');}
        }else{
          let approval=this.db.approvals.find(a=>a.fingerprint===fingerprint&&a.requester===credential.issuer&&a.status==='pending'&&a.expires>this.now());
          if(!approval){approval={id:this.id(),agent_id:agent.id,tool,args:JSON.stringify(args),fingerprint,requester:credential.issuer,status:'pending',expires:this.now()+300,approved_by:null,created:this.now()};this.db.approvals.push(approval);this.db.approvals=this.db.approvals.slice(-200);}
          result.approval_id=approval.id;
        }
      }
      if(result.decision==='allow'){
        if(tool==='tickets.read'){const t=this.db.tickets.find(t=>t.id===args.ticket_id);result.data={id:t.id,department:t.department,subject:t.subject,status:t.status};result.trace.push('Requester email excluded from response');}
        if(tool==='tickets.update'){this.db.tickets.find(t=>t.id===args.ticket_id).status=args.status;result.data={ticket_id:args.ticket_id,status:args.status};}
        if(tool==='finance.read')result.data={quarter:'Q4',total_budget_usd:42000,classification:'synthetic aggregate; no payroll fields'};
        if(tool==='reports.export'){const records=this.db.tickets.filter(t=>t.department===agent.department).map(t=>({id:t.id,subject:t.subject,status:t.status}));result.data={export_id:this.id(),destination:args.destination,records};this.db.exports.push({...result.data,agent_id:agent.id,created:this.now()});this.db.exports=this.db.exports.slice(-80);}
        result.trace.push('Synthetic browser tool executed');
      }else result.trace.push('No tool side effect executed');
      this.log(agent.id,tool,String(args.ticket_id||args.destination||'aggregate'),result.decision,result.reason);
      return result;
    }
    approve(user,id){
      this.administrator(user);const approval=this.db.approvals.find(a=>a.id===Number(id));
      if(!approval||approval.status!=='pending'||approval.expires<=this.now())throw Error('Approval request is no longer pending or has expired.');
      if(approval.requester===user.name)throw Error('You cannot approve your own requested action.');
      if(this.check(this.agent(approval.agent_id),approval.tool,JSON.parse(approval.args)).decision==='deny')throw Error('Current policy rejects this action.');
      approval.status='approved';approval.approved_by=user.name;approval.expires=this.now()+120;
      this.log(user.name,'approval',approval.agent_id,'allow','Exact action approved for 120 seconds');return {ok:true};
    }
    revoke(user,id){const agent=this.agent(id);this.manage(user,agent);this.db.credentials.filter(c=>c.agent_id===id).forEach(c=>c.revoked=1);this.log(user.name,'credential.revoke',id,'deny','Demo credentials for this identity revoked');return {ok:true};}
    state(){
      const user=this.user(),agents=global.GateFixture.agents.filter(a=>user.role==='security_admin'||a.owner===user.name),own=new Set([user.name,...agents.map(a=>a.id)]);
      return {user,csrf:'',agents,tools:global.GateFixture.tools,approvals:this.db.approvals.filter(a=>user.role==='security_admin'||a.requester===user.name).slice().reverse(),credentials:this.db.credentials.filter(c=>user.role==='security_admin'||c.issuer===user.name).map(({token,...credential})=>credential).reverse(),audit:this.db.audit.filter(a=>user.role==='security_admin'||own.has(a.actor)).slice().reverse(),tests:this.db.tests};
    }
    evaluate(){
      const lab=new GateDemo(null,this.now),alice=profiles.alice,bob=profiles.bob,admin=profiles.admin;
      const support=lab.issue(alice,'support-assistant').token,exporter=lab.issue(alice,'report-exporter').token,finance=lab.issue(bob,'finance-reader').token,cases=[];
      const test=(name,user,token,body,expected)=>{let result;try{result=lab.execute(user,{token,...body});}catch(error){result={decision:'invalid_credential',reason:error.message};}cases.push({name,expected,actual:result.decision,passed:result.decision===expected,reason:result.reason});return result;};
      test('Own-department ticket read',alice,support,{tool:'tickets.read',args:{ticket_id:'T-101'}},'allow');
      test('Cross-department ticket denied',alice,support,{tool:'tickets.read',args:{ticket_id:'T-102'}},'deny');
      test('Finance tool outside support scope',alice,support,{tool:'finance.read',args:{}},'deny');
      test('Unexpected arguments rejected',alice,support,{tool:'tickets.read',args:{ticket_id:'T-101',include_email:true}},'deny');
      test('External destination rejected',alice,exporter,{tool:'reports.export',args:{destination:'external://outside'}},'deny');
      const pending=test('Ticket mutation requires approval',alice,support,{tool:'tickets.update',args:{ticket_id:'T-101',status:'resolved'}},'approval_required');
      lab.approve(admin,pending.approval_id);
      test('Changed arguments invalidate approval',alice,support,{tool:'tickets.update',args:{ticket_id:'T-103',status:'resolved'},approval_id:pending.approval_id},'deny');
      const action={tool:'tickets.update',args:{ticket_id:'T-101',status:'resolved'},approval_id:pending.approval_id};
      test('Approved exact action executes',alice,support,action,'allow');
      test('Consumed approval cannot replay',alice,support,action,'deny');
      test('Finance aggregate allowed',bob,finance,{tool:'finance.read',args:{}},'allow');
      lab.revoke(alice,'support-assistant');test('Revoked credential rejected',alice,support,{tool:'tickets.read',args:{ticket_id:'T-101'}},'invalid_credential');
      lab.db.credentials.find(c=>c.token===finance).expires=0;test('Expired credential rejected',bob,finance,{tool:'finance.read',args:{}},'invalid_credential');
      return {cases,total:cases.length,passed:cases.filter(c=>c.passed).length,scope:'public browser simulation of explicit access controls; not server security or LLM safety accuracy'};
    }
    request(path,body){
      try{
        if(path==='login'){if(!profiles[body?.name]||body.password!=='DemoPass!2026')throw Error('Use a demo account and password DemoPass!2026.');this.db.user=body.name;return {csrf:''};}
        if(path==='reset'){this.db.user=null;this.db.tickets=clone(global.GateFixture.tickets);this.db.credentials=[];this.db.approvals=[];this.db.exports=[];this.db.audit=[];this.db.tests=null;this.db.next=1;return {ok:true};}
        const user=this.user();
        if(path==='logout'){this.db.user=null;return {ok:true};}
        if(path==='state')return clone(this.state());
        if(path==='issue')return this.issue(user,body.agent_id);
        if(path==='execute')return this.execute(user,body);
        if(path==='approve')return this.approve(user,body.id);
        if(path==='revoke')return this.revoke(user,body.agent_id);
        if(path==='reject'){this.administrator(user);const approval=this.db.approvals.find(a=>a.id===Number(body.id)&&a.status==='pending');if(!approval)throw Error('Request is no longer pending.');approval.status='rejected';approval.approved_by=user.name;this.log(user.name,'approval.reject','request','deny','Sensitive action rejected');return {ok:true};}
        if(path==='test'){this.administrator(user);this.db.tests=this.evaluate();this.log(user.name,'test','isolated synthetic scenarios','complete','Browser control scenarios executed');return clone(this.db.tests);}
        throw Error('Endpoint does not exist.');
      }finally{this.save();}
    }
  }
  global.GateDemo=GateDemo;
  if(typeof module!=='undefined')module.exports=GateDemo;
  if(typeof window!=='undefined'){let storage;try{storage=window.localStorage;}catch{}global.agentGateDemo=new GateDemo(storage);}
})(typeof window!=='undefined'?window:globalThis);
