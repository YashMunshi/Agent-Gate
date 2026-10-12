"""Build the clearly labeled public browser simulation; preserve the local backend."""
import json
import os
import re
import shutil
from pathlib import Path
from app import AGENTS, TOOLS, TICKETS
root=Path(__file__).resolve().parent
output=root/'public'
output.mkdir(exist_ok=True)
for name in ('style.css','favicon.svg','404.html','og.png'):
    shutil.copyfile(root/'web'/name,output/name)
shutil.copytree(root/'web'/'fonts',output/'fonts',dirs_exist_ok=True)
shutil.copyfile(root/'hosted'/'demo.js',output/'demo.js')
(output/'fixture.js').write_text('window.GateFixture='+json.dumps({'agents':AGENTS,'tools':TOOLS,'tickets':TICKETS})+';\n')
html=(root/'web'/'index.html').read_text().replace('<script src="app.js" defer></script>', '<script src="fixture.js" defer></script>\n  <script src="demo.js" defer></script>\n  <script src="app.js" defer></script>')
host=os.environ.get('VERCEL_PROJECT_PRODUCTION_URL') or os.environ.get('VERCEL_URL')
if host and re.fullmatch(r'[A-Za-z0-9.-]+',host):
    html=html.replace('content="/og.png"',f'content="https://{host}/og.png"')
(output/'index.html').write_text(html)
source=(root/'web'/'app.js').read_text()
start=source.index('async function api(')
end=source.index('\nasync function refresh(',start)
source=source[:start]+"async function api(path,data){return window.agentGateDemo.request(path,data);}"+source[end:]
source=source.replace('LOCAL / SYNTHETIC','PUBLIC / BROWSER DEMO')
source=source.replace('AGENT GATE / LOCAL ENFORCEMENT LAB','PUBLIC SIMULATION / BROWSER-LOCAL STATE')
source=source.replace('Scripted agent requests.<br>Synthetic records. Real access checks.','Interactive browser simulation.<br>Synthetic records. No server access control.')
source=source.replace('NORTHSTAR / LOCAL LAB','NORTHSTAR / PUBLIC DEMO')
source=source.replace('All records are synthetic. No model API key required.','Public simulation. Settings stay in this browser.<br>The Python backend is available on GitHub.')
source=source.replace('Opaque bearer secrets are shown only when issued, held in page memory, and stored as SHA-256 digests on the server.','Demo credentials and records stay in this browser. The Python backend implements server-side credential digest storage.')
source=source.replace('Execute real enforcement code against an isolated synthetic database.','Run deterministic browser scenarios on a fresh, isolated demo state.')
source=source.replace('These tests measure explicit access controls, not an LLM’s resistance to arbitrary prompt injection. Test data does not alter the workspace’s tickets or credentials.','These scenarios demonstrate access controls in this public browser simulation. They do not measure server security or live LLM safety, and do not change your workspace records.')
source=source.replace('This gateway checks tool actions independently of the model. Requests here are scripted; arbitrary prompt injections are not classified.','This browser demo illustrates tool checks using scripted requests. Run the Python backend for server enforcement. Arbitrary prompt injections are not classified.')
source=source.replace('A prompt cannot grant extra permissions.', 'SCOPED TOOL REQUESTS.')
source=source.replace('LOCAL MOCK TOOLS','SYNTHETIC TOOLS')
source=source.replace('<button id="logout">Sign out</button>','<div class="actions"><button id="demo-reset">Reset demo</button><button id="logout">Sign out</button></div>')
source=source.replace('function bind(){','function bind(){root.querySelector("#demo-reset")?.addEventListener("click",run(async()=>{await api("reset",{});state=null;result=null;issued=null;csrf="";view="gateway";login();toast("Demo reset. Choose an account to start again.");}));')
(output/'app.js').write_text(source)
print('Built public browser demo in public/. Local Python backend retained.')
