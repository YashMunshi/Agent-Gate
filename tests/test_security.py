"""Independent security and HTTP tests; Python standard library only."""
import concurrent.futures
import hashlib
import json
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from core import Problem
import app as gate
ALICE={'name':'alice','department':'sales','role':'employee'}
BOB={'name':'bob','department':'finance','role':'employee'}
ADMIN={'name':'admin','department':'security','role':'security_admin'}


class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.app=gate.Application(Path(self.tmp.name)/'gate.sqlite')
        self.token=self.app.issue(ALICE,'support-assistant')['token']
    def tearDown(self):self.tmp.cleanup()
    def call(self,tool='tickets.read',args=None,**extra):
        return self.app.execute_bearer(self.token,{'tool':tool,'args':args if args is not None else {'ticket_id':'T-101'},**extra})
    def approved(self):
        payload={'tool':'tickets.update','args':{'ticket_id':'T-101','status':'resolved'}}
        i=self.app.execute_bearer(self.token,payload)['approval_id']
        self.app.approve(ADMIN,i)
        return {**payload,'approval_id':i}
    def test_owner_cannot_issue_other_department_identity(self):
        with self.assertRaises(Problem):self.app.issue(ALICE,'finance-reader')
    def test_invalid_and_expired_credentials(self):
        with self.assertRaises(Problem):self.app.execute_bearer('invalid',{'tool':'tickets.read','args':{'ticket_id':'T-101'}})
        with self.app.store.connect() as db:db.execute('UPDATE credentials SET expires=0')
        with self.assertRaises(Problem):self.call()
    def test_token_secret_not_stored(self):
        with self.app.store.connect() as db:r=db.execute('SELECT digest FROM credentials').fetchone()
        self.assertNotEqual(r['digest'],self.token)
        self.assertEqual(r['digest'],hashlib.sha256(self.token.encode()).hexdigest())
    def test_read_masks_email(self):
        r=self.call();self.assertEqual(r['decision'],'allow')
        self.assertNotIn('requester_email',r['data'])
    def test_cross_department_denied(self):self.assertEqual(self.call(args={'ticket_id':'T-102'})['decision'],'deny')
    def test_tool_scope_denied(self):self.assertEqual(self.call('finance.read',{})['decision'],'deny')
    def test_unknown_tool_denied(self):self.assertEqual(self.call('unknown',{})['decision'],'deny')
    def test_extra_arguments_denied(self):self.assertEqual(self.call(args={'ticket_id':'T-101','include_email':True})['decision'],'deny')
    def test_external_export_denied(self):
        token=self.app.issue(ALICE,'report-exporter')['token']
        self.assertEqual(self.app.execute_bearer(token,{'tool':'reports.export','args':{'destination':'external://outside'}})['decision'],'deny')
    def test_no_side_effect_before_approval(self):
        r=self.call('tickets.update',{'ticket_id':'T-101','status':'resolved'})
        self.assertEqual(r['decision'],'approval_required')
        with self.app.store.connect() as db:self.assertEqual(db.execute("SELECT status FROM tickets WHERE id='T-101'").fetchone()[0],'open')
    def test_approval_rejects_changed_args(self):
        p=self.approved();p['args']={'ticket_id':'T-103','status':'resolved'}
        self.assertEqual(self.app.execute_bearer(self.token,p)['decision'],'deny')
    def test_approval_consumed_only_once(self):
        p=self.approved()
        self.assertEqual(self.app.execute_bearer(self.token,p)['decision'],'allow')
        self.assertEqual(self.app.execute_bearer(self.token,p)['decision'],'deny')
    def test_approval_atomic_under_concurrent_requests(self):
        p=self.approved()
        with concurrent.futures.ThreadPoolExecutor(2) as pool:
            results=list(pool.map(lambda _:self.app.execute_bearer(self.token,p)['decision'],range(2)))
        self.assertEqual(sorted(results),['allow','deny'])
    def test_approval_expiry(self):
        p=self.approved()
        with self.app.store.connect() as db:db.execute('UPDATE approvals SET expires=0')
        self.assertEqual(self.app.execute_bearer(self.token,p)['decision'],'deny')
    def test_revocation_still_blocks_approved_action(self):
        p=self.approved();self.app.route('POST','/api/revoke',{'agent_id':'support-assistant'},ALICE)
        with self.assertRaises(Problem):self.app.execute_bearer(self.token,p)
    def test_admin_cannot_approve_own_action(self):
        token=self.app.issue(ADMIN,'support-assistant')['token']
        r=self.app.execute_bearer(token,{'tool':'tickets.update','args':{'ticket_id':'T-101','status':'resolved'}})
        with self.assertRaises(Problem):self.app.approve(ADMIN,r['approval_id'])
    def test_internal_export_is_local_and_approved(self):
        token=self.app.issue(ALICE,'report-exporter')['token']
        p={'tool':'reports.export','args':{'destination':'internal://reports'}}
        r=self.app.execute_bearer(token,p);self.assertEqual(r['decision'],'approval_required')
        self.app.approve(ADMIN,r['approval_id']);p['approval_id']=r['approval_id']
        result=self.app.execute_bearer(token,p)
        self.assertEqual(result['decision'],'allow')
        self.assertEqual(len(result['data']['records']),2)
        self.assertTrue(all('requester_email' not in t for t in result['data']['records']))
    def test_embedded_evaluation_passes(self):
        r=self.app.route('POST','/api/test',{},ADMIN)
        self.assertEqual(r['passed'],r['total']);self.assertEqual(r['total'],12)

