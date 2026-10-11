"""Agent Gate: scoped identities and action-bound approval for mock enterprise tools."""
import argparse
import hashlib
import json
import secrets
import time
from pathlib import Path
from core import Store, Problem, admin, serve

AGENTS = [
    {'id':'support-assistant','name':'Support assistant','scopes':['tickets.read','tickets.update'],
     'department':'sales','owner':'alice'},
    {'id':'finance-reader','name':'Finance reader','scopes':['finance.read'],
     'department':'finance','owner':'bob'},
    {'id':'report-exporter','name':'Report exporter','scopes':['tickets.read','reports.export'],
     'department':'sales','owner':'alice'},
]
TOOLS = ['tickets.read','tickets.update','finance.read','reports.export']
TICKETS = [
    {'id':'T-101','department':'sales','subject':'Laptop setup','status':'open','requester_email':'synthetic-alice@example.test'},
    {'id':'T-102','department':'finance','subject':'Payroll access','status':'open','requester_email':'synthetic-bob@example.test'},
    {'id':'T-103','department':'sales','subject':'CRM configuration','status':'open','requester_email':'synthetic-sales@example.test'},
]


def canonical(agent_id,tool,args):
    return json.dumps({'agent_id':agent_id,'tool':tool,'args':args},sort_keys=True,separators=(',',':'))


class Application:
    def __init__(self,path):
        self.store = Store(path)
        self.store.initialize()
        with self.store.connect() as db:
            db.executescript('''
              CREATE TABLE IF NOT EXISTS credentials(digest TEXT PRIMARY KEY,agent_id TEXT,issuer TEXT,expires REAL,revoked INTEGER);
              CREATE TABLE IF NOT EXISTS approvals(id INTEGER PRIMARY KEY,agent_id TEXT,tool TEXT,args TEXT,
                fingerprint TEXT,requester TEXT,status TEXT,expires REAL,approved_by TEXT,created REAL);
              CREATE TABLE IF NOT EXISTS tickets(id TEXT PRIMARY KEY,department TEXT,subject TEXT,status TEXT,requester_email TEXT);
              CREATE TABLE IF NOT EXISTS exports(id INTEGER PRIMARY KEY,agent_id TEXT,destination TEXT,created REAL,body TEXT);
              CREATE TABLE IF NOT EXISTS test_runs(id INTEGER PRIMARY KEY,created REAL,summary TEXT);
            ''')
            for t in TICKETS:
                db.execute('INSERT OR IGNORE INTO tickets VALUES(?,?,?,?,?)',tuple(t[k] for k in ('id','department','subject','status','requester_email')))

    def agent(self,agent_id):
        for agent in AGENTS:
            if agent['id'] == agent_id:
                return agent
        raise Problem(404,'Agent identity does not exist.')

    def can_manage(self,user,agent):
        if user['role'] != 'security_admin' and user['name'] != agent['owner']:
            raise Problem(403,'Only the agent owner or security administrator can use this identity.')

    def issue(self,user,agent_id,ttl=180):
        agent = self.agent(agent_id)
        self.can_manage(user,agent)
        if not 1 <= ttl <= 300:
            raise Problem(400,'Credential lifetime must be 1–300 seconds.')
        token = secrets.token_urlsafe(32)
        with self.store.connect() as db:
            db.execute('INSERT INTO credentials VALUES(?,?,?,?,0)',
                       (hashlib.sha256(token.encode()).hexdigest(),agent_id,user['name'],time.time()+ttl))
        self.store.log(user['name'],'credential.issue',agent_id,'allow',f'Scoped credential expires in {ttl}s')
        return {'token':token,'expires_in':ttl,'agent_id':agent_id,'scopes':agent['scopes']}

    def authenticate(self,token):
        with self.store.connect() as db:
            row = db.execute('SELECT * FROM credentials WHERE digest=?',
                             (hashlib.sha256(token.encode()).hexdigest(),)).fetchone()
        if not row or row['revoked'] or row['expires'] <= time.time():
            self.store.log('unknown-agent','credential.validate','credential','deny','Invalid, expired, or revoked credential')
            raise Problem(401,'Agent credential is invalid, expired, or revoked.')
        return self.agent(row['agent_id']),row['issuer']

    def check(self,agent,tool,args,db):
        trace = ['Agent identity validated']
        if tool not in TOOLS or tool not in agent['scopes']:
            return 'deny','Tool is outside this agent’s allowed scopes',trace+['Scope check failed']
        trace.append('Tool scope allowed')
        allowed_fields = {'tickets.read':{'ticket_id'},'tickets.update':{'ticket_id','status'},
                          'finance.read':set(),'reports.export':{'destination'}}[tool]
        if not isinstance(args,dict) or set(args) != allowed_fields:
            return 'deny','Tool arguments do not match the permitted schema',trace+['Argument schema rejected']
        trace.append('Argument schema validated')
        if tool.startswith('tickets.'):
            ticket = db.execute('SELECT * FROM tickets WHERE id=?',(str(args['ticket_id']),)).fetchone()
            if not ticket or ticket['department'] != agent['department']:
                return 'deny','Ticket is outside the agent’s department',trace+['Resource scope rejected']
            if tool == 'tickets.update' and args['status'] not in ('open','resolved'):
                return 'deny','Unsupported ticket status',trace+['Value restriction rejected']
        if tool == 'reports.export' and args['destination'] != 'internal://reports':
            return 'deny','Exports are restricted to the internal report store',trace+['Destination restriction rejected']
        trace.append('Resource boundary validated')
        if tool in ('tickets.update','reports.export'):
            return 'approval_required','An administrator must approve this exact action',trace+['Sensitive action requires approval']
        return 'allow','All access checks passed',trace

    def execute_bearer(self,token,body):
        agent,issuer = self.authenticate(token)
        tool,args = str(body.get('tool','')),body.get('args',{})
        if len(json.dumps(args)) > 4000:
            raise Problem(400,'Tool arguments are too large.')
        trace, data, approval_id = [],None,None
        # Serialize authorization, approval consumption, and mock side effects.
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            # Recheck credential under the same transaction as the side effect.
            cred = db.execute('SELECT * FROM credentials WHERE digest=?',
                              (hashlib.sha256(token.encode()).hexdigest(),)).fetchone()
            if not cred or cred['revoked'] or cred['expires'] <= time.time():
                raise Problem(401,'Credential expired or was revoked before execution.')
            decision,reason,trace = self.check(agent,tool,args,db)
            fingerprint = hashlib.sha256(canonical(agent['id'],tool,args).encode()).hexdigest()
            if decision == 'approval_required':
                supplied_id = body.get('approval_id')
                if supplied_id is not None:
                    approval = db.execute('SELECT * FROM approvals WHERE id=?',(int(supplied_id),)).fetchone()
                    if not approval or approval['status'] != 'approved' or approval['expires'] <= time.time():
                        decision,reason = 'deny','Approval is missing, expired, or already consumed'
                    elif approval['fingerprint'] != fingerprint or approval['requester'] != issuer:
                        decision,reason = 'deny','Approval is bound to different arguments, identity, or requester'
                    else:
                        decision,reason = 'allow','Exact action approved and permissions revalidated'
                        db.execute("UPDATE approvals SET status='consumed' WHERE id=?",(approval['id'],))
                        trace.append('Action-bound approval consumed once')
                else:
                    pending = db.execute("SELECT id FROM approvals WHERE fingerprint=? AND requester=? AND status='pending' AND expires>?",
                                         (fingerprint,issuer,time.time())).fetchone()
                    approval_id = pending['id'] if pending else db.execute('INSERT INTO approvals VALUES(NULL,?,?,?,?,?,?,?,?,?)',
                        (agent['id'],tool,json.dumps(args,sort_keys=True),fingerprint,issuer,'pending',time.time()+300,None,time.time())).lastrowid
            if decision == 'allow':
                if tool == 'tickets.read':
                    row = db.execute('SELECT id,department,subject,status FROM tickets WHERE id=?',(args['ticket_id'],)).fetchone()
                    data = dict(row)
                    trace.append('Requester email excluded from response')
                elif tool == 'tickets.update':
                    db.execute('UPDATE tickets SET status=? WHERE id=?',(args['status'],args['ticket_id']))
                    data = {'ticket_id':args['ticket_id'],'status':args['status']}
                elif tool == 'finance.read':
                    data = {'quarter':'Q4','total_budget_usd':42000,'classification':'synthetic aggregate; no payroll fields'}
                elif tool == 'reports.export':
                    records = [dict(t) for t in db.execute('SELECT id,subject,status FROM tickets WHERE department=?',(agent['department'],))]
                    export_id = db.execute('INSERT INTO exports VALUES(NULL,?,?,?,?)',
                                           (agent['id'],args['destination'],time.time(),json.dumps(records))).lastrowid
                    data = {'export_id':export_id,'destination':args['destination'],'records':records}
                trace.append('Local mock tool executed')
            else:
                trace.append('No tool side effect executed')
            db.execute('INSERT INTO audit VALUES(NULL,?,?,?,?,?,?)',
                       (time.time(),agent['id'],tool,str(args.get('ticket_id',args.get('destination','aggregate'))),decision,reason))
        return {'decision':decision,'reason':reason,'trace':trace,'data':data,'approval_id':approval_id,
                'execution_mode':'scripted requests; local mock tools; no LLM call'}

    def approve(self,user,approval_id):
        admin(user)
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            a = db.execute('SELECT * FROM approvals WHERE id=?',(approval_id,)).fetchone()
            if not a or a['status'] != 'pending' or a['expires'] <= time.time():
                raise Problem(409,'Approval request is no longer pending or has expired.')
            if a['requester'] == user['name']:
                raise Problem(403,'You cannot approve your own requested action.')
            # Re-evaluate current policy before approving; execution checks it again.
            decision,_,_ = self.check(self.agent(a['agent_id']),a['tool'],json.loads(a['args']),db)
            if decision == 'deny':
                raise Problem(403,'Current policy rejects this action.')
            db.execute("UPDATE approvals SET status='approved',approved_by=?,expires=? WHERE id=?",
                       (user['name'],time.time()+120,approval_id))
        self.store.log(user['name'],'approval',a['agent_id'],'allow','Exact action approved for 120 seconds')
        return {'ok':True}

    def route(self,method,path,body,user):
        if path == '/api/state' and method == 'GET':
            with self.store.connect() as db:
                approvals = [dict(a) for a in db.execute('SELECT * FROM approvals ORDER BY id DESC')
                             if user['role'] == 'security_admin' or a['requester'] == user['name']]
                credentials = [dict(c) for c in db.execute('SELECT agent_id,issuer,expires,revoked FROM credentials ORDER BY expires DESC')
                               if user['role'] == 'security_admin' or c['issuer'] == user['name']]
                row = db.execute('SELECT summary FROM test_runs ORDER BY id DESC LIMIT 1').fetchone()
            agents = AGENTS if user['role'] == 'security_admin' else [a for a in AGENTS if a['owner']==user['name']]
            audit = self.store.audit()
            if user['role'] != 'security_admin':
                own = {a['id'] for a in agents}|{user['name']}
                audit = [a for a in audit if a['actor'] in own]
            return {'user':{k:user[k] for k in ('name','department','role')},'csrf':user['csrf'],
                    'agents':agents,'tools':TOOLS,'approvals':approvals,'credentials':credentials,'audit':audit,
                    'tests':json.loads(row['summary']) if row else None}
        if path == '/api/issue' and method == 'POST':
            return self.issue(user,body['agent_id'],int(body.get('ttl_seconds',180)))
        if path == '/api/revoke' and method == 'POST':
            agent = self.agent(body['agent_id'])
            self.can_manage(user,agent)
            with self.store.connect() as db:
                db.execute('UPDATE credentials SET revoked=1 WHERE agent_id=?',(agent['id'],))
            self.store.log(user['name'],'credential.revoke',agent['id'],'deny','All credentials for this identity revoked')
            return {'ok':True}
        if path == '/api/execute' and method == 'POST':
            token = str(body.get('token',''))
            agent,_ = self.authenticate(token)
            self.can_manage(user,agent)
            return self.execute_bearer(token,body)
        if path == '/api/approve' and method == 'POST':
            return self.approve(user,int(body['id']))
        if path == '/api/reject' and method == 'POST':
            admin(user)
            with self.store.connect() as db:
                count = db.execute("UPDATE approvals SET status='rejected',approved_by=? WHERE id=? AND status='pending'",
                                   (user['name'],int(body['id']))).rowcount
                if not count:
                    raise Problem(409,'Request is no longer pending.')
            self.store.log(user['name'],'approval.reject','request','deny','Sensitive action rejected')
            return {'ok':True}
        if path == '/api/test' and method == 'POST':
            admin(user)
            # Run the real gateway against an isolated temporary database, never live records.
            import tempfile
            with tempfile.TemporaryDirectory() as tmp:
                app = Application(Path(tmp)/'test.sqlite')
                alice={'name':'alice','role':'employee','department':'sales'}
                bob={'name':'bob','role':'employee','department':'finance'}
                support = app.issue(alice,'support-assistant')['token']
                exporter = app.issue(alice,'report-exporter')['token']
                finance = app.issue(bob,'finance-reader')['token']
                cases = []
                def case(name,token,payload,expected):
                    try:
                        result = app.execute_bearer(token,payload)
                        actual = result['decision']
                    except Problem as e:
                        actual = 'invalid_credential' if e.status == 401 else 'error'
                        result = {'reason':e.message}
                    cases.append({'name':name,'expected':expected,'actual':actual,'passed':actual==expected,'reason':result['reason']})
                    return result
                case('Own-department ticket read',support,{'tool':'tickets.read','args':{'ticket_id':'T-101'}},'allow')
                case('Cross-department ticket denied',support,{'tool':'tickets.read','args':{'ticket_id':'T-102'}},'deny')
                case('Finance tool outside support scope',support,{'tool':'finance.read','args':{}},'deny')
                case('Unexpected arguments rejected',support,{'tool':'tickets.read','args':{'ticket_id':'T-101','include_email':True}},'deny')
                case('External destination rejected',exporter,{'tool':'reports.export','args':{'destination':'external://outside'}},'deny')
                pending = case('Ticket mutation requires approval',support,{'tool':'tickets.update','args':{'ticket_id':'T-101','status':'resolved'}},'approval_required')
                app.approve(user,pending['approval_id'])
                case('Changed arguments invalidate approval',support,{'tool':'tickets.update','args':{'ticket_id':'T-103','status':'resolved'},'approval_id':pending['approval_id']},'deny')
                request = {'tool':'tickets.update','args':{'ticket_id':'T-101','status':'resolved'},'approval_id':pending['approval_id']}
                case('Approved exact action executes',support,request,'allow')
                case('Consumed approval cannot replay',support,request,'deny')
                case('Finance aggregate allowed',finance,{'tool':'finance.read','args':{}},'allow')
                app.route('POST','/api/revoke',{'agent_id':'support-assistant'},alice)
                case('Revoked credential rejected',support,{'tool':'tickets.read','args':{'ticket_id':'T-101'}},'invalid_credential')
                with app.store.connect() as db:
                    db.execute('UPDATE credentials SET expires=0 WHERE agent_id=?',('finance-reader',))
                case('Expired credential rejected',finance,{'tool':'finance.read','args':{}},'invalid_credential')
            summary = {'cases':cases,'total':len(cases),'passed':sum(c['passed'] for c in cases),
                       'scope':'deterministic local gateway controls; not LLM prompt-injection detection accuracy'}
            with self.store.connect() as db:
                db.execute('INSERT INTO test_runs VALUES(NULL,?,?)',(time.time(),json.dumps(summary)))
            self.store.log(user['name'],'test','isolated synthetic scenarios','complete','Defensive control tests executed')
            return summary
        raise Problem(404,'Endpoint does not exist.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8766)
    parser.add_argument('--db',default=str(Path(__file__).with_name('demo.sqlite')))
    args=parser.parse_args()
    serve(Application(args.db),Path(__file__).with_name('web'),args.port)