class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
            cls.tmp=tempfile.TemporaryDirectory();cls.processes=[]
            for directory,port in [('agent-gateway', 18766)]:
                p=subprocess.Popen([sys.executable,str(ROOT/'app.py'),'--port',str(port),'--db',str(Path(cls.tmp.name)/(directory+'.sqlite'))],stdout=subprocess.DEVNULL)
                cls.processes.append(p)
            for port in (18766,):
                for _ in range(100):
                    try:urllib.request.urlopen(f'http://127.0.0.1:{port}/',timeout=.3);break
                    except (OSError,urllib.error.URLError):time.sleep(.05)
                else:raise RuntimeError('HTTP test server did not start')
    @classmethod
    def tearDownClass(cls):
            for p in cls.processes:p.terminate();p.wait()
            cls.tmp.cleanup()
    def req(self,path,data=None,headers=None,port=18766):
            h={'Content-Type':'application/json',**(headers or {})}
            req=urllib.request.Request(f'http://127.0.0.1:{port}'+path,json.dumps(data).encode() if data is not None else None,headers=h)
            try:
                with urllib.request.urlopen(req) as r:return r.status,json.loads(r.read()),r.headers
            except urllib.error.HTTPError as r:return r.code,json.loads(r.read()),r.headers
    def login(self,name='alice',port=18766):
            status,r,h=self.req('/api/login',{'name':name,'password':'DemoPass!2026'},port=port)
            self.assertEqual(status,200)
            return {'Cookie':h['Set-Cookie'].split(';')[0],'X-CSRF-Token':r['csrf']}
    def test_unauthenticated_api_denied(self):self.assertEqual(self.req('/api/state')[0],401)
    def test_csrf_required(self):
            h=self.login();h.pop('X-CSRF-Token')
            self.assertEqual(self.req('/api/access',{'resource':'sales-dashboard'},h)[0],403)
    def test_cross_origin_login_rejected(self):
            self.assertEqual(self.req('/api/login',{'name':'alice','password':'DemoPass!2026'},{'Origin':'https://untrusted.example'})[0],403)
    def test_wrong_host_rejected(self):self.assertEqual(self.req('/api/state',headers={'Host':'untrusted.example'})[0],403)
    def test_login_rate_limit_persists(self):
            for _ in range(8):self.assertEqual(self.req('/api/login',{'name':'rate-test','password':'wrong'})[0],401)
            self.assertEqual(self.req('/api/login',{'name':'rate-test','password':'wrong'})[0],429)
    def test_session_invalidation_on_logout(self):
            h=self.login();self.assertEqual(self.req('/api/logout',{},h)[0],200)
            self.assertEqual(self.req('/api/state',headers=h)[0],401)
    def test_bearer_execution(self):
            h=self.login(port=18766)
            _,issued,_=self.req('/api/issue',{'agent_id':'support-assistant'},h,18766)
            s,r,_=self.req('/api/execute',{'tool':'tickets.read','args':{'ticket_id':'T-101'}},
                           {'Authorization':'Bearer '+issued['token']},18766)
            self.assertEqual(s,200);self.assertEqual(r['decision'],'allow')
    def test_api_security_headers(self):
            _,_,h=self.req('/api/state')
            self.assertEqual(h['X-Content-Type-Options'],'nosniff')
            self.assertIn("frame-ancestors 'none'",h['Content-Security-Policy'])

if __name__=='__main__':unittest.main(verbosity=2)
